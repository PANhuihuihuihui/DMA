import json
import logging
import os
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request

from backend.app import instagram_token_vault, store, token_crypto

INSTAGRAM_AUTHORIZE_BASE = "https://www.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
GRAPH_API_BASE = "https://graph.instagram.com/v25.0"
REQUIRED_SCOPES = ["instagram_business_basic", "instagram_business_content_publish"]
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8787/api/v1/instagram/oauth/callback"
DEFAULT_RETURN_URL = "http://127.0.0.1:5173/app?instagramConnected=1"
STATE_TTL_SECONDS = 600
CONNECT_SESSION_TTL_SECONDS = 600

logger = logging.getLogger(__name__)


def oauth_config():
    return {
        "appId": os.environ.get("INSTAGRAM_APP_ID", ""),
        "appSecret": os.environ.get("INSTAGRAM_APP_SECRET", ""),
        "redirectUri": os.environ.get("INSTAGRAM_REDIRECT_URI", DEFAULT_REDIRECT_URI),
        "returnUrl": os.environ.get("INSTAGRAM_OAUTH_RETURN_URL", DEFAULT_RETURN_URL),
        "authorizeBase": os.environ.get("INSTAGRAM_AUTHORIZE_BASE", INSTAGRAM_AUTHORIZE_BASE),
        "tokenUrl": os.environ.get("INSTAGRAM_TOKEN_URL", INSTAGRAM_TOKEN_URL),
        "graphBase": os.environ.get("INSTAGRAM_GRAPH_API_BASE", GRAPH_API_BASE),
    }


def _require_connection(conn):
    if conn is None:
        raise store.StoreError(500, "Instagram OAuth requires a database connection.")
    return conn


def _require_config(config):
    missing = [name for name, key in (("INSTAGRAM_APP_ID", "appId"), ("INSTAGRAM_APP_SECRET", "appSecret"), ("INSTAGRAM_REDIRECT_URI", "redirectUri")) if not config.get(key)]
    if missing:
        raise store.StoreError(503, "Instagram OAuth configuration is unavailable.")


def build_login_url(return_url=None, conn=None, config=None):
    conn = _require_connection(conn)
    config = {**oauth_config(), **(config or {})}
    _require_config(config)
    store.cleanup_expired_oauth_sessions(conn)
    state = store.create_oauth_session(conn, "instagram", "state", {"returnUrl": return_url or config["returnUrl"]}, STATE_TTL_SECONDS)
    conn.commit()
    query = parse.urlencode({"client_id": config["appId"], "redirect_uri": config["redirectUri"], "response_type": "code", "scope": ",".join(REQUIRED_SCOPES), "state": state})
    return f"{config['authorizeBase']}?{query}"


def pop_valid_state(state, conn=None):
    return store.consume_oauth_session(_require_connection(conn), state, "state")


def graph_url(config, path, params=None):
    base = (config.get("graphBase") or GRAPH_API_BASE).rstrip("/")
    query = parse.urlencode(params or {})
    return f"{base}/{path.lstrip('/')}" + (f"?{query}" if query else "")


def _expires_at(expires_in):
    try:
        seconds = int(expires_in)
        if seconds <= 0:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise store.StoreError(502, "Instagram returned an invalid token expiry.") from exc
    return (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def request_json(method, url, data=None, transport=None):
    if transport is not None:
        try:
            payload = transport(method=method, url=url, data=data)
        except store.StoreError as exc:
            raise store.StoreError(exc.status, "Instagram OAuth request failed.") from exc
        except Exception as exc:
            raise store.StoreError(502, "Instagram OAuth request failed.") from exc
        if not isinstance(payload, dict):
            raise store.StoreError(502, "Instagram OAuth returned malformed JSON.")
        return payload
    encoded = parse.urlencode(data or {}).encode("utf-8") if data is not None else None
    req = request.Request(url, data=encoded, method=method, headers={"Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=15) as response:
            try:
                payload = json.loads(response.read().decode("utf-8") or "{}")
            except json.JSONDecodeError as exc:
                raise store.StoreError(502, "Instagram OAuth returned malformed JSON.") from exc
    except error.HTTPError as exc:
        exc.close()
        raise store.StoreError(exc.code, "Instagram OAuth request failed.") from exc
    except (error.URLError, OSError, TimeoutError) as exc:
        raise store.StoreError(502, "Instagram OAuth request failed.") from exc
    if not isinstance(payload, dict):
        raise store.StoreError(502, "Instagram OAuth returned malformed JSON.")
    return payload


def complete_callback(conn, query, config=None):
    conn = _require_connection(conn)
    store.cleanup_expired_oauth_sessions(conn)
    state = (query.get("state") or [""])[0]
    code = (query.get("code") or [""])[0]
    state_record = pop_valid_state(state, conn)
    if (query.get("error") or [""])[0]:
        raise store.StoreError(400, "Instagram authorization was not completed.")
    if not code:
        raise store.StoreError(400, "Instagram authorization callback did not include a code.")
    config = {**oauth_config(), **(config or {})}
    from backend.app.instagram_auth_provider import InstagramAuthProvider
    provider = InstagramAuthProvider()
    payload = provider.exchange_code(conn, code, config)
    token = payload["access_token"]
    account = provider.list_selectable_accounts(token, config)[0]
    try:
        staged_ciphertext = token_crypto.encrypt_secret(token).decode("utf-8")
    except token_crypto.TokenEncryptionError as exc:
        raise store.StoreError(503, "Instagram credential encryption is unavailable.") from exc
    session_id = store.create_oauth_session(conn, "instagram", "connect", {
        "accounts": [account],
        "credentialCiphertext": staged_ciphertext,
        "issuedAt": store.utc_now(),
        "expiresAt": _expires_at(payload.get("expires_in")),
    }, CONNECT_SESSION_TTL_SECONDS)
    conn.commit()
    separator = "&" if "?" in state_record["returnUrl"] else "?"
    return f"{state_record['returnUrl']}{separator}connectSession={parse.quote(session_id)}"


def _load_connect_session(session_id, conn=None, consume=False):
    conn = _require_connection(conn)
    return (store.consume_oauth_session if consume else store.get_oauth_session)(conn, session_id, "connect")


def list_accounts_for_session(session_id, conn=None):
    session = _load_connect_session(session_id, conn=conn)
    return session.get("accounts", [])


def select_account(conn, session_id, account_id):
    session = _load_connect_session(session_id, conn=conn, consume=True)
    account = next((item for item in session.get("accounts", []) if str(item.get("id")) == str(account_id)), None)
    if account is None:
        raise store.StoreError(400, "Selected Instagram account was not in the connect session.")
    try:
        token = token_crypto.decrypt_secret(session.get("credentialCiphertext", "").encode("utf-8"))
    except (token_crypto.TokenEncryptionError, AttributeError) as exc:
        raise store.StoreError(503, "Instagram credential encryption is unavailable.") from exc
    instagram_token_vault.put_account_token(
        account["id"], token, conn=conn, expires_at=session.get("expiresAt"), issued_at=session.get("issuedAt"),
    )
    logger.info("instagram_account_token_stored account_id=%s expiry_known=%s", account["id"], bool(session.get("expiresAt")))
    update_demo_instagram_channel(conn, account)
    return connection_status(conn=conn)


def update_demo_instagram_channel(conn, account):
    conn.execute(
        """update connected_channels
           set display_name = ?, provider_channel_id = ?, status = ?, updated_at = ?
           where id = ?""",
        (
            f"@{account.get('username')}" if account.get("username") else "Connected Instagram account",
            str(account["id"]), "connected", store.utc_now(), store.INSTAGRAM_CHANNEL_ID,
        ),
    )
    conn.commit()


def connection_status(conn=None):
    config = oauth_config()
    return {"status": "ok", "configured": bool(config["appId"] and config["appSecret"]), "scopes": REQUIRED_SCOPES, "connectedAccounts": instagram_token_vault.list_connected_accounts(conn=conn), "redirectUri": config["redirectUri"]}


def reset_for_tests(conn=None):
    if conn is not None:
        conn.execute("delete from oauth_sessions where provider = ?", ("instagram",))
        conn.execute("delete from instagram_account_tokens")
        conn.commit()
