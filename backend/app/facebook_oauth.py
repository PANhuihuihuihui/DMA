import json
import os
import secrets
import time
from urllib import error, parse, request

from backend.app import facebook_token_vault, store


GRAPH_API_BASE = "https://graph.facebook.com/v25.0"
FACEBOOK_DIALOG_BASE = "https://www.facebook.com/v25.0/dialog/oauth"
REQUIRED_SCOPES = ["pages_show_list", "pages_read_engagement", "pages_manage_posts"]
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8787/api/v1/facebook/oauth/callback"
DEFAULT_RETURN_URL = "http://127.0.0.1:5173/app?facebookConnected=1"
STATE_TTL_SECONDS = 600
CONNECT_SESSION_TTL_SECONDS = 600

_OAUTH_STATES = {}
_CONNECT_SESSIONS = {}


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
    return {
        "status": "ok",
        "configured": bool(config["appId"] and config["appSecret"]),
        "scopes": REQUIRED_SCOPES,
        "connectedPages": pages,
        "activePage": active_page,
        "redirectUri": config["redirectUri"],
    }


def build_login_url(return_url=None):
    config = oauth_config()
    if not config["appId"] or not config["appSecret"]:
        raise store.StoreError(503, "Facebook OAuth requires FACEBOOK_APP_ID and FACEBOOK_APP_SECRET on the backend.")
    state = secrets.token_urlsafe(24)
    _OAUTH_STATES[state] = {
        "createdAt": time.time(),
        "returnUrl": return_url or config["returnUrl"],
    }
    params = {
        "client_id": config["appId"],
        "redirect_uri": config["redirectUri"],
        "state": state,
        "response_type": "code",
        "scope": ",".join(REQUIRED_SCOPES),
    }
    return f"{config['dialogBase']}?{parse.urlencode(params)}"


def complete_callback(conn, query):
    state = query.get("state", [""])[0]
    code = query.get("code", [""])[0]
    error_message = query.get("error_description", query.get("error", [""]))[0]
    state_record = pop_valid_state(state)
    if error_message:
        raise store.StoreError(400, f"Facebook authorization was not completed: {error_message}")
    if not code:
        raise store.StoreError(400, "Facebook authorization callback did not include a code.")

    config = oauth_config()
    user_token_payload = exchange_code_for_user_token(code, config)
    user_token = user_token_payload.get("access_token")
    if not user_token:
        raise store.StoreError(502, "Facebook did not return a user access token.")

    long_lived_payload = exchange_for_long_lived_user_token(user_token, config)
    effective_user_token = long_lived_payload.get("access_token") or user_token
    pages = fetch_pages(effective_user_token, config)
    if not pages:
        raise store.StoreError(403, "No manageable Facebook Pages were returned for this login.")

    session_id = secrets.token_urlsafe(24)
    _CONNECT_SESSIONS[session_id] = {
        "createdAt": time.time(),
        "pages": pages,
    }

    return_url = state_record["returnUrl"]
    separator = "&" if "?" in return_url else "?"
    return f"{return_url}{separator}connectSession={parse.quote(session_id)}"


def list_pages_for_session(session_id):
    session = _pop_or_peek_session(session_id, consume=False)
    return [
        {
            "id": str(p.get("id")),
            "name": p.get("name"),
            "category": p.get("category"),
            "link": p.get("link"),
            "tasks": p.get("tasks") or [],
        }
        for p in session["pages"]
    ]


def select_page(conn, session_id, page_id):
    session = _pop_or_peek_session(session_id, consume=True)
    page_id = str(page_id)
    page = next((p for p in session["pages"] if str(p.get("id")) == page_id), None)
    if not page:
        raise store.StoreError(400, "Selected Page was not in the connect session.")
    page_token = page.get("access_token")
    if not page_token:
        raise store.StoreError(403, "Selected Facebook Page did not include a Page access token.")

    facebook_token_vault.put_page_token(
        page_id, page_token, page, conn=conn,
        merchant_id=store.DEMO_MERCHANT_ID,
        connected_channel_id=store.FACEBOOK_CHANNEL_ID,
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


def _pop_or_peek_session(session_id, consume=False):
    if not session_id or session_id not in _CONNECT_SESSIONS:
        raise store.StoreError(400, "Connect session is invalid or expired.")
    session = _CONNECT_SESSIONS[session_id] if not consume else _CONNECT_SESSIONS.pop(session_id)
    if time.time() - session["createdAt"] > CONNECT_SESSION_TTL_SECONDS:
        _CONNECT_SESSIONS.pop(session_id, None)
        raise store.StoreError(400, "Connect session is expired.")
    return session


def pop_valid_state(state):
    if not state or state not in _OAUTH_STATES:
        raise store.StoreError(400, "Facebook authorization state is invalid or expired.")
    record = _OAUTH_STATES.pop(state)
    if time.time() - record["createdAt"] > STATE_TTL_SECONDS:
        raise store.StoreError(400, "Facebook authorization state is expired.")
    return record


def exchange_code_for_user_token(code, config):
    params = {
        "client_id": config["appId"],
        "redirect_uri": config["redirectUri"],
        "client_secret": config["appSecret"],
        "code": code,
    }
    return graph_get(f"{config['graphBase']}/oauth/access_token?{parse.urlencode(params)}")


def exchange_for_long_lived_user_token(user_token, config):
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": config["appId"],
        "client_secret": config["appSecret"],
        "fb_exchange_token": user_token,
    }
    try:
        return graph_get(f"{config['graphBase']}/oauth/access_token?{parse.urlencode(params)}")
    except store.StoreError:
        return {}


def fetch_pages(user_token, config):
    params = {
        "fields": "id,name,category,link,tasks,access_token",
        "limit": "100",
        "access_token": user_token,
    }
    payload = graph_get(f"{config['graphBase']}/me/accounts?{parse.urlencode(params)}")
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


def graph_get(url):
    req = request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}
        finally:
            exc.close()
        message = (payload.get("error") or {}).get("message") or "Facebook OAuth request failed."
        raise store.StoreError(exc.code, message) from exc


def reset_for_tests():
    _OAUTH_STATES.clear()
    _CONNECT_SESSIONS.clear()
    facebook_token_vault.clear()
