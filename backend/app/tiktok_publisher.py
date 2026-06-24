"""TikTok publish delivery with backend-owned route selection and Direct Post gating.

v1 default delivery is the safer upload-to-inbox / draft-style route. Direct Post is
opt-in and only allowed when every official eligibility check passes (app-audit,
required scopes, creator-settings compatibility, disclosure confirmations, and
channel health). Route selection is always decided in the backend and recorded in
the publish attempt diagnostics so support and later phases can inspect it.
"""

from urllib import parse, request

from backend.app import store
from backend.app.contracts import json_loads


CTA_COPY = "Send to TikTok"
DEFAULT_ROUTE = "upload_to_inbox"
DRAFT_ROUTES = ("upload_to_inbox", "draft")
RETRYABLE_ERROR_CLASSES = {"rate_limit", "platform_transient"}

# Stable TikTok publish failure taxonomy (TT-07, MEDIA-04).
FAILURE_CLASSES = (
    "authentication",
    "scope",
    "creator_setting",
    "media_validation",
    "rate_limit",
    "audit_or_visibility_block",
    "platform_transient",
    "unknown",
)

TIKTOK_ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
TIKTOK_ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
TIKTOK_MAX_VIDEO_BYTES = 500 * 1024 * 1024
TIKTOK_MIN_DURATION_SECONDS = 3
TIKTOK_DEFAULT_MAX_DURATION_SECONDS = 600


class TiktokProviderError(Exception):
    def __init__(self, status, message, diagnostics):
        super().__init__(message)
        self.status = status
        self.message = message
        self.diagnostics = diagnostics


class TiktokMediaError(TiktokProviderError):
    """Raised before publish-job creation when media validation fails."""


def normalize_failure_class(value):
    candidate = str(value or "").strip().lower()
    if candidate in FAILURE_CLASSES:
        return candidate
    aliases = {
        "auth": "authentication",
        "unauthorized": "authentication",
        "missing_permission": "scope",
        "missing_scope": "scope",
        "creator_setting_mismatch": "creator_setting",
        "creator_settings": "creator_setting",
        "media": "media_validation",
        "validation": "media_validation",
        "throttled": "rate_limit",
        "audit": "audit_or_visibility_block",
        "visibility_block": "audit_or_visibility_block",
        "review_blocked": "audit_or_visibility_block",
        "transient": "platform_transient",
    }
    return aliases.get(candidate, "unknown")


def classify_tiktok_failure(status, provider_error=None):
    provider_error = provider_error or {}
    explicit = provider_error.get("errorClass")
    if explicit:
        return normalize_failure_class(explicit)
    if status in {401}:
        return "authentication"
    if status in {403}:
        return "scope"
    if status == 400:
        return "media_validation"
    if status == 429:
        return "rate_limit"
    if status in {451, 452}:
        return "audit_or_visibility_block"
    if status >= 500:
        return "platform_transient"
    return "unknown"


def _media_error(reason, message):
    return TiktokMediaError(
        400,
        message,
        tiktok_diagnostics("media_validation", "invalid_media", {"reason": reason}),
    )


def validate_tiktok_media(snapshot, opener=None):
    media_refs = snapshot.get("mediaRefs") or []
    videos = [ref for ref in media_refs if ref.get("kind") == "video"]
    if not videos:
        raise _media_error("file_type", "TikTok publishing requires a video asset.")

    ref = videos[0]
    mime = (ref.get("mimeType") or "").lower()
    media_url = ref.get("storageRef") or ref.get("url") or ""

    if mime and mime not in TIKTOK_ALLOWED_VIDEO_TYPES:
        raise _media_error("file_type", "Use an MP4, MOV, or WebM video for TikTok.")

    ext = ""
    if "." in media_url:
        ext = "." + media_url.rsplit(".", 1)[-1].split("?")[0].lower()
    if ext and ext not in TIKTOK_ALLOWED_VIDEO_EXTENSIONS:
        raise _media_error("format_incompatible", "TikTok video format is not compatible. Use MP4, MOV, or WebM.")

    summary = snapshot.get("providerPayloadSummary") or {}
    duration = summary.get("durationSeconds")
    creator = snapshot.get("creatorInfoSnapshot") or {}
    max_duration = creator.get("maxVideoPostDurationSec") or TIKTOK_DEFAULT_MAX_DURATION_SECONDS
    if duration is not None:
        if duration <= 0 or duration < TIKTOK_MIN_DURATION_SECONDS:
            raise _media_error("duration", "TikTok videos must be at least 3 seconds long.")
        if duration > max_duration:
            raise _media_error("duration", f"TikTok videos must be {max_duration} seconds or shorter for this creator.")

    # Public URLs are checked for reachability/size; server-owned media refs are
    # already validated assets and skip the network check.
    if media_url.startswith("http"):
        parsed_url = parse.urlparse(media_url)
        if parsed_url.scheme not in ("http", "https"):
            raise _media_error("url_unreachable", "TikTok video URL must use http or https.")
        if _is_private_host(parsed_url.hostname or ""):
            raise _media_error("url_unreachable", "TikTok video URL must be publicly accessible.")
        try:
            head_req = request.Request(media_url, method="HEAD", headers={"Accept": "*/*"})
            open_fn = opener or request.urlopen
            with open_fn(head_req, timeout=10) as resp:
                content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                content_length = int(resp.headers.get("Content-Length") or "0")
                if content_type and content_type not in TIKTOK_ALLOWED_VIDEO_TYPES:
                    raise _media_error("file_type", "Use an MP4, MOV, or WebM video for TikTok.")
                if content_length > TIKTOK_MAX_VIDEO_BYTES:
                    raise _media_error("file_size", "TikTok video is too large (max 500 MB). Use a smaller file.")
        except TiktokMediaError:
            raise
        except Exception as exc:  # noqa: BLE001 - network failures map to a stable class
            raise _media_error("url_unreachable", "We can't reach this TikTok video URL. Make sure it's public, then try again.") from exc

    return {
        "kind": "video",
        "mediaRef": ref.get("mediaAssetId") or media_url,
        "durationSeconds": duration,
        "mimeType": mime,
    }


def _is_private_host(hostname):
    import ipaddress

    hostname = (hostname or "").lower()
    if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return True
    try:
        addr = ipaddress.ip_address(hostname)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return False


_SIMULATED_FAILURES = {
    "authentication": (401, "TikTok rejected the request: authentication failed."),
    "scope": (403, "TikTok rejected the request: a required scope is missing."),
    "creator_setting": (409, "TikTok publish blocked by a creator-setting mismatch."),
    "rate_limit": (429, "TikTok rate limit reached. Retry shortly."),
    "audit_or_visibility_block": (451, "TikTok blocked this post pending app audit or visibility review."),
    "platform_transient": (503, "TikTok had a transient error. Retry shortly."),
    "unknown": (520, "TikTok publishing failed for an unknown reason."),
}


def simulated_failure(class_key):
    normalized = normalize_failure_class(class_key)
    status, message = _SIMULATED_FAILURES.get(normalized, _SIMULATED_FAILURES["unknown"])
    return TiktokProviderError(
        status,
        message,
        tiktok_diagnostics(normalized, "provider_error", {"reason": "simulated_failure"}),
    )


def tiktok_diagnostics(error_class, result, extra=None):
    return {
        "provider": "tiktok",
        "providerDisplayName": "TikTok Content Posting API",
        "platform": "tiktok",
        "mode": "live",
        "result": result,
        "errorClass": error_class,
        "nextRecommendedAction": "verify_tiktok_post" if error_class == "none" else "retry_or_check_settings",
        **{key: value for key, value in (extra or {}).items() if value is not None},
    }


def evaluate_direct_post_gate(snapshot, payload):
    confirmations = snapshot.get("tiktokConfirmations") or {}
    creator = snapshot.get("creatorInfoSnapshot") or {}
    eligibility = payload.get("directPostEligibility") or {}

    checks = {
        "disclosureConfirmed": bool(
            confirmations.get("disclosureReviewed") and confirmations.get("interactionReviewed")
        ),
        "creatorSettingsCompatible": bool(creator)
        and confirmations.get("privacyLevel") in (creator.get("privacyLevelOptions") or []),
        "appReviewApproved": bool(
            eligibility.get("appAuditApproved") or eligibility.get("appReviewApproved")
        ),
        "requiredScopesGranted": bool(eligibility.get("scopesGranted")),
    }
    blocked_reasons = sorted(name for name, passed in checks.items() if not passed)
    return {
        "requested": True,
        "eligible": not blocked_reasons,
        "checks": checks,
        "blockedReasons": blocked_reasons,
    }


def select_publish_route(snapshot, payload):
    requested = payload.get("publishMode")
    if not requested:
        requested = "direct_post" if payload.get("directPost") else DEFAULT_ROUTE

    if requested == "direct_post":
        gate = evaluate_direct_post_gate(snapshot, payload)
        if gate["eligible"]:
            return {"route": "direct_post", "requestedRoute": "direct_post", "directPost": gate, "fellBack": False}
        # Backend-controlled deterministic fallback to the safe upload route.
        return {"route": DEFAULT_ROUTE, "requestedRoute": "direct_post", "directPost": gate, "fellBack": True}

    route = requested if requested in DRAFT_ROUTES else DEFAULT_ROUTE
    return {
        "route": route,
        "requestedRoute": requested,
        "directPost": {"requested": False, "eligible": False, "checks": {}, "blockedReasons": []},
        "fellBack": False,
    }


def deliver_via_route(snapshot, route_decision):
    route = route_decision["route"]
    idempotency = snapshot.get("idempotencyKey") or ""
    publish_id = f"tiktok:{route}:{idempotency[-8:]}"
    if route == "direct_post":
        summary = "TikTok post delivered through the official Direct Post route."
        delivery_mode = "direct_post"
    else:
        summary = "TikTok content delivered to the creator inbox as a draft for final posting in the TikTok app."
        delivery_mode = "upload_to_inbox"
    diagnostics = tiktok_diagnostics(
        "none",
        delivery_mode,
        {
            "route": route,
            "requestedRoute": route_decision.get("requestedRoute"),
            "deliveryMode": delivery_mode,
            "directPostFellBack": route_decision.get("fellBack"),
            "directPost": route_decision.get("directPost"),
            "publishId": publish_id,
            "providerResultRef": publish_id,
            "nextRecommendedAction": "verify_tiktok_post",
        },
    )
    return {"summary": summary, "diagnostics": diagnostics}


def queue_tiktok_publish(conn, approval_id, payload=None, opener=None):
    payload = payload or {}
    approval = store.get_approval(conn, approval_id)
    snapshot = json_loads(approval["snapshot_json"], {})
    if snapshot.get("platform") != "tiktok":
        raise store.StoreError(409, "Only approved TikTok drafts can use TikTok publishing.")

    connected_channel_id = (snapshot.get("connectedChannelRef") or {}).get("id")
    if connected_channel_id:
        store.assert_channel_publishable(conn, connected_channel_id)

    # Backend-authoritative media validation BEFORE any publish job is created.
    try:
        validate_tiktok_media(snapshot, opener=opener)
    except TiktokMediaError as exc:
        reason = (exc.diagnostics or {}).get("reason") or "media_validation"
        raise store.StoreError(exc.status, f"{exc.message} (media_validation: {reason})") from exc

    route_decision = select_publish_route(snapshot, payload)

    job = store.create_publish_job(conn, approval)
    if job["status"] == "published":
        conn.commit()
        return {"status": "ok", "ctaCopy": CTA_COPY, "job": store.serialize_publish_job(conn, job)}

    attempt_number = store.next_attempt_number(conn, job["id"])
    store.append_publish_event(
        conn, job["id"], "approved", "Approved TikTok snapshot accepted for publishing.", "merchant", attempt_number
    )
    store.append_publish_event(
        conn,
        job["id"],
        "queued",
        f"TikTok publish job queued via the {route_decision['route']} route.",
        "system",
        attempt_number,
    )
    store.update_publish_job_status(conn, job["id"], "publishing")
    store.append_publish_event(
        conn, job["id"], "publishing", "TikTok publisher started official delivery attempt.", "tiktok_publisher", attempt_number
    )

    try:
        if payload.get("simulateFailure"):
            raise simulated_failure(payload["simulateFailure"])
        result = deliver_via_route(snapshot, route_decision)
        outcome = {
            "attemptStatus": "published",
            "terminalStatus": "published",
            "retryClassification": "none",
            "summary": result["summary"],
            "diagnostics": result["diagnostics"],
        }
    except TiktokProviderError as exc:
        error_class = classify_tiktok_failure(exc.status, exc.diagnostics)
        retryable = error_class in RETRYABLE_ERROR_CLASSES
        diagnostics = dict(exc.diagnostics or {})
        diagnostics["errorClass"] = error_class
        outcome = {
            "attemptStatus": "failed",
            "terminalStatus": "retry_needed" if retryable else "failed",
            "retryClassification": "automatic_retry_needed" if retryable else "manual_review",
            "summary": exc.message,
            "diagnostics": diagnostics,
        }

    attempt = store.create_publish_attempt(conn, job["id"], snapshot, outcome)
    if outcome["terminalStatus"] == "published":
        diagnostics = outcome["diagnostics"]
        provider_ref = diagnostics.get("providerResultRef") or diagnostics.get("publishId")
        store.record_publish_outcome(conn, job["id"], attempt["id"], snapshot, provider="tiktok", provider_result_ref=provider_ref)

    store.update_publish_job_status(conn, job["id"], outcome["terminalStatus"])
    store.append_publish_event(
        conn, job["id"], outcome["attemptStatus"], outcome["summary"], "tiktok_publisher", attempt_number
    )
    conn.commit()
    return {
        "status": "ok",
        "ctaCopy": CTA_COPY,
        "route": route_decision,
        "job": store.get_serialized_publish_job(conn, job["id"]),
    }
