from urllib import parse

from backend.app import facebook_oauth, facebook_token_vault
from backend.app.auth_provider import AuthProvider


class FacebookAuthProvider(AuthProvider):
    def build_auth_url(self, config):
        return facebook_oauth.build_login_url(return_url=config.get("returnUrl"), config=config)

    def exchange_code(self, conn, code, config):
        user_token_payload = facebook_oauth.exchange_code_for_user_token(code, config)
        user_token = user_token_payload.get("access_token")
        if not user_token:
            return user_token_payload

        long_lived_payload = facebook_oauth.exchange_for_long_lived_user_token(user_token, config)
        if not long_lived_payload:
            return user_token_payload

        merged_payload = dict(user_token_payload)
        merged_payload.update(long_lived_payload)
        merged_payload["access_token"] = long_lived_payload.get("access_token") or user_token
        return merged_payload

    def refresh(self, conn, credential_row, config):
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": config.get("appId", ""),
            "client_secret": config.get("appSecret", ""),
            "fb_exchange_token": facebook_token_vault.get_page_token(
                credential_row["page_id"],
                conn=conn,
                merchant_id=credential_row["merchant_id"],
            ),
        }
        refresh_url = f"{config.get('graphBase', facebook_oauth.GRAPH_API_BASE)}/oauth/access_token?{parse.urlencode(params)}"
        return {
            "access_token": params["fb_exchange_token"],
            "token": params["fb_exchange_token"],
            "refresh_url": refresh_url,
        }

    def revoke(self, conn, credential_row, config):
        token = facebook_token_vault.get_page_token(
            credential_row["page_id"],
            conn=conn,
            merchant_id=credential_row["merchant_id"],
        )
        revoke_url = f"{config.get('graphBase', facebook_oauth.GRAPH_API_BASE)}/me/permissions?{parse.urlencode({'access_token': token})}"
        return {
            "revoked": False,
            "revoke_url": revoke_url,
        }

    def get_profile(self, token, config):
        params = {
            "fields": "id,name",
            "access_token": token,
        }
        return facebook_oauth.graph_get(
            f"{config.get('graphBase', facebook_oauth.GRAPH_API_BASE)}/me?{parse.urlencode(params)}"
        )

    def list_selectable_accounts(self, token, config):
        return facebook_oauth.fetch_pages(token, config)
