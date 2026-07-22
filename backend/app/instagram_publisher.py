import ipaddress
import json
import logging
import time
from datetime import datetime, timezone
from urllib import error, parse, request

from backend.app import auth_provider, instagram_oauth, instagram_token_vault, store
from backend.app.contracts import json_loads
from backend.app.instagram_auth_provider import InstagramAuthProvider


GRAPH_API_BASE = "https://graph.instagram.com"
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_CAPTION_LENGTH = 2200
MAX_CAROUSEL_ITEMS = 10
POLL_ATTEMPTS = 12
POLL_INTERVAL_SECONDS = 5
CTA_COPY = "Publish to Instagram"
logger = logging.getLogger(__name__)


class InstagramProviderError(Exception):
    def __init__(self, status, message, diagnostics):
        super().__init__(message)
        self.status = status
        self.message = message
        self.diagnostics = diagnostics


def queue_instagram_publish(conn, approval_id, payload=None, **kwargs):
    approval = store.get_approval(conn, approval_id)
    snapshot = json_loads(approval["snapshot_json"], {})
    if snapshot.get("platform") != "instagram":
        raise store.StoreError(409, "Only approved Instagram drafts can use live Instagram publishing.")
    channel = snapshot.get("connectedChannelRef") or {}
    stored_channel = store.assert_channel_publishable(conn, channel.get("id"))
    account_id = str(channel.get("providerChannelId") or "")
    requested_account = str((payload or {}).get("igUserId") or account_id)
    if not account_id or requested_account != account_id:
        raise store.StoreError(403, "Instagram account does not belong to the approved channel.")
    credential = store.get_instagram_account_token_row(conn, account_id, stored_channel["merchant_id"])
    if credential is None or credential["connected_channel_id"] != stored_channel["id"]:
        raise store.StoreError(409, "Connect Instagram before publishing.")
    media = validate_instagram_media(snapshot, opener=kwargs.get("opener"))
    return _run_job(conn, approval, snapshot, account_id, credential, media, fresh=True, **kwargs)


def retry_instagram_publish(conn, job_id, **kwargs):
    job = store.get_publish_job(conn, job_id)
    if job["status"] == "published":
        return {"status": "ok", "ctaCopy": CTA_COPY, "job": store.get_serialized_publish_job(conn, job_id)}
    approval = store.get_approval(conn, job["approval_id"])
    snapshot = json_loads(approval["snapshot_json"], {})
    channel = snapshot.get("connectedChannelRef") or {}
    account_id = str(channel.get("providerChannelId") or "")
    stored_channel = store.assert_channel_publishable(conn, channel.get("id"))
    credential = store.get_instagram_account_token_row(conn, account_id, stored_channel["merchant_id"])
    if credential is None or credential["connected_channel_id"] != stored_channel["id"]:
        raise store.StoreError(409, "Reconnect Instagram before retrying.")
    media = validate_instagram_media(snapshot, opener=kwargs.get("opener"))
    return _run_job(conn, approval, snapshot, account_id, credential, media, fresh=False, **kwargs)


def _run_job(conn, approval, snapshot, account_id, credential, media, fresh, **kwargs):
    job = store.create_publish_job(conn, approval)
    if job["status"] == "published":
        conn.commit()
        return {"status": "ok", "ctaCopy": CTA_COPY, "job": store.get_serialized_publish_job(conn, job["id"])}
    attempt_number = store.next_attempt_number(conn, job["id"])
    if fresh:
        store.append_publish_event(conn, job["id"], "approved", "Approved snapshot accepted for Instagram publishing.", "merchant", attempt_number)
        store.append_publish_event(conn, job["id"], "queued", "Instagram publish job queued from the approved snapshot.", "system", attempt_number)
    store.update_publish_job_status(conn, job["id"], "publishing")
    store.append_publish_event(conn, job["id"], "publishing", "Instagram container publisher started official Graph API attempt.", "instagram_publisher", attempt_number)
    try:
        result = publish_approved_snapshot(snapshot, account_id, credential, media, conn=conn, **kwargs)
        outcome = {"attemptStatus": "published", "terminalStatus": "published", "retryClassification": "none", "summary": result["summary"], "diagnostics": result["diagnostics"]}
    except InstagramProviderError as exc:
        transient = exc.status in {429, 500, 502, 503, 504}
        outcome = {"attemptStatus": "failed", "terminalStatus": "retry_needed" if transient else "failed", "retryClassification": "automatic_retry_needed" if transient else "manual_review", "summary": exc.message, "diagnostics": exc.diagnostics}
    persisted_snapshot = _persistable_snapshot(snapshot)
    # The approval snapshot is returned as part of serialized jobs. It may carry a
    # short-lived signed media URL only while this attempt is running; retain the
    # path for audit/retry context but never serialize or persist its query string.
    conn.execute(
        "update approvals set snapshot_json = ? where id = ?",
        (json.dumps(persisted_snapshot, sort_keys=True), approval["id"]),
    )
    attempt = store.create_publish_attempt(conn, job["id"], persisted_snapshot, outcome)
    if outcome["terminalStatus"] == "published":
        store.record_publish_outcome(conn, job["id"], attempt["id"], persisted_snapshot, provider="instagram", provider_result_ref=outcome["diagnostics"].get("providerResultRef"))
    error_class = outcome["diagnostics"].get("errorClass")
    if error_class == "authentication":
        instagram_token_vault.mark_reconnect_required(account_id, conn=conn)
    if outcome["attemptStatus"] == "failed" and store.should_manual_fallback(error_class):
        store.append_publish_event(conn, job["id"], "failed", outcome["summary"], "instagram_publisher", attempt_number)
        store.mark_publish_job_manual_fallback(conn, job["id"], error_class, outcome["summary"])
    else:
        store.update_publish_job_status(conn, job["id"], outcome["terminalStatus"])
        store.append_publish_event(conn, job["id"], outcome["attemptStatus"], outcome["summary"], "instagram_publisher", attempt_number)
    conn.commit()
    return {"status": "ok", "ctaCopy": CTA_COPY, "job": store.get_serialized_publish_job(conn, job["id"])}


def validate_instagram_media(snapshot, opener=None):
    refs = [ref for ref in snapshot.get("mediaRefs") or [] if ref.get("kind") == "image"]
    if not refs:
        raise store.StoreError(400, "Instagram publishing requires one JPEG image or a 2-10 image carousel.")
    if len(refs) > MAX_CAROUSEL_ITEMS:
        raise store.StoreError(400, "Instagram carousels support at most 10 images.")
    for ref in refs:
        url = ref.get("storageRef") or ref.get("url") or ""
        parsed = parse.urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or _is_private_host(parsed.hostname):
            raise store.StoreError(400, "Instagram images must use public HTTPS URLs.")
        if not parsed.path.lower().endswith((".jpg", ".jpeg")):
            raise store.StoreError(400, "Instagram supports JPEG images only.")
        try:
            head = request.Request(url, method="HEAD", headers={"Accept": "image/jpeg"})
            with (opener or request.urlopen)(head, timeout=10) as response:
                content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].lower()
                length = int(response.headers.get("Content-Length") or "0")
                if content_type and content_type != "image/jpeg":
                    raise store.StoreError(400, "Instagram supports JPEG images only.")
                if length > MAX_IMAGE_BYTES:
                    raise store.StoreError(400, "Instagram images must be 8 MB or smaller.")
        except store.StoreError:
            raise
        except Exception as exc:
            raise store.StoreError(400, "Instagram image URL must be publicly reachable.") from exc
    caption = build_instagram_caption(snapshot)
    if len(caption) > MAX_CAPTION_LENGTH:
        raise store.StoreError(400, "Instagram captions must be 2,200 characters or fewer.")
    return {"kind": "image" if len(refs) == 1 else "carousel", "urls": [ref.get("storageRef") or ref.get("url") for ref in refs], "caption": caption}


def _persistable_snapshot(snapshot):
    """Drop signed URL queries before audit data is stored or serialized."""
    safe = dict(snapshot)
    safe["mediaRefs"] = []
    for ref in snapshot.get("mediaRefs") or []:
        copied = dict(ref)
        for field in ("storageRef", "url"):
            if copied.get(field):
                parsed = parse.urlsplit(copied[field])
                copied[field] = parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
        safe["mediaRefs"].append(copied)
    return safe


def _is_private_host(host):
    host = host.lower()
    if host in {"localhost", "0.0.0.0", "::1"}:
        return True
    try:
        value = ipaddress.ip_address(host)
        return value.is_private or value.is_loopback or value.is_link_local
    except ValueError:
        return False


def build_instagram_caption(snapshot):
    return "\n\n".join(value.strip() for value in (snapshot.get("caption"), snapshot.get("body"), snapshot.get("cta")) if isinstance(value, str) and value.strip())


def publish_approved_snapshot(snapshot, account_id, credential, media, *, conn, graph_base=GRAPH_API_BASE, opener=None, sleep=time.sleep, clock=time.monotonic, poll_attempts=POLL_ATTEMPTS, poll_interval=POLL_INTERVAL_SECONDS):
    provider = InstagramAuthProvider()
    config = instagram_oauth.oauth_config()
    try:
        auth_provider.get_valid_credential(conn, account_id, credential["merchant_id"], provider="instagram")
    except store.StoreError as exc:
        if exc.status != 401:
            raise
        try:
            provider.refresh(conn, credential, config)
            credential = store.get_instagram_account_token_row(conn, account_id, credential["merchant_id"])
            auth_provider.get_valid_credential(conn, account_id, credential["merchant_id"], provider="instagram")
        except store.StoreError as refresh_exc:
            raise InstagramProviderError(403, "Reconnect Instagram before publishing.", provider_diagnostics("authentication", "credential_refresh_failed", {"providerStatus": refresh_exc.status, "igUserId": account_id})) from refresh_exc
    retried = {"value": False}
    def operation(token):
        try:
            return _publish_with_token(account_id, token, media, graph_base, opener, sleep, clock, poll_attempts, poll_interval)
        except InstagramProviderError as exc:
            if exc.diagnostics.get("errorClass") != "authentication":
                raise
            if retried["value"]:
                raise
            retried["value"] = True
            raise store.StoreError(401, "Instagram credential was rejected.") from exc
    try:
        return auth_provider.run_with_credential_refresh(conn, provider, credential, config, operation)
    except InstagramProviderError:
        raise
    except store.StoreError as exc:
        raise InstagramProviderError(403, "Reconnect Instagram before publishing.", provider_diagnostics("authentication", "credential_retry_failed", {"providerStatus": exc.status, "igUserId": account_id})) from exc


def _ensure_credential_fresh(credential):
    if credential is None:
        raise store.StoreError(401, "Instagram credential is unavailable.")
    value = credential["token_expires_at"]
    if not value:
        return
    expires = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    if (expires - datetime.now(timezone.utc)).total_seconds() <= 60:
        raise store.StoreError(401, "Instagram credential requires refresh.")


def _publish_with_token(account_id, token, media, graph_base, opener, sleep, clock, attempts, interval):
    children = []
    child_poll_attempts = []
    if media["kind"] == "carousel":
        for url in media["urls"]:
            child = graph_request("POST", f"{graph_base}/{parse.quote(account_id)}/media", token, {"image_url": url, "is_carousel_item": "true"}, opener)
            child_id = child.get("id")
            if not child_id:
                raise InstagramProviderError(502, "Instagram did not return a child container ID.", provider_diagnostics("platform_transient", "missing_container_id", {"igUserId": account_id}))
            child_detail = _poll_container(child_id, token, graph_base, opener, sleep, clock, attempts, interval)
            children.append(child_id)
            child_poll_attempts.append(child_detail.get("pollAttempts"))
        created = graph_request("POST", f"{graph_base}/{parse.quote(account_id)}/media", token, {"media_type": "CAROUSEL", "children": ",".join(children), "caption": media["caption"]}, opener)
    else:
        created = graph_request("POST", f"{graph_base}/{parse.quote(account_id)}/media", token, {"image_url": media["urls"][0], "caption": media["caption"]}, opener)
    container_id = created.get("id")
    if not container_id:
        raise InstagramProviderError(502, "Instagram did not return a media container ID.", provider_diagnostics("platform_transient", "missing_container_id", {"igUserId": account_id}))
    detail = _poll_container(container_id, token, graph_base, opener, sleep, clock, attempts, interval)
    published = graph_request("POST", f"{graph_base}/{parse.quote(account_id)}/media_publish", token, {"creation_id": container_id}, opener)
    media_id = published.get("id")
    if not media_id:
        raise InstagramProviderError(502, "Instagram did not return a published media ID.", provider_diagnostics("platform_transient", "missing_publish_id", {"containerId": container_id}))
    return {"summary": "Instagram media published through the official Graph API.", "diagnostics": provider_diagnostics("none", "published", {"igUserId": account_id, "containerId": container_id, "childContainerIds": children, "childPollAttempts": child_poll_attempts, "pollAttempts": detail.get("pollAttempts"), "mediaId": media_id, "permalinkUrl": detail.get("permalink"), "providerResultRef": media_id})}


def _poll_container(container_id, token, graph_base, opener, sleep, clock, attempts, interval):
    started = clock()
    for attempt in range(1, attempts + 1):
        detail = graph_request("GET", f"{graph_base}/{parse.quote(container_id)}?fields=status_code,permalink", token, None, opener)
        status = str(detail.get("status_code") or "").upper()
        logger.info("instagram_container_poll container_id=%s status=%s attempt=%s", container_id, status or "PENDING", attempt)
        if status == "FINISHED":
            detail["pollAttempts"] = attempt
            return detail
        if status in {"ERROR", "EXPIRED"}:
            raise InstagramProviderError(422, "Instagram media container did not finish processing.", provider_diagnostics("validation", "container_terminal_failure", {"containerId": container_id, "containerStatus": status, "pollAttempts": attempt}))
        if attempt < attempts:
            sleep(interval)
    raise InstagramProviderError(504, "Instagram media container timed out processing.", provider_diagnostics("platform_transient", "container_poll_timeout", {"containerId": container_id, "pollAttempts": attempts, "elapsedSeconds": round(clock() - started, 3)}))


def graph_request(method, url, token, body=None, opener=None):
    data = parse.urlencode(body or {}).encode("utf-8") if body is not None else None
    req = request.Request(url, data=data, method=method, headers={"Accept": "application/json", "Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with (opener or request.urlopen)(req, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError("Expected object")
            return payload
    except error.HTTPError as exc:
        info = _read_graph_error(exc)
        raise InstagramProviderError(exc.code, "Instagram rejected this publishing request.", provider_diagnostics(_classify(exc.code, info), "provider_error", info)) from exc
    except (error.URLError, TimeoutError):
        raise InstagramProviderError(503, "Instagram Graph API request failed before receiving a response.", provider_diagnostics("platform_transient", "network_error", {"transport": "network"}))
    except (ValueError, json.JSONDecodeError):
        raise InstagramProviderError(502, "Instagram returned a malformed response.", provider_diagnostics("platform_transient", "malformed_response", {}))


def _read_graph_error(exc):
    try:
        payload = json.loads(exc.read().decode("utf-8") or "{}")
    except Exception:
        payload = {}
    finally:
        exc.close()
    item = payload.get("error") or {}
    return {"code": item.get("code"), "errorSubcode": item.get("error_subcode"), "fbtraceId": item.get("fbtrace_id")}


def _classify(status, info):
    if status in {401, 403}:
        return "authentication"
    if status == 400:
        return "validation"
    if status == 429:
        return "rate_limit"
    return "platform_transient" if status >= 500 else "unknown"


def provider_diagnostics(error_class, result, extra):
    return {"provider": "instagram", "providerDisplayName": "Instagram Graph API", "platform": "instagram", "mode": "live", "result": result, "errorClass": error_class, "nextRecommendedAction": "retry_or_reconnect" if error_class != "none" else "verify_live_post", **{key: value for key, value in (extra or {}).items() if key != "message" and value is not None}}
