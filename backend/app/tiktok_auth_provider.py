import logging

from backend.app import store, tiktok_oauth, tiktok_token_vault
from backend.app.auth_provider import AuthProvider

logger = logging.getLogger(__name__)


class TikTokAuthProvider(AuthProvider):
    def build_auth_url(self, config, conn=None):
        return tiktok_oauth.build_login_url(
            return_url=config.get("returnUrl"), conn=conn, config=config,
        )

    def exchange_code(self, conn, code, config, code_verifier=None):
        if not code_verifier:
            raise store.StoreError(400, "TikTok OAuth verifier is unavailable.")
        payload = tiktok_oauth.request_json(
            "POST", config.get("tokenUrl", tiktok_oauth.TIKTOK_TOKEN_URL), {
                "client_key": config.get("clientKey", ""),
                "client_secret": config.get("clientSecret", ""),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": config.get("redirectUri", ""),
                "code_verifier": code_verifier,
            }, config.get("httpTransport"),
        )
        if not payload.get("access_token") or not payload.get("refresh_token"):
            raise store.StoreError(502, "TikTok did not return complete credentials.")
        return payload

    def refresh(self, conn, credential_row, config):
        account_id = credential_row["account_id"]
        bundle = tiktok_token_vault.get_token_bundle(
            account_id, conn=conn, merchant_id=credential_row["merchant_id"],
        )
        if not bundle:
            raise store.StoreError(401, "TikTok credential is unavailable.")
        payload = tiktok_oauth.request_json(
            "POST", config.get("tokenUrl", tiktok_oauth.TIKTOK_TOKEN_URL), {
                "client_key": config.get("clientKey", ""),
                "client_secret": config.get("clientSecret", ""),
                "grant_type": "refresh_token",
                "refresh_token": bundle["refresh_token"],
            }, config.get("httpTransport"),
        )
        access_token = payload.get("access_token")
        if not access_token:
            raise store.StoreError(502, "TikTok did not return a refreshed access token.")
        replacement = {
            "access_token": access_token,
            "refresh_token": payload.get("refresh_token") or bundle["refresh_token"],
        }
        tiktok_token_vault.put_token_bundle(
            account_id, replacement, conn=conn, merchant_id=credential_row["merchant_id"],
            connected_channel_id=credential_row["connected_channel_id"],
            expires_at=tiktok_oauth.expires_at(payload.get("expires_in")),
            refresh_expires_at=tiktok_oauth.expires_at(payload.get("refresh_expires_in")),
            issued_at=store.utc_now(),
        )
        logger.info("tiktok_token_refreshed merchant_id=%s account_id=%s", credential_row["merchant_id"], account_id)
        return {"access_token": access_token, "expires_in": payload.get("expires_in")}

    def revoke(self, conn, credential_row, config):
        bundle = tiktok_token_vault.get_token_bundle(
            credential_row["account_id"], conn=conn, merchant_id=credential_row["merchant_id"],
        )
        if not bundle:
            raise store.StoreError(401, "TikTok credential is unavailable.")
        payload = tiktok_oauth.request_json(
            "POST", config.get("revokeUrl", tiktok_oauth.TIKTOK_REVOKE_URL), {
                "client_key": config.get("clientKey", ""),
                "client_secret": config.get("clientSecret", ""),
                "token": bundle["access_token"],
            }, config.get("httpTransport"),
        )
        if not (payload.get("data") or {}).get("success", payload.get("success")):
            raise store.StoreError(502, "TikTok did not revoke the credential.")
        tiktok_token_vault.mark_reconnect_required(credential_row["account_id"], conn=conn)
        logger.info("tiktok_token_revoked account_id=%s", credential_row["account_id"])
        return {"revoked": True}

    def get_profile(self, token, config):
        payload = tiktok_oauth.request_json(
            "GET", tiktok_oauth.api_url(config, "/v2/user/info/?fields=open_id,display_name"),
            None, config.get("httpTransport"), {"Authorization": f"Bearer {token}"},
        )
        profile = (payload.get("data") or {}).get("user") or {}
        if not profile.get("open_id"):
            raise store.StoreError(502, "TikTok returned a malformed profile.")
        return profile

    def list_selectable_accounts(self, token, config):
        profile = self.get_profile(token, config)
        return [{"id": str(profile["open_id"]), "displayName": profile.get("display_name") or "TikTok business account"}]
