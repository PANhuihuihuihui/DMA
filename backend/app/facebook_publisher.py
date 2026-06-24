import json
import time
from urllib import error, parse, request

from backend.app import facebook_token_vault, store
from backend.app.contracts import json_loads


GRAPH_API_BASE = "https://graph.facebook.com/v20.0"
CTA_COPY = "Publish to Facebook"


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

    page_id = payload.get("pageId") or (snapshot.get("connectedChannelRef") or {}).get("providerChannelId")
    if not page_id or not str(page_id).isdigit():
        raise store.StoreError(400, "Facebook publishing requires a numeric Page ID.")

    if not payload.get("userAccessToken"):
        health = facebook_oauth.active_page_health(conn)
        if not health["canPublish"]:
            raise store.StoreError(409, "This Page can't publish yet \u2014 reconnect or grant the publishing permission first.")

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
            opener=opener,
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
    if error_class == "authentication":
        facebook_token_vault.mark_reconnect_required(str(page_id), conn=conn)

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


def publish_approved_snapshot(snapshot, user_token, page_id, publish_mode, scheduled_publish_time, graph_base, opener=None):
    page_token = facebook_token_vault.get_page_token(page_id)
    if not page_token and user_token:
        page_token = resolve_page_access_token(user_token, page_id, graph_base, opener=opener)
    if not page_token:
        raise FacebookProviderError(
            403,
            "Connect Facebook before publishing this Page.",
            provider_diagnostics("authentication", "not_connected", {"pageId": page_id}),
        )
    message = build_facebook_message(snapshot)
    body = {"message": message}
    scheduled_at = None
    if publish_mode == "schedule":
        scheduled_at = parse_scheduled_time(scheduled_publish_time)
        body["published"] = "false"
        body["scheduled_publish_time"] = str(scheduled_at)

    published = graph_request(
        "POST",
        f"{graph_base}/{parse.quote(page_id)}/feed",
        page_token,
        body=body,
        opener=opener,
    )
    post_id = published.get("id")
    if not post_id:
        raise FacebookProviderError(
            502,
            "Facebook did not return a post ID.",
            provider_diagnostics("unknown", "missing_post_id", {"pageId": page_id}),
        )

    detail = graph_request(
        "GET",
        f"{graph_base}/{parse.quote(post_id)}?fields=id,message,created_time,permalink_url,is_published",
        page_token,
        opener=opener,
    )
    permalink = detail.get("permalink_url")
    mode_label = "scheduled" if scheduled_at else "published"
    return {
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
            provider_diagnostics("platform_transient", "network_error", {"reason": str(exc.reason)}),
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
    return provider_error.get("message") or "Facebook publishing failed."


def provider_diagnostics(error_class, result, extra):
    return {
        "provider": "facebook",
        "providerDisplayName": "Facebook Graph API",
        "platform": "facebook",
        "mode": "live",
        "result": result,
        "errorClass": error_class,
        "nextRecommendedAction": "retry_or_check_permissions" if error_class != "none" else "verify_live_post",
        **{key: value for key, value in (extra or {}).items() if value is not None},
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
