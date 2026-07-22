import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from backend.app import store, token_crypto


logger = logging.getLogger(__name__)


def _parse_utc(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class AuthProvider(ABC):
    @abstractmethod
    def build_auth_url(self, config):
        raise NotImplementedError

    @abstractmethod
    def exchange_code(self, conn, code, config):
        raise NotImplementedError

    @abstractmethod
    def refresh(self, conn, credential_row, config):
        raise NotImplementedError

    @abstractmethod
    def revoke(self, conn, credential_row, config):
        raise NotImplementedError

    @abstractmethod
    def get_profile(self, token, config):
        raise NotImplementedError

    @abstractmethod
    def list_selectable_accounts(self, token, config):
        raise NotImplementedError


def get_valid_credential(conn, account_id, merchant_id, buffer_seconds=60, provider="facebook"):
    lookups = {
        "facebook": store.get_facebook_page_token_row,
        "instagram": store.get_instagram_account_token_row,
        "tiktok": store.get_tiktok_account_token_row,
    }
    lookup = lookups.get(provider)
    if lookup is None:
        raise store.StoreError(400, "Unsupported credential provider.")
    credential_row = lookup(conn, account_id, merchant_id)
    if credential_row is None:
        raise store.StoreError(404, f"{provider.title()} credential not found for account {account_id}.")

    expires_at = _parse_utc(credential_row["token_expires_at"])
    if expires_at is not None:
        seconds_remaining = (expires_at - datetime.now(timezone.utc)).total_seconds()
        if seconds_remaining <= buffer_seconds:
            raise store.StoreError(401, f"{provider.title()} credential expired.")
        if seconds_remaining <= 300:
            logger.warning(
                "%s_credential_expiring_soon merchant_id=%s account_id=%s expires_in_seconds=%s",
                provider,
                merchant_id,
                account_id,
                max(0, int(seconds_remaining)),
            )

    plaintext = token_crypto.decrypt_secret(credential_row["ciphertext"])
    if provider == "tiktok":
        try:
            bundle = json.loads(plaintext)
        except json.JSONDecodeError as exc:
            raise store.StoreError(503, "TikTok credential store is invalid.") from exc
        if not bundle.get("access_token"):
            raise store.StoreError(503, "TikTok credential store is invalid.")
        return bundle["access_token"]
    return plaintext


def run_with_credential_refresh(conn, provider, credential_row, config, operation):
    token = token_crypto.decrypt_secret(credential_row["ciphertext"])
    if provider.__class__.__name__ == "TikTokAuthProvider":
        try:
            token = json.loads(token)["access_token"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise store.StoreError(503, "TikTok credential store is invalid.") from exc
    try:
        return operation(token)
    except store.StoreError as exc:
        if exc.status != 401:
            raise

    refreshed_payload = provider.refresh(conn, credential_row, config)
    refreshed_token = refreshed_payload.get("access_token") or refreshed_payload.get("token")
    if not refreshed_token:
        raise store.StoreError(502, "Provider refresh did not return an access token.")

    logger.info(
        "credential_refresh_retry provider=%s credential_id=%s",
        provider.__class__.__name__,
        credential_row["id"],
    )
    return operation(refreshed_token)
