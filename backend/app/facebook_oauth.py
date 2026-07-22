import json
import logging
import os
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request

from backend.app import facebook_token_vault, store


GRAPH_API_BASE = "https://graph.facebook.com/v25.0"
FACEBOOK_DIALOG_BASE = "https://www.facebook.com/v25.0/dialog/oauth"
REQUIRED_SCOPES = ["pages_show_list", "pages_read_engagement", "pages_manage_posts"]
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8787/api/v1/facebook/oauth/callback"
DEFAULT_RETURN_URL = "http://127.0.0.1:5173/app?facebookConnected=1"
STATE_TTL_SECONDS = 600
CONNECT_SESSION_TTL_SECONDS = 600
MISSING_EXPIRY_SECONDS = 300

logger = logging.getLogger(__name__)


def oauth_config():
    return {
        "appId": os.environ.get("FACEBOOK_APP_ID", ""),
        "appSecret": os.environ.get("FACEBOOK_APP_SECRET", ""),
        "redirectUri": os.environ.get("FACEBOOK_REDIRECT_URI", DEFAULT_REDIRECT_URI),
        "returnUrl": os.environ.get("FACEBOOK_OAUTH_RETURN_URL", DEFAULT_RETURN_URL),
        "graphBase": os.environ.get("FACEBOOK_GRAPH_API_BASE", GRAPH_API_BASE),
        "dialogBase": os.environ.get("FACEBOOK_DIALOG_BASE", FACEBOOK_DIALOG_BASE),
    }


def connection_status(conn=None):
    config = oauth_config()
    pages = facebook_token_vault.list_connected_pages(conn=conn)
    active_page = None
    for p in pages:
        if p.get("isActive"):
            active_page = p
            break
    if active_page is None and pages:
        active_page = pages[0]
    return {
        "status": "ok",
        "configured": bool(config["appId"] and config["appSecret"]),
        "scopes": REQUIRED_SCOPES,
        "connectedPages": pages,
        "activePage": active_page,
        "redirectUri": config["redirectUri"],
    }


def _require_connection(conn):
    if conn is None:
        raise store.StoreError(500, "Facebook OAuth requires a database connection.")
    return conn


def build_login_url(return_url=None, conn=None, config=None):
    conn = _require_connection(conn)
    config = config or oauth_config()
    if not config["appId"] or not config["appSecret"]:
        raise store.StoreError(503, "Facebook OAuth requires FACEBOOK_APP_ID and FACEBOOK_APP_SECRET on the backend.")

    payload = {"returnUrl": return_url or config["returnUrl"]}
    store.cleanup_expired_oauth_sessions(conn)
    state = store.create_oauth_session(conn, "facebook", "state", payload, STATE_TTL_SECONDS)
    conn.commit()

    query = parse.urlencode(
        {
            "client_id": config["appId"],
            "redirect_uri": config["redirectUri"],
            "scope": ",".join(REQUIRED_SCOPES),
            "response_type": "code",
            "state": state,
        }
    )
    return f"{config['dialogBase']}?{query}"


def complete_callback(conn, query):
    conn = _require_connection(conn)
    store.cleanup_expired_oauth_sessions(conn)
    state = query.get("state", [""])[0]
    code = query.get("code", [""])[0]
    error_message = query.get("error_description", query.get("error", [""]))[0]
    state_record = pop_valid_state(state, conn=conn)
    if error_message:
        raise store.StoreError(400, f"Facebook authorization was not completed: {error_message}")
    if not code:
        raise store.StoreError(400, "Facebook authorization callback did not include a code.")

    config = oauth_config()
    # Import lazily to keep the provider's OAuth-helper imports acyclic.
    from backend.app.facebook_auth_provider import FacebookAuthProvider

    token_payload = FacebookAuthProvider().exchange_code(conn, code, config)
    effective_user_token = token_payload.get("access_token")
    if not effective_user_token:
        raise store.StoreError(502, "Facebook did not return a user access token.")
    pages = fetch_pages(effective_user_token, config)
    if not pages:
        raise store.StoreError(403, "No manageable Facebook Pages were returned for this login.")

    issued_at = store.utc_now()
    expires_at = _expires_at_from_seconds(token_payload.get("expires_in"))
    session_payload = {
        "pages": pages,
        "issuedAt": issued_at,
        "expiresAt": expires_at,
    }
    session_id = store.create_oauth_session(conn, "facebook", "connect", session_payload, CONNECT_SESSION_TTL_SECONDS)
    conn.commit()

    return_url = state_record["returnUrl"]
    separator = "&" if "?" in return_url else "?"
    return f"{return_url}{separator}connectSession={parse.quote(session_id)}"


def list_pages_for_session(session_id, conn=None):
    conn = _require_connection(conn)
    store.cleanup_expired_oauth_sessions(conn)
    session = _load_connect_session(session_id, conn=conn, consume=False)
    return [
        {
            key: value
            for key, value in page.items()
            if key != "access_token"
        }
        for page in session["pages"]
    ]


def select_page(conn, session_id, page_id):
    conn = _require_connection(conn)
    store.cleanup_expired_oauth_sessions(conn)
    session = _load_connect_session(session_id, conn=conn, consume=True)
    page_id = str(page_id)
    page = next((p for p in session["pages"] if str(p.get("id")) == page_id), None)
    if not page:
        raise store.StoreError(400, "Selected Page was not in the connect session.")
    page_token = page.get("access_token")
    if not page_token:
        raise store.StoreError(403, "Selected Facebook Page did not include a Page access token.")

    expires_at = session.get("expiresAt")
    issued_at = session.get("issuedAt")
    facebook_token_vault.put_page_token(
        page_id,
        page_token,
        page,
        conn=conn,
        merchant_id=store.DEMO_MERCHANT_ID,
        connected_channel_id=store.FACEBOOK_CHANNEL_ID,
        expires_at=expires_at,
        issued_at=issued_at,
    )
    logger.info(
        "facebook_page_token_stored page_id=%s expiry_known=%s",
        page_id,
        bool(expires_at),
    )
    facebook_token_vault.set_active_page(page_id, conn=conn)
    update_demo_facebook_channel(conn, page)
    return connection_status(conn=conn)


def switch_active_page(conn, page_id):
    page_id = str(page_id)
    row = store.get_facebook_page_token_row(conn, page_id)
    if not row:
        raise store.StoreError(404, "Page is not connected. Connect it first via Facebook OAuth.")
    facebook_token_vault.set_active_page(page_id, conn=conn)
    return connection_status(conn=conn)


def _load_connect_session(session_id, conn=None, consume=False):
    conn = _require_connection(conn)
    if consume:
        return store.consume_oauth_session(conn, session_id, "connect")
    return store.get_oauth_session(conn, session_id, "connect")


def pop_valid_state(state, conn=None):
    conn = _require_connection(conn)
    return store.consume_oauth_session(conn, state, "state")


def graph_url(config, path, params=None):
    base_url = (config.get("graphBase") or GRAPH_API_BASE).rstrip("/")
    query = parse.urlencode(params or {})
    return f"{base_url}/{path.lstrip('/')}" + (f"?{query}" if query else "")


def exchange_code_for_user_token(code, config):
    params = {
        "client_id": config["appId"],
        "redirect_uri": config["redirectUri"],
        "client_secret": config["appSecret"],
        "code": code,
    }
    return graph_get(graph_url(config, "/oauth/access_token", params))


def exchange_for_long_lived_user_token(user_token, config):
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": config["appId"],
        "client_secret": config["appSecret"],
        "fb_exchange_token": user_token,
    }
    try:
        payload = graph_get(graph_url(config, "/oauth/access_token", params))
    except store.StoreError as exc:
        logger.warning("facebook_long_lived_exchange_fallback status=%s", exc.status)
        return {}
    if not isinstance(payload, dict) or not payload.get("access_token"):
        logger.warning("facebook_long_lived_exchange_fallback malformed_payload=true")
        return {}
    return payload


def fetch_pages(user_token, config):
    params = {
        "fields": "id,name,category,link,tasks,access_token",
        "limit": "100",
        "access_token": user_token,
    }
    payload = graph_get(graph_url(config, "/me/accounts", params))
    if not isinstance(payload, dict):
        raise store.StoreError(502, "Facebook Page list response was malformed.")
    return payload.get("data") or []


def choose_page(pages):
    preferred_page_id = os.environ.get("FACEBOOK_DEMO_PAGE_ID", "1243605852158721")
    for page in pages:
        if str(page.get("id")) == str(preferred_page_id):
            return page
    return pages[0]


def update_demo_facebook_channel(conn, page):
    now = store.utc_now()
    conn.execute(
        """
        update connected_channels
        set display_name = ?, provider_channel_id = ?, status = ?, updated_at = ?
        where id = ?
        """,
        (
            page.get("name") or "Connected Facebook Page",
            str(page.get("id")),
            "connected",
            now,
            store.FACEBOOK_CHANNEL_ID,
        ),
    )
    conn.commit()


def page_health(page_row):
    if page_row.get("status") == "reconnect_required":
        return "reconnect_required"
    if "tasks" not in page_row:
        return "connected"
    tasks = set(page_row.get("tasks") or [])
    if not tasks.intersection({"CREATE_CONTENT", "MANAGE"}):
        return "missing_permission"
    return "connected"


def active_page_health(conn=None, merchant_id=None):
    merchant_id = merchant_id or store.DEMO_MERCHANT_ID
    if conn is not None:
        row = store.get_active_facebook_page_row(conn, merchant_id)
        if row:
            health = page_health(dict(row))
            return {
                "activePageId": row["page_id"],
                "health": health,
                "canPublish": health == "connected",
            }
    pages = facebook_token_vault.list_connected_pages(conn=conn)
    if pages:
        return {"activePageId": pages[0].get("pageId"), "health": "connected", "canPublish": True}
    return {"activePageId": None, "health": "reconnect_required", "canPublish": False}


def _graph_request(url, method):
    req = request.Request(url, method=method, headers={"Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=15) as response:
            try:
                return json.loads(response.read().decode("utf-8") or "{}")
            except json.JSONDecodeError as exc:
                raise store.StoreError(502, "Facebook OAuth returned malformed JSON.") from exc
    except error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}
        finally:
            exc.close()
        message = (payload.get("error") or {}).get("message") or "Facebook OAuth request failed."
        raise store.StoreError(exc.code, message) from exc
    except (error.URLError, OSError, TimeoutError) as exc:
        raise store.StoreError(502, "Facebook OAuth request failed.") from exc


def graph_get(url):
    return _graph_request(url, "GET")


def graph_delete(url):
    return _graph_request(url, "DELETE")


def reset_for_tests(conn=None):
    if conn is not None:
        store.cleanup_expired_oauth_sessions(conn)
        conn.execute(
            "delete from oauth_sessions where provider = ? and session_type in (?, ?)",
            ("facebook", "state", "connect"),
        )
        conn.commit()
    facebook_token_vault.clear()


def _expires_at_from_seconds(expires_in):
    try:
        expires_delta = int(expires_in)
        if expires_delta <= 0:
            raise ValueError
    except (TypeError, ValueError):
        expires_delta = MISSING_EXPIRY_SECONDS
        logger.warning(
            "facebook_token_expiry_missing fallback_seconds=%s",
            MISSING_EXPIRY_SECONDS,
        )
    return (
        datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=expires_delta)
    ).isoformat().replace("+00:00", "Z")
