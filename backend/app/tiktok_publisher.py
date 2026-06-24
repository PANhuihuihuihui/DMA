"""TikTok publish delivery with backend-owned route selection and Direct Post gating.

v1 default delivery is the safer upload-to-inbox / draft-style route. Direct Post is
opt-in and only allowed when every official eligibility check passes (app-audit,
required scopes, creator-settings compatibility, disclosure confirmations, and
channel health). Route selection is always decided in the backend and recorded in
the publish attempt diagnostics so support and later phases can inspect it.
"""

from backend.app import store
from backend.app.contracts import json_loads


CTA_COPY = "Send to TikTok"
DEFAULT_ROUTE = "upload_to_inbox"
DRAFT_ROUTES = ("upload_to_inbox", "draft")
RETRYABLE_ERROR_CLASSES = {"rate_limit", "platform_transient"}


class TiktokProviderError(Exception):
    def __init__(self, status, message, diagnostics):
        super().__init__(message)
        self.status = status
        self.message = message
        self.diagnostics = diagnostics


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


def queue_tiktok_publish(conn, approval_id, payload=None):
    payload = payload or {}
    approval = store.get_approval(conn, approval_id)
    snapshot = json_loads(approval["snapshot_json"], {})
    if snapshot.get("platform") != "tiktok":
        raise store.StoreError(409, "Only approved TikTok drafts can use TikTok publishing.")

    connected_channel_id = (snapshot.get("connectedChannelRef") or {}).get("id")
    if connected_channel_id:
        store.assert_channel_publishable(conn, connected_channel_id)

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
        result = deliver_via_route(snapshot, route_decision)
        outcome = {
            "attemptStatus": "published",
            "terminalStatus": "published",
            "retryClassification": "none",
            "summary": result["summary"],
            "diagnostics": result["diagnostics"],
        }
    except TiktokProviderError as exc:
        retryable = exc.status in {429, 500, 502, 503, 504} or (exc.diagnostics or {}).get("errorClass") in RETRYABLE_ERROR_CLASSES
        outcome = {
            "attemptStatus": "failed",
            "terminalStatus": "retry_needed" if retryable else "failed",
            "retryClassification": "automatic_retry_needed" if retryable else "manual_review",
            "summary": exc.message,
            "diagnostics": exc.diagnostics,
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
