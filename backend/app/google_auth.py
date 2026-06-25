import os

from backend.app import store

VALID_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


def verify_google_id_token(credential, *, client_id=None, verifier=None):
    client_id = client_id or os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id and not verifier:
        raise store.StoreError(500, "GOOGLE_CLIENT_ID is not configured.")
    try:
        if verifier:
            payload = verifier(credential, client_id)
        else:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token

            payload = google_id_token.verify_oauth2_token(
                credential, google_requests.Request(), client_id,
            )
    except store.StoreError:
        raise
    except Exception as exc:
        raise store.StoreError(401, f"Invalid Google credential: {exc}") from exc

    iss = payload.get("iss", "")
    if iss not in VALID_ISSUERS:
        raise store.StoreError(401, f"Invalid token issuer: {iss}")

    return {
        "sub": payload["sub"],
        "email": payload.get("email"),
        "email_verified": payload.get("email_verified", False),
        "name": payload.get("name"),
    }


def resolve_or_create_identity(conn, claims):
    sub = claims["sub"]
    email = claims.get("email")
    email_verified = claims.get("email_verified", False)
    name = claims.get("name")

    user = store.get_user_by_google_sub(conn, sub)
    if user:
        return user

    if email and email_verified:
        user = store.get_user_by_email(conn, email)
        if user:
            conn.execute("update users set google_sub = ? where id = ?", (sub, user["id"]))
            if not user["email_verified"]:
                conn.execute("update users set email_verified = 1 where id = ?", (user["id"],))
            conn.commit()
            return conn.execute("select * from users where id = ?", (user["id"],)).fetchone()

    return store.create_merchant_and_user(
        conn,
        name=name,
        email=email or f"{sub}@google.identity",
        google_sub=sub,
        email_verified=email_verified,
    )


def dev_login_enabled():
    return bool(os.environ.get("LOCALPILOT_DEV_LOGIN")) and not os.environ.get("GOOGLE_CLIENT_ID")
