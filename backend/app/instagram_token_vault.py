from backend.app import store, token_boundary, token_crypto


def _require_encryption():
    if not token_crypto.encryption_available():
        raise store.StoreError(503, "Instagram credential encryption is unavailable.")


def put_account_token(account_id, token, *, conn, merchant_id=None, connected_channel_id=None, expires_at=None, issued_at=None):
    if conn is None:
        raise store.StoreError(500, "Database connection required for Instagram credentials.")
    _require_encryption()
    merchant_id = merchant_id or store.DEMO_MERCHANT_ID
    connected_channel_id = connected_channel_id or store.INSTAGRAM_CHANNEL_ID
    account_id = str(account_id)
    try:
        ciphertext = token_crypto.encrypt_secret(token)
    except token_crypto.TokenEncryptionError as exc:
        raise store.StoreError(503, "Instagram credential encryption is unavailable.") from exc
    boundary = token_boundary.create_token_boundary(
        "instagram", connected_channel_id,
        f"localpilot/provider/instagram/{connected_channel_id}/{account_id}",
    )
    store.upsert_instagram_account_token(
        conn, merchant_id, connected_channel_id, account_id, ciphertext,
        boundary["credentialFingerprint"], expires_at, issued_at,
    )
    conn.commit()


def get_account_token(account_id, *, conn, merchant_id=None):
    if conn is None:
        raise store.StoreError(500, "Database connection required for Instagram credentials.")
    _require_encryption()
    row = store.get_instagram_account_token_row(conn, account_id, merchant_id or store.DEMO_MERCHANT_ID)
    if row is None:
        return None
    try:
        return token_crypto.decrypt_secret(row["ciphertext"])
    except token_crypto.TokenEncryptionError as exc:
        raise store.StoreError(503, "Instagram credential encryption is unavailable.") from exc


def list_connected_accounts(*, conn, merchant_id=None):
    if conn is None:
        raise store.StoreError(500, "Database connection required for Instagram credentials.")
    rows = conn.execute(
        "select * from instagram_account_tokens where merchant_id = ? order by account_id",
        (merchant_id or store.DEMO_MERCHANT_ID,),
    ).fetchall()
    return [{
        "accountId": row["account_id"], "status": row["status"],
        "credentialFingerprint": row["credential_fingerprint"],
        "issuedAt": row["issued_at"], "expiresAt": row["token_expires_at"],
    } for row in rows]


def mark_reconnect_required(account_id, *, conn):
    if conn is None:
        raise store.StoreError(500, "Database connection required for Instagram credentials.")
    store.mark_instagram_reconnect_required(conn, account_id)
    conn.commit()
