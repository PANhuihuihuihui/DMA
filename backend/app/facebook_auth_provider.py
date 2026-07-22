import logging

from backend.app import facebook_oauth, facebook_token_vault, store
from backend.app.auth_provider import AuthProvider


logger = logging.getLogger(__name__)


class FacebookAuthProvider(AuthProvider):
    def build_auth_url(self, config, conn=None):
        return facebook_oauth.build_login_url(
            return_url=config.get("returnUrl"),
            conn=conn,
            config=config,
        )

    def exchange_code(self, conn, code, config):
        user_token_payload = facebook_oauth.exchange_code_for_user_token(code, config)
        if not isinstance(user_token_payload, dict):
            raise store.StoreError(502, "Facebook returned a malformed user token response.")
        user_token = user_token_payload.get("access_token")
        if not user_token:
            raise store.StoreError(502, "Facebook did not return a user access token.")

        long_lived_payload = facebook_oauth.exchange_for_long_lived_user_token(user_token, config)
        if not long_lived_payload:
            return user_token_payload

        merged_payload = dict(user_token_payload)
        merged_payload.update(long_lived_payload)
        merged_payload["access_token"] = long_lived_payload.get("access_token") or user_token
        return merged_payload

    def refresh(self, conn, credential_row, config):
        page_token = facebook_token_vault.get_page_token(
            credential_row["page_id"],
            conn=conn,
            merchant_id=credential_row["merchant_id"],
        )
        if not page_token:
            raise store.StoreError(401, "Facebook Page credential is unavailable.")
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": config.get("appId", ""),
            "client_secret": config.get("appSecret", ""),
            "fb_exchange_token": page_token,
        }
        payload = facebook_oauth.graph_get(
            facebook_oauth.graph_url(config, "/oauth/access_token", params)
        )
        if not isinstance(payload, dict):
            raise store.StoreError(502, "Facebook returned a malformed refresh response.")
        new_token = payload.get("access_token")
        if not new_token:
            raise store.StoreError(502, "Facebook did not return a refreshed Page access token.")

        expires_in = payload.get("expires_in")
        expires_at = facebook_oauth._expires_at_from_seconds(expires_in)
        now = store.utc_now()
        facebook_token_vault.put_page_token(
            credential_row["page_id"],
            new_token,
            conn=conn,
            merchant_id=credential_row["merchant_id"],
            expires_at=expires_at,
            issued_at=now,
        )
        logger.info(
            "facebook_token_refreshed merchant_id=%s page_id=%s",
            credential_row["merchant_id"],
            credential_row["page_id"],
        )
        return {"access_token": new_token, "expires_in": expires_in}

    def revoke(self, conn, credential_row, config):
        page_id = credential_row["page_id"]
        token = facebook_token_vault.get_page_token(
            page_id,
            conn=conn,
            merchant_id=credential_row["merchant_id"],
        )
        if not token:
            raise store.StoreError(401, "Facebook Page credential is unavailable.")
        payload = facebook_oauth.graph_delete(
            facebook_oauth.graph_url(config, "/me/permissions", {"access_token": token})
        )
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise store.StoreError(502, "Facebook did not revoke the Page access token.")

        facebook_token_vault.mark_reconnect_required(page_id, conn=conn)
        logger.info("facebook_token_revoked page_id=%s", page_id)
        return {"revoked": True}

    def get_profile(self, token, config):
        params = {
            "fields": "id,name",
            "access_token": token,
        }
        return facebook_oauth.graph_get(facebook_oauth.graph_url(config, "/me", params))

    def list_selectable_accounts(self, token, config):
        return facebook_oauth.fetch_pages(token, config)
