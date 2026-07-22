import logging

from backend.app import instagram_oauth, instagram_token_vault, store
from backend.app.auth_provider import AuthProvider

logger = logging.getLogger(__name__)
_ALLOWED_ACCOUNT_TYPES = {"BUSINESS", "CREATOR"}


class InstagramAuthProvider(AuthProvider):
    def build_auth_url(self, config, conn=None):
        return instagram_oauth.build_login_url(
            return_url=config.get("returnUrl"), conn=conn, config=config,
        )

    def exchange_code(self, conn, code, config):
        short_payload = instagram_oauth.request_json(
            "POST", config.get("tokenUrl", instagram_oauth.INSTAGRAM_TOKEN_URL),
            {
                "client_id": config.get("appId", ""),
                "client_secret": config.get("appSecret", ""),
                "grant_type": "authorization_code",
                "redirect_uri": config.get("redirectUri", ""),
                "code": code,
            }, config.get("httpTransport"),
        )
        short_token = short_payload.get("access_token")
        if not short_token:
            raise store.StoreError(502, "Instagram did not return an authorization token.")
        long_payload = instagram_oauth.request_json(
            "GET", instagram_oauth.graph_url(config, "/access_token", {
                "grant_type": "ig_exchange_token",
                "client_secret": config.get("appSecret", ""),
                "access_token": short_token,
            }), None, config.get("httpTransport"),
        )
        long_token = long_payload.get("access_token")
        if not long_token:
            raise store.StoreError(502, "Instagram did not return a long-lived token.")
        result = dict(long_payload)
        result["access_token"] = long_token
        return result

    def refresh(self, conn, credential_row, config):
        account_id = credential_row["account_id"]
        token = instagram_token_vault.get_account_token(
            account_id, conn=conn, merchant_id=credential_row["merchant_id"],
        )
        if not token:
            raise store.StoreError(401, "Instagram credential is unavailable.")
        payload = instagram_oauth.request_json(
            "GET", instagram_oauth.graph_url(config, "/refresh_access_token", {
                "grant_type": "ig_refresh_token", "access_token": token,
            }), None, config.get("httpTransport"),
        )
        replacement = payload.get("access_token")
        if not replacement:
            raise store.StoreError(502, "Instagram did not return a refreshed token.")
        expires_at = instagram_oauth._expires_at(payload.get("expires_in"))
        instagram_token_vault.put_account_token(
            account_id, replacement, conn=conn,
            merchant_id=credential_row["merchant_id"],
            connected_channel_id=credential_row["connected_channel_id"],
            expires_at=expires_at, issued_at=store.utc_now(),
        )
        logger.info("instagram_token_refreshed merchant_id=%s account_id=%s", credential_row["merchant_id"], account_id)
        return {"access_token": replacement, "expires_in": payload.get("expires_in")}

    def revoke(self, conn, credential_row, config):
        account_id = credential_row["account_id"]
        token = instagram_token_vault.get_account_token(
            account_id, conn=conn, merchant_id=credential_row["merchant_id"],
        )
        if not token:
            raise store.StoreError(401, "Instagram credential is unavailable.")
        payload = instagram_oauth.request_json(
            "DELETE", instagram_oauth.graph_url(config, "/me/permissions", {"access_token": token}),
            None, config.get("httpTransport"),
        )
        if payload.get("success") is not True:
            raise store.StoreError(502, "Instagram did not revoke the credential.")
        instagram_token_vault.mark_reconnect_required(account_id, conn=conn)
        logger.info("instagram_token_revoked account_id=%s", account_id)
        return {"revoked": True}

    def get_profile(self, token, config):
        payload = instagram_oauth.request_json(
            "GET", instagram_oauth.graph_url(config, "/me", {
                "fields": "id,username,account_type", "access_token": token,
            }), None, config.get("httpTransport"),
        )
        if not payload.get("id"):
            raise store.StoreError(502, "Instagram returned a malformed profile.")
        return payload

    def list_selectable_accounts(self, token, config):
        profile = self.get_profile(token, config)
        account_type = str(profile.get("account_type") or "").upper()
        if account_type not in _ALLOWED_ACCOUNT_TYPES:
            raise store.StoreError(403, "Instagram account must be a Business or Creator account.")
        return [{
            "id": str(profile["id"]), "username": profile.get("username", ""),
            "accountType": account_type,
        }]
