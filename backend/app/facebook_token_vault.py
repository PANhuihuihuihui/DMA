from backend.app import store, token_boundary, token_crypto
from backend.app.contracts import utc_now


_PAGE_TOKENS = {}


def put_page_token(page_id, token, page=None, conn=None, merchant_id=None, connected_channel_id=None, expires_at=None, issued_at=None):
    merchant_id = merchant_id or store.DEMO_MERCHANT_ID
    connected_channel_id = connected_channel_id or store.FACEBOOK_CHANNEL_ID
    page_id = str(page_id)
    page = page or {}

    if conn is not None and token_crypto.encryption_available():
        ciphertext = token_crypto.encrypt_secret(token)
        boundary = token_boundary.create_token_boundary(
            provider="facebook",
            connected_channel_id=connected_channel_id,
            secret_ref=f"localpilot/provider/facebook/{connected_channel_id}/{page_id}",
        )
        store.upsert_facebook_page_token(
            conn,
            merchant_id=merchant_id,
            connected_channel_id=connected_channel_id,
            page_id=page_id,
            ciphertext=ciphertext,
            credential_fingerprint=boundary["credentialFingerprint"],
            expires_at=expires_at,
            issued_at=issued_at,
            status="active",
        )
        conn.commit()
    else:
        token_crypto.emit_insecure_warning()
        _PAGE_TOKENS[page_id] = {
            "token": token,
            "page": page,
            "connectedAt": utc_now(),
        }


def get_page_token(page_id, conn=None, merchant_id=None):
    merchant_id = merchant_id or store.DEMO_MERCHANT_ID
    page_id = str(page_id)

    if conn is not None and token_crypto.encryption_available():
        row = store.get_facebook_page_token_row(conn, page_id, merchant_id)
        if row is None:
            return None
        return token_crypto.decrypt_secret(row["ciphertext"])

    record = _PAGE_TOKENS.get(page_id)
    return record["token"] if record else None


def list_connected_pages(conn=None, merchant_id=None):
    merchant_id = merchant_id or store.DEMO_MERCHANT_ID

    if conn is not None and token_crypto.encryption_available():
        rows = store.list_facebook_page_token_rows(conn, merchant_id)
        return [
            {
                "pageId": row["page_id"],
                "status": row["status"],
                "isActive": bool(row["is_active"]),
                "credentialFingerprint": row["credential_fingerprint"],
                "connectedAt": row["created_at"],
            }
            for row in rows
        ]

    return [
        {
            "pageId": page_id,
            "name": record["page"].get("name"),
            "link": record["page"].get("link"),
            "category": record["page"].get("category"),
            "tasks": record["page"].get("tasks") or [],
            "connectedAt": record["connectedAt"],
        }
        for page_id, record in sorted(_PAGE_TOKENS.items())
    ]


def set_active_page(page_id, conn=None, merchant_id=None):
    merchant_id = merchant_id or store.DEMO_MERCHANT_ID
    page_id = str(page_id)

    if conn is not None:
        store.set_active_facebook_page(conn, merchant_id, page_id)
        conn.commit()


def mark_reconnect_required(page_id, conn=None):
    page_id = str(page_id)

    if conn is not None:
        store.mark_facebook_page_reconnect_required(conn, page_id)
        conn.commit()


def clear():
    _PAGE_TOKENS.clear()
