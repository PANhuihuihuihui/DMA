from datetime import datetime, timedelta, timezone

from backend.app.contracts import new_id, utc_now


def _parse_timestamp(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class SessionError(Exception):
    pass


def create_session(conn, user_id, merchant_id, *, ttl_seconds=86400, user_agent=None, ip_hash=None):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    token = new_id("session")
    created_at = now.isoformat().replace("+00:00", "Z")
    expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z")
    conn.execute(
        """
        insert into sessions (
          id, user_id, merchant_id, status, created_at, last_seen_at, expires_at, user_agent, ip_hash
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            token,
            user_id,
            merchant_id,
            "authenticated",
            created_at,
            created_at,
            expires_at,
            user_agent,
            ip_hash,
        ),
    )
    conn.commit()
    return token


def resolve_session(conn, token):
    row = conn.execute("select * from sessions where id = ?", (token,)).fetchone()
    if row is None:
        raise SessionError("Session not found.")
    if row["status"] != "authenticated":
        raise SessionError("Session is not active.")

    expires_at = _parse_timestamp(row["expires_at"])
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        conn.execute(
            "update sessions set status = ?, last_seen_at = ? where id = ?",
            ("expired", utc_now(), token),
        )
        conn.commit()
        raise SessionError("Session expired.")

    last_seen_at = utc_now()
    conn.execute("update sessions set last_seen_at = ? where id = ?", (last_seen_at, token))
    conn.commit()
    return {
        "user_id": row["user_id"],
        "merchant_id": row["merchant_id"],
    }


def expire_session(conn, token):
    conn.execute("update sessions set status = ? where id = ?", ("logged_out", token))
    conn.commit()
