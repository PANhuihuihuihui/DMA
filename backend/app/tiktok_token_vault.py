"""Encrypted, durable TikTok credential storage. Never returns credential material in inspection payloads."""

import json

from backend.app import store, token_boundary, token_crypto


def _require_encryption():
    if not token_crypto.encryption_available():
        raise store.StoreError(503, "TikTok credential encryption is unavailable.")


def put_token_bundle(account_id, bundle, *, conn, merchant_id=None, connected_channel_id=None, expires_at=None, refresh_expires_at=None, issued_at=None):
    if conn is None:
        raise store.StoreError(500, "Database connection required for TikTok credentials.")
    _require_encryption()
    if not isinstance(bundle, dict) or not bundle.get("access_token") or not bundle.get("refresh_token"):
        raise store.StoreError(502, "TikTok returned incomplete credentials.")
    account_id = str(account_id)
    merchant_id = merchant_id or store.DEMO_MERCHANT_ID
    connected_channel_id = connected_channel_id or store.TIKTOK_CHANNEL_ID
    try:
        ciphertext = token_crypto.encrypt_secret(json.dumps({
            "access_token": bundle["access_token"],
            "refresh_token": bundle["refresh_token"],
        }, separators=(",", ":")))
    except token_crypto.TokenEncryptionError as exc:
        raise store.StoreError(503, "TikTok credential encryption is unavailable.") from exc
    boundary = token_boundary.create_token_boundary(
        "tiktok", connected_channel_id,
        f"localpilot/provider/tiktok/{connected_channel_id}/{account_id}",
    )
    store.upsert_tiktok_account_token(
        conn, merchant_id, connected_channel_id, account_id, ciphertext,
        boundary["credentialFingerprint"], expires_at, refresh_expires_at, issued_at,
    )
    conn.commit()


def get_token_bundle(account_id, *, conn, merchant_id=None):
    if conn is None:
        raise store.StoreError(500, "Database connection required for TikTok credentials.")
    _require_encryption()
    row = store.get_tiktok_account_token_row(conn, account_id, merchant_id or store.DEMO_MERCHANT_ID)
    if row is None:
        return None
    try:
        bundle = json.loads(token_crypto.decrypt_secret(row["ciphertext"]))
    except (token_crypto.TokenEncryptionError, json.JSONDecodeError) as exc:
        raise store.StoreError(503, "TikTok credential encryption is unavailable.") from exc
    if not isinstance(bundle, dict) or not bundle.get("access_token") or not bundle.get("refresh_token"):
        raise store.StoreError(503, "TikTok credential store is invalid.")
    return bundle


def list_connected_accounts(*, conn, merchant_id=None):
    if conn is None:
        raise store.StoreError(500, "Database connection required for TikTok credentials.")
    rows = conn.execute(
        "select * from tiktok_account_tokens where merchant_id = ? order by account_id",
        (merchant_id or store.DEMO_MERCHANT_ID,),
    ).fetchall()
    return [{
        "accountId": row["account_id"], "status": row["status"],
        "credentialFingerprint": row["credential_fingerprint"],
        "issuedAt": row["issued_at"], "expiresAt": row["token_expires_at"],
        "refreshExpiresAt": row["refresh_expires_at"],
    } for row in rows]


def mark_reconnect_required(account_id, *, conn):
    if conn is None:
        raise store.StoreError(500, "Database connection required for TikTok credentials.")
    store.mark_tiktok_reconnect_required(conn, account_id)
    conn.commit()
