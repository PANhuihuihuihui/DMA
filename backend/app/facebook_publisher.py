import json
import logging
import time
from urllib import error, parse, request

from backend.app import auth_provider, facebook_token_vault, store
from backend.app.contracts import json_loads
from backend.app.facebook_auth_provider import FacebookAuthProvider


GRAPH_API_BASE = "https://graph.facebook.com/v25.0"

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
CTA_COPY = "Publish to Facebook"

logger = logging.getLogger(__name__)


class FacebookProviderError(Exception):
    def __init__(self, status, message, diagnostics):
        super().__init__(message)
        self.status = status
        self.message = message
        self.diagnostics = diagnostics


def queue_facebook_publish(conn, approval_id, payload, graph_base=GRAPH_API_BASE, opener=None):
    from backend.app import facebook_oauth

    approval = store.get_approval(conn, approval_id)
    snapshot = json_loads(approval["snapshot_json"], {})
    if snapshot.get("platform") != "facebook":
        raise store.StoreError(409, "Only approved Facebook drafts can use live Facebook publishing.")

    connected_channel_id = (snapshot.get("connectedChannelRef") or {}).get("id")
    if connected_channel_id:
        store.assert_channel_publishable(conn, connected_channel_id)

    page_id = payload.get("pageId") or (snapshot.get("connectedChannelRef") or {}).get("providerChannelId")
    if not page_id or not str(page_id).isdigit():
        raise store.StoreError(400, "Facebook publishing requires a numeric Page ID.")

    if not payload.get("userAccessToken"):
        health = facebook_oauth.active_page_health(conn)
        if not health["canPublish"]:
            raise store.StoreError(409, "This Page can't publish yet \u2014 reconnect or grant the publishing permission first.")

    media_info = validate_facebook_media(snapshot, opener=opener)

    job = store.create_publish_job(conn, approval)
    if job["status"] == "published":
        conn.commit()
        return {"status": "ok", "ctaCopy": CTA_COPY, "job": store.serialize_publish_job(conn, job)}

    attempt_number = store.next_attempt_number(conn, job["id"])
    store.append_publish_event(
        conn,
        job["id"],
        "approved",
        "Approved snapshot accepted for Facebook Page publishing.",
        "merchant",
        attempt_number,
    )
    store.append_publish_event(
        conn,
        job["id"],
        "queued",
        "Facebook Page publish job queued from the approved snapshot.",
        "system",
        attempt_number,
    )
    store.update_publish_job_status(conn, job["id"], "publishing")
    store.append_publish_event(
        conn,
        job["id"],
        "publishing",
        "Facebook publisher started official Graph API attempt.",
        "facebook_publisher",
        attempt_number,
    )

    try:
        result = publish_approved_snapshot(
            snapshot,
            user_token=payload.get("userAccessToken"),
            page_id=str(page_id),
            publish_mode=payload.get("publishMode") or "publish_now",
            scheduled_publish_time=payload.get("scheduledPublishTime"),
            graph_base=graph_base,
            conn=conn,
            opener=opener,
            media_info=media_info,
        )
        outcome = {
            "attemptStatus": "published",
            "terminalStatus": "published",
            "retryClassification": "none",
            "summary": result["summary"],
            "diagnostics": result["diagnostics"],
        }
    except FacebookProviderError as exc:
        outcome = {
            "attemptStatus": "failed",
            "terminalStatus": "retry_needed" if exc.status in {429, 500, 502, 503, 504} else "failed",
            "retryClassification": "automatic_retry_needed" if exc.status in {429, 500, 502, 503, 504} else "manual_review",
            "summary": exc.message,
            "diagnostics": exc.diagnostics,
        }

    attempt = store.create_publish_attempt(conn, job["id"], snapshot, outcome)
    if outcome["terminalStatus"] == "published":
        diagnostics = outcome["diagnostics"]
        provider_ref = diagnostics.get("providerResultRef") or diagnostics.get("postId")
        store.record_publish_outcome(conn, job["id"], attempt["id"], snapshot, provider="facebook", provider_result_ref=provider_ref)

    error_class = (outcome.get("diagnostics") or {}).get("errorClass")
    manual_fallback = outcome["attemptStatus"] == "failed" and store.should_manual_fallback(error_class)
    if manual_fallback:
        outcome["terminalStatus"] = "manual_fallback_required"
    if error_class == "authentication":
        facebook_token_vault.mark_reconnect_required(str(page_id), conn=conn)

    if manual_fallback:
        store.append_publish_event(
            conn,
            job["id"],
            outcome["attemptStatus"],
            outcome["summary"],
            "facebook_publisher",
            attempt_number,
        )
        store.mark_publish_job_manual_fallback(conn, job["id"], error_class, outcome["summary"])
    else:
        store.update_publish_job_status(conn, job["id"], outcome["terminalStatus"])
        store.append_publish_event(
            conn,
            job["id"],
            outcome["attemptStatus"],
            outcome["summary"],
            "facebook_publisher",
            attempt_number,
        )
    conn.commit()
    return {"status": "ok", "ctaCopy": CTA_COPY, "job": store.get_serialized_publish_job(conn, job["id"])}


def recommended_action_for(error_class):
    if error_class in ("authentication", "missing_permission", "page_capability"):
        return "reconnect"
    if error_class in ("rate_limit", "platform_transient"):
        return "retry"
    if error_class == "validation":
        return "fix_media_or_copy"
    return "manual_fallback"


def retry_facebook_publish(conn, job_id, graph_base=GRAPH_API_BASE, opener=None):
    from backend.app import facebook_oauth

    job_row = conn.execute("select * from publish_jobs where id = ?", (job_id,)).fetchone()
    if not job_row:
        raise store.StoreError(404, "Publish job not found.")
    if job_row["status"] == "published":
        return {"status": "ok", "ctaCopy": CTA_COPY, "job": store.get_serialized_publish_job(conn, job_id)}

    approval = store.get_approval(conn, job_row["approval_id"])
    snapshot = json_loads(approval["snapshot_json"], {})
    page_id = (snapshot.get("connectedChannelRef") or {}).get("providerChannelId")

    health = facebook_oauth.active_page_health(conn)
    if not health["canPublish"]:
        raise store.StoreError(409, "This Page can't publish yet \u2014 reconnect or grant the publishing permission first.")

    media_info = validate_facebook_media(snapshot, opener=opener)
    attempt_number = store.next_attempt_number(conn, job_id)
    store.update_publish_job_status(conn, job_id, "publishing")
    store.append_publish_event(conn, job_id, "publishing", "Facebook retry attempt started.", "facebook_publisher", attempt_number)

    try:
        result = publish_approved_snapshot(
            snapshot,
            user_token=None,
            page_id=str(page_id),
            publish_mode="publish_now",
            scheduled_publish_time=None,
            graph_base=graph_base,
            conn=conn,
            opener=opener,
            media_info=media_info,
        )
        outcome = {
            "attemptStatus": "published",
            "terminalStatus": "published",
            "retryClassification": "none",
            "summary": result["summary"],
            "diagnostics": result["diagnostics"],
        }
    except FacebookProviderError as exc:
        outcome = {
            "attemptStatus": "failed",
            "terminalStatus": "retry_needed" if exc.status in {429, 500, 502, 503, 504} else "failed",
            "retryClassification": "automatic_retry_needed" if exc.status in {429, 500, 502, 503, 504} else "manual_review",
            "summary": exc.message,
            "diagnostics": exc.diagnostics,
        }

    attempt = store.create_publish_attempt(conn, job_id, snapshot, outcome)
    if outcome["terminalStatus"] == "published":
        diagnostics = outcome["diagnostics"]
        provider_ref = diagnostics.get("providerResultRef") or diagnostics.get("postId")
        store.record_publish_outcome(conn, job_id, attempt["id"], snapshot, provider="facebook", provider_result_ref=provider_ref)

    error_class = (outcome.get("diagnostics") or {}).get("errorClass")
    manual_fallback = outcome["attemptStatus"] == "failed" and store.should_manual_fallback(error_class)
    if manual_fallback:
        outcome["terminalStatus"] = "manual_fallback_required"
    if error_class == "authentication":
        facebook_token_vault.mark_reconnect_required(str(page_id), conn=conn)

    if manual_fallback:
        store.append_publish_event(conn, job_id, outcome["attemptStatus"], outcome["summary"], "facebook_publisher", attempt_number)
        store.mark_publish_job_manual_fallback(conn, job_id, error_class, outcome["summary"])
    else:
        store.update_publish_job_status(conn, job_id, outcome["terminalStatus"])
        store.append_publish_event(conn, job_id, outcome["attemptStatus"], outcome["summary"], "facebook_publisher", attempt_number)
    conn.commit()
    return {"status": "ok", "ctaCopy": CTA_COPY, "job": store.get_serialized_publish_job(conn, job_id)}


def _is_private_host(hostname):
    import ipaddress
    hostname = hostname.lower()
    if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return True
    try:
        addr = ipaddress.ip_address(hostname)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return False


def validate_facebook_media(snapshot, opener=None):
    all_refs = snapshot.get("mediaRefs") or []
    media_refs = [
        r for r in all_refs
        if r.get("kind") == "image" and (r.get("storageRef") or r.get("url") or "").startswith("http")
    ]
    link = snapshot.get("link")

    if len(media_refs) > 1:
        raise store.StoreError(400, "Facebook publishing supports one image per post. Remove extra images.")

    if media_refs:
        ref = media_refs[0]
        image_url = ref.get("storageRef") or ref.get("url") or ""
        if not image_url:
            raise store.StoreError(400, "Image media ref is missing a URL.")

        parsed_url = parse.urlparse(image_url)
        if parsed_url.scheme not in ("http", "https"):
            raise store.StoreError(400, "Image URL must use http or https.")
        if _is_private_host(parsed_url.hostname or ""):
            raise store.StoreError(400, "Image URL must be publicly accessible.")

        ext = (parsed_url.path.rsplit(".", 1)[-1] if "." in parsed_url.path else "").lower()
        if f".{ext}" not in ALLOWED_IMAGE_EXTENSIONS:
            raise store.StoreError(400, "Use a JPG, PNG, or GIF image for Facebook.")

        try:
            head_req = request.Request(image_url, method="HEAD", headers={"Accept": "*/*"})
            open_fn = opener or request.urlopen
            with open_fn(head_req, timeout=10) as resp:
                content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                content_length = int(resp.headers.get("Content-Length") or "0")
                if content_type and content_type not in ALLOWED_IMAGE_TYPES:
                    raise store.StoreError(400, "Use a JPG, PNG, or GIF image for Facebook.")
                if content_length > MAX_IMAGE_BYTES:
                    raise store.StoreError(400, "Image is too large for Facebook (max 10 MB). Use a smaller file.")
        except store.StoreError:
            raise
        except Exception:
            raise store.StoreError(400, "We can't reach this image URL. Make sure it's public, then try again.")

        return {"kind": "image", "imageUrl": image_url}

    if link:
        return {"kind": "link", "link": link}

    return {"kind": "text"}


def _publish_snapshot_with_token(snapshot, page_id, publish_mode, scheduled_publish_time, graph_base, page_token, opener=None, media_info=None):
    message = build_facebook_message(snapshot)
    media_info = media_info or {"kind": "text"}
    scheduled_at = None
    if publish_mode == "schedule":
        scheduled_at = parse_scheduled_time(scheduled_publish_time)

    if media_info["kind"] == "image":
        body = {"url": media_info["imageUrl"]}
        if message:
            body["message"] = message
        published = graph_request(
            "POST",
            f"{graph_base}/{parse.quote(page_id)}/photos",
            page_token,
            body=body,
            opener=opener,
        )
        post_id = published.get("post_id") or published.get("id")
    else:
        body = {"message": message}
        if media_info["kind"] == "link":
            body["link"] = media_info["link"]
        if scheduled_at:
            body["published"] = "false"
            body["scheduled_publish_time"] = str(scheduled_at)
        published = graph_request(
            "POST",
            f"{graph_base}/{parse.quote(page_id)}/feed",
            page_token,
            body=body,
            opener=opener,
        )
        post_id = published.get("post_id") or published.get("id")

    if not post_id:
        raise FacebookProviderError(
            502,
            "Facebook Graph API did not return a post id.",
            provider_diagnostics("platform_transient", "missing_post_id", {"pageId": page_id}),
        )

    detail = graph_request(
        "GET",
        f"{graph_base}/{parse.quote(post_id)}?fields=permalink_url,is_published,created_time",
        page_token,
        opener=opener,
    )
    permalink = detail.get("permalink_url") or f"https://www.facebook.com/{post_id}"
    mode_label = "scheduled" if scheduled_at else "published"
    return {
        "postId": post_id,
        "permalinkUrl": permalink,
        "scheduledPublishTime": scheduled_at,
        "status": "scheduled" if scheduled_at else "published",
        "summary": f"Facebook Page post {mode_label} through the official Graph API.",
        "diagnostics": provider_diagnostics(
            "none",
            mode_label,
            {
                "pageId": page_id,
                "postId": post_id,
                "permalinkUrl": permalink,
                "isPublished": detail.get("is_published"),
                "createdTime": detail.get("created_time"),
                "scheduledPublishTime": scheduled_at,
                "providerResultRef": post_id,
                "nextRecommendedAction": "verify_live_post",
            },
        ),
    }


def publish_approved_snapshot(
    snapshot,
    user_token,
    page_id,
    publish_mode,
    scheduled_publish_time,
    graph_base,
    conn=None,
    opener=None,
    media_info=None,
):
    merchant_id = snapshot.get("merchantId") or store.DEMO_MERCHANT_ID
    page_id = str(page_id)

    if user_token:
        page_token = resolve_page_access_token(user_token, page_id, graph_base, opener=opener)
        if not page_token:
            raise FacebookProviderError(
                403,
                "Connect Facebook before publishing this Page.",
                provider_diagnostics("authentication", "not_connected", {"pageId": page_id}),
            )
        return _publish_snapshot_with_token(
            snapshot,
            page_id,
            publish_mode,
            scheduled_publish_time,
            graph_base,
            page_token,
            opener=opener,
            media_info=media_info,
        )

    if conn is None:
        raise store.StoreError(500, "Database connection required for stored Facebook credentials.")

    from backend.app import facebook_oauth

    provider = FacebookAuthProvider()
    config = facebook_oauth.oauth_config()
    credential_row = store.get_facebook_page_token_row(conn, page_id, merchant_id)
    if credential_row is None:
        raise FacebookProviderError(
            403,
            "Connect Facebook before publishing this Page.",
            provider_diagnostics(
                "authentication",
                "not_connected",
                {"merchantId": merchant_id, "pageId": page_id},
            ),
        )

    try:
        auth_provider.get_valid_credential(conn, page_id, merchant_id)
    except store.StoreError as exc:
        if exc.status != 401:
            raise
        try:
            provider.refresh(conn, credential_row, config)
            credential_row = store.get_facebook_page_token_row(conn, page_id, merchant_id)
            auth_provider.get_valid_credential(conn, page_id, merchant_id)
        except store.StoreError as refresh_exc:
            facebook_token_vault.mark_reconnect_required(page_id, conn=conn)
            raise FacebookProviderError(
                403,
                "Reconnect Facebook before publishing this Page.",
                provider_diagnostics(
                    "authentication",
                    "credential_refresh_failed",
                    {
                        "merchantId": merchant_id,
                        "pageId": page_id,
                        "providerStatus": refresh_exc.status,
                    },
                ),
            ) from refresh_exc

    retry_state = {"logged": False}

    def perform_publish(page_token):
        try:
            return _publish_snapshot_with_token(
                snapshot,
                page_id,
                publish_mode,
                scheduled_publish_time,
                graph_base,
                page_token,
                opener=opener,
                media_info=media_info,
            )
        except FacebookProviderError as exc:
            if (exc.diagnostics or {}).get("errorClass") != "authentication":
                raise
            if not retry_state["logged"]:
                logger.warning(
                    "facebook_publish_auth_retry merchant_id=%s page_id=%s",
                    merchant_id,
                    page_id,
                )
                retry_state["logged"] = True
            raise store.StoreError(401, exc.message) from exc

    try:
        return auth_provider.run_with_credential_refresh(conn, provider, credential_row, config, perform_publish)
    except store.StoreError as exc:
        facebook_token_vault.mark_reconnect_required(page_id, conn=conn)
        raise FacebookProviderError(
            403,
            "Reconnect Facebook before publishing this Page.",
            provider_diagnostics(
                "authentication",
                "credential_retry_failed",
                {
                    "merchantId": merchant_id,
                    "pageId": page_id,
                    "providerStatus": exc.status,
                },
            ),
        ) from exc


def resolve_page_access_token(user_token, page_id, graph_base, opener=None):
    accounts = graph_request(
        "GET",
        f"{graph_base}/me/accounts?fields=id,name,category,link,tasks,access_token&limit=100",
        user_token,
        opener=opener,
    )
    page = next((item for item in accounts.get("data", []) if str(item.get("id")) == str(page_id)), None)
    if not page or not page.get("access_token"):
        raise FacebookProviderError(
            403,
            "Facebook Page access token was not available for this user token.",
            provider_diagnostics("missing_permission", "page_token_not_found", {"pageId": page_id}),
        )
    return page["access_token"]


def graph_request(method, url, token, body=None, opener=None):
    encoded_body = None
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    if body is not None:
        encoded_body = parse.urlencode(body).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = request.Request(url, data=encoded_body, method=method, headers=headers)
    open_request = opener or request.urlopen
    try:
        with open_request(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        provider_error = read_graph_error(exc)
        raise FacebookProviderError(
            exc.code,
            classify_error_message(provider_error),
            provider_diagnostics(classify_error_class(exc.code, provider_error), "provider_error", provider_error),
        ) from exc
    except error.URLError as exc:
        raise FacebookProviderError(
            503,
            "Facebook Graph API request failed before receiving a response.",
            provider_diagnostics("platform_transient", "network_error", {"transport": "network"}),
        ) from exc


def read_graph_error(exc):
    try:
        payload = json.loads(exc.read().decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}
    finally:
        exc.close()
    error_payload = payload.get("error") or {}
    return {
        "status": exc.code,
        "type": error_payload.get("type"),
        "code": error_payload.get("code"),
        "errorSubcode": error_payload.get("error_subcode"),
        "message": error_payload.get("message") or "Facebook Graph API request failed.",
        "fbtraceId": error_payload.get("fbtrace_id"),
    }


def classify_error_class(status, provider_error):
    message = (provider_error.get("message") or "").lower()
    if status in {401, 403}:
        if "permission" in message or "pages_manage_posts" in message:
            return "missing_permission"
        return "authentication"
    if status == 400:
        return "validation"
    if status == 429:
        return "rate_limit"
    if status >= 500:
        return "platform_transient"
    return "unknown"


def classify_error_message(provider_error):
    return "Facebook rejected this publishing request."


def provider_diagnostics(error_class, result, extra):
    safe_extra = {
        key: value
        for key, value in (extra or {}).items()
        if key != "message" and value is not None
    }
    return {
        "provider": "facebook",
        "providerDisplayName": "Facebook Graph API",
        "platform": "facebook",
        "mode": "live",
        "result": result,
        "errorClass": error_class,
        "nextRecommendedAction": "retry_or_check_permissions" if error_class != "none" else "verify_live_post",
        **safe_extra,
    }


def build_facebook_message(snapshot):
    parts = [
        snapshot.get("caption"),
        snapshot.get("body"),
        snapshot.get("cta"),
    ]
    return "\n\n".join(part.strip() for part in parts if isinstance(part, str) and part.strip())


def parse_scheduled_time(value):
    if not value:
        raise store.StoreError(400, "Scheduled Facebook publishing requires scheduledPublishTime.")
    try:
        scheduled_at = int(value)
    except (TypeError, ValueError) as exc:
        raise store.StoreError(400, "scheduledPublishTime must be a Unix timestamp in seconds.") from exc
    if scheduled_at < int(time.time()) + 600:
        raise store.StoreError(400, "Facebook scheduled posts must be at least 10 minutes in the future.")
    return scheduled_at
