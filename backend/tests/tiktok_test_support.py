"""Explicit encrypted OAuth credential plus deterministic Content API transport for TikTok unit tests."""
import os

from backend.app import store, tiktok_token_vault
from backend.app.tiktok_content_api import TikTokContentApi
from backend.app.token_crypto import generate_dev_key


def install_connected_tiktok(conn):
    os.environ.setdefault("LOCALPILOT_TOKEN_KEY", generate_dev_key())
    account_id = "tiktok-test-account"
    conn.execute(
        "update connected_channels set provider_channel_id = ?, status = ? where id = ?",
        (account_id, "connected", store.TIKTOK_CHANNEL_ID),
    )
    conn.commit()
    tiktok_token_vault.put_token_bundle(account_id, {"access_token": "test-access", "refresh_token": "test-refresh"}, conn=conn, expires_at="2099-01-01T00:00:00Z")


def published_api(calls=None):
    calls = calls if calls is not None else []
    def transport(**kwargs):
        calls.append(kwargs)
        if kwargs["url"].endswith("status/fetch/"):
            return {"data": {"status": "PUBLISH_COMPLETE"}, "error": {"code": "ok"}}
        return {"data": {"publish_id": "provider-publish-test"}, "error": {"code": "ok"}}
    return TikTokContentApi(transport=transport), calls
