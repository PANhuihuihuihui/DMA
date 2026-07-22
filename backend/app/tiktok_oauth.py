import base64
import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request

from backend.app import store, tiktok_token_vault, token_crypto

TIKTOK_AUTHORIZE_BASE = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_API_BASE = "https://open.tiktokapis.com"
TIKTOK_REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"
REQUIRED_SCOPES = ["user.info.basic", "video.publish"]
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8787/api/v1/tiktok/oauth/callback"
DEFAULT_RETURN_URL = "http://127.0.0.1:5173/app?tiktokConnected=1"
STATE_TTL_SECONDS = 600
CONNECT_SESSION_TTL_SECONDS = 600
logger = logging.getLogger(__name__)


def oauth_config():
    return {
        "clientKey": os.environ.get("TIKTOK_CLIENT_KEY", ""),
        "clientSecret": os.environ.get("TIKTOK_CLIENT_SECRET", ""),
        "redirectUri": os.environ.get("TIKTOK_REDIRECT_URI", DEFAULT_REDIRECT_URI),
        "returnUrl": os.environ.get("TIKTOK_OAUTH_RETURN_URL", DEFAULT_RETURN_URL),
        "authorizeBase": os.environ.get("TIKTOK_AUTHORIZE_BASE", TIKTOK_AUTHORIZE_BASE),
        "tokenUrl": os.environ.get("TIKTOK_TOKEN_URL", TIKTOK_TOKEN_URL),
        "apiBase": os.environ.get("TIKTOK_API_BASE", TIKTOK_API_BASE),
    }


def _require_connection(conn):
    if conn is None:
        raise store.StoreError(500, "TikTok OAuth requires a database connection.")
    return conn


def _require_config(config):
    if not all(config.get(key) for key in ("clientKey", "clientSecret", "redirectUri")):
        raise store.StoreError(503, "TikTok OAuth configuration is unavailable.")
    if not token_crypto.encryption_available():
        raise store.StoreError(503, "TikTok credential encryption is unavailable.")


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_login_url(return_url=None, conn=None, config=None):
    conn = _require_connection(conn)
    config = {**oauth_config(), **(config or {})}
    _require_config(config)
    store.cleanup_expired_oauth_sessions(conn)
    verifier, challenge = _pkce_pair()
    try:
        verifier_ciphertext = token_crypto.encrypt_secret(verifier).decode("utf-8")
    except token_crypto.TokenEncryptionError as exc:
        raise store.StoreError(503, "TikTok credential encryption is unavailable.") from exc
    state = store.create_oauth_session(conn, "tiktok", "state", {
        "returnUrl": return_url or config["returnUrl"], "pkceVerifierCiphertext": verifier_ciphertext,
    }, STATE_TTL_SECONDS)
    conn.commit()
    query = parse.urlencode({
        "client_key": config["clientKey"], "redirect_uri": config["redirectUri"], "response_type": "code",
        "scope": ",".join(REQUIRED_SCOPES), "state": state, "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    return f"{config['authorizeBase']}?{query}"


def api_url(config, path):
    return f"{(config.get('apiBase') or TIKTOK_API_BASE).rstrip('/')}/{path.lstrip('/')}"


def expires_at(value):
    if value is None:
        return None
    try:
        seconds = int(value)
        if seconds <= 0:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise store.StoreError(502, "TikTok returned an invalid token expiry.") from exc
    return (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def request_json(method, url, data=None, transport=None, headers=None):
    if transport is not None:
        try:
            payload = transport(method=method, url=url, data=data, headers=headers or {})
        except store.StoreError as exc:
            raise store.StoreError(exc.status, "TikTok OAuth request failed.") from exc
        except Exception as exc:
            raise store.StoreError(502, "TikTok OAuth request failed.") from exc
        if not isinstance(payload, dict):
            raise store.StoreError(502, "TikTok OAuth returned malformed JSON.")
        return payload
    encoded = parse.urlencode(data or {}).encode("utf-8") if data is not None else None
    req = request.Request(url, data=encoded, method=method, headers={"Accept": "application/json", **(headers or {})})
    try:
        with request.urlopen(req, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise store.StoreError(502, "TikTok OAuth returned malformed JSON.") from exc
    except error.HTTPError as exc:
        exc.close()
        raise store.StoreError(exc.code, "TikTok OAuth request failed.") from exc
    except (error.URLError, OSError, TimeoutError) as exc:
        raise store.StoreError(502, "TikTok OAuth request failed.") from exc
    if not isinstance(payload, dict):
        raise store.StoreError(502, "TikTok OAuth returned malformed JSON.")
    return payload


def complete_callback(conn, query, config=None):
    conn = _require_connection(conn)
    store.cleanup_expired_oauth_sessions(conn)
    state = (query.get("state") or [""])[0]
    code = (query.get("code") or [""])[0]
    state_record = store.consume_oauth_session(conn, state, "state")
    if (query.get("error") or [""])[0]:
        raise store.StoreError(400, "TikTok authorization was not completed.")
    if not code:
        raise store.StoreError(400, "TikTok authorization callback did not include a code.")
    config = {**oauth_config(), **(config or {})}
    _require_config(config)
    try:
        verifier = token_crypto.decrypt_secret(state_record.get("pkceVerifierCiphertext", "").encode("utf-8"))
    except (token_crypto.TokenEncryptionError, AttributeError) as exc:
        raise store.StoreError(503, "TikTok credential encryption is unavailable.") from exc
    from backend.app.tiktok_auth_provider import TikTokAuthProvider
    provider = TikTokAuthProvider()
    payload = provider.exchange_code(conn, code, config, verifier)
    account = provider.list_selectable_accounts(payload["access_token"], config)[0]
    try:
        ciphertext = token_crypto.encrypt_secret(
            json.dumps({"access_token": payload["access_token"], "refresh_token": payload["refresh_token"]}, separators=(",", ":"))
        ).decode("utf-8")
    except token_crypto.TokenEncryptionError as exc:
        raise store.StoreError(503, "TikTok credential encryption is unavailable.") from exc
    session_id = store.create_oauth_session(conn, "tiktok", "connect", {
        "accounts": [account], "credentialCiphertext": ciphertext, "issuedAt": store.utc_now(),
        "expiresAt": expires_at(payload.get("expires_in")), "refreshExpiresAt": expires_at(payload.get("refresh_expires_in")),
    }, CONNECT_SESSION_TTL_SECONDS)
    conn.commit()
    separator = "&" if "?" in state_record["returnUrl"] else "?"
    return f"{state_record['returnUrl']}{separator}connectSession={parse.quote(session_id)}"


def _connect_session(session_id, conn, consume=False):
    fn = store.consume_oauth_session if consume else store.get_oauth_session
    return fn(_require_connection(conn), session_id, "connect")


def list_accounts_for_session(session_id, conn=None):
    return _connect_session(session_id, conn, False).get("accounts", [])


def select_account(conn, session_id, account_id):
    session = _connect_session(session_id, conn, True)
    account = next((item for item in session.get("accounts", []) if str(item.get("id")) == str(account_id)), None)
    if account is None:
        raise store.StoreError(400, "Selected TikTok account was not in the connect session.")
    try:
        bundle = json.loads(token_crypto.decrypt_secret(session.get("credentialCiphertext", "").encode("utf-8")))
    except (token_crypto.TokenEncryptionError, AttributeError, json.JSONDecodeError) as exc:
        raise store.StoreError(503, "TikTok credential encryption is unavailable.") from exc
    tiktok_token_vault.put_token_bundle(account["id"], bundle, conn=conn, expires_at=session.get("expiresAt"), refresh_expires_at=session.get("refreshExpiresAt"), issued_at=session.get("issuedAt"))
    conn.execute("update connected_channels set display_name = ?, provider_channel_id = ?, status = ?, updated_at = ? where id = ?", (account.get("displayName") or "Connected TikTok account", str(account["id"]), "connected", store.utc_now(), store.TIKTOK_CHANNEL_ID))
    conn.commit()
    logger.info("tiktok_account_token_stored account_id=%s expiry_known=%s", account["id"], bool(session.get("expiresAt")))
    return connection_status(conn=conn)


def connection_status(conn=None):
    config = oauth_config()
    return {"status": "ok", "configured": bool(config["clientKey"] and config["clientSecret"]), "scopes": REQUIRED_SCOPES, "connectedAccounts": tiktok_token_vault.list_connected_accounts(conn=conn) if conn else [], "redirectUri": config["redirectUri"]}


def reset_for_tests(conn=None):
    if conn is not None:
        conn.execute("delete from oauth_sessions where provider = ?", ("tiktok",))
        conn.execute("delete from tiktok_account_tokens")
        conn.commit()
