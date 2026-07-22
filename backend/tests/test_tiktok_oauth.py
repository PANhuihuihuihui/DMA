import hashlib
import json
import os
import tempfile
import unittest
from base64 import urlsafe_b64encode
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from backend.app import auth_provider, store, tiktok_oauth, tiktok_token_vault, token_crypto
from backend.app.tiktok_auth_provider import TikTokAuthProvider


class TikTokOAuthTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)
        self.key = token_crypto.generate_dev_key()
        self.calls = []
        self.config = {
            "clientKey": "tt-client-key",
            "clientSecret": "tt-client-secret",
            "redirectUri": "https://local.test/api/v1/tiktok/oauth/callback",
            "returnUrl": "https://local.test/app?tiktokConnected=1",
            "httpTransport": self.transport,
        }

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def env(self):
        return patch.dict(os.environ, {"LOCALPILOT_TOKEN_KEY": self.key}, clear=False)

    def transport(self, *, method, url, data=None, headers=None):
        self.calls.append((method, url, data, headers or {}))
        if (data or {}).get("grant_type") == "refresh_token":
            return {"access_token": "rotated-access-secret", "refresh_token": "rotated-refresh-secret", "expires_in": 3600}
        if method == "POST":
            self.assertEqual("authorization_code", data["grant_type"])
            self.assertTrue(data["code_verifier"])
            return {"access_token": "access-secret", "refresh_token": "refresh-secret", "expires_in": 7200, "refresh_expires_in": 86400}
        if "/v2/user/info/" in url:
            return {"data": {"user": {"open_id": "tt-open-id", "display_name": "Aurora HVAC"}}}
        if method == "DELETE":
            return {"data": {"success": True}}
        raise AssertionError(f"unexpected request {method} {url}")

    def _state(self):
        url = tiktok_oauth.build_login_url(conn=self.conn, config=self.config)
        return url, parse_qs(urlparse(url).query)["state"][0]

    def _connect(self):
        _url, state = self._state()
        return tiktok_oauth.complete_callback(self.conn, {"state": [state], "code": ["private-code"]}, self.config)

    def test_login_url_uses_s256_pkce_and_persists_only_encrypted_verifier(self):
        with self.env():
            url, state = self._state()
            query = parse_qs(urlparse(url).query)
            session = store.get_oauth_session(self.conn, state, "state")
            verifier = token_crypto.decrypt_secret(session["pkceVerifierCiphertext"].encode("utf-8"))
            challenge = urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual("code", query["response_type"][0])
        self.assertEqual("S256", query["code_challenge_method"][0])
        self.assertEqual(self.config["redirectUri"], query["redirect_uri"][0])
        self.assertEqual(challenge, query["code_challenge"][0])
        self.assertNotIn(verifier, str(session))
        self.assertNotIn("tt-client-secret", url)

    def test_callback_is_one_time_and_token_bundle_is_encrypted(self):
        with self.env(), self.assertLogs("backend.app.tiktok_oauth", level="INFO") as logs:
            returned_url = self._connect()
            session_id = parse_qs(urlparse(returned_url).query)["connectSession"][0]
            accounts = tiktok_oauth.list_accounts_for_session(session_id, conn=self.conn)
            staged = store.get_oauth_session(self.conn, session_id, "connect")
            status = tiktok_oauth.select_account(self.conn, session_id, "tt-open-id")
        self.assertEqual([{"id": "tt-open-id", "displayName": "Aurora HVAC"}], accounts)
        self.assertNotIn("access-secret", str(staged))
        self.assertNotIn("refresh-secret", str(staged))
        row = store.get_tiktok_account_token_row(self.conn, "tt-open-id")
        self.assertIsNotNone(row)
        self.assertNotIn(b"access-secret", row["ciphertext"])
        self.assertNotIn(b"refresh-secret", row["ciphertext"])
        self.assertEqual("tt-open-id", status["connectedAccounts"][0]["accountId"])
        self.assertTrue(any("tiktok_account_token_stored" in line for line in logs.output))
        self.assertFalse(any("private-code" in line or "access-secret" in line for line in logs.output))
        with self.assertRaises(store.StoreError):
            tiktok_oauth.list_accounts_for_session(session_id, conn=self.conn)

    def test_callback_replay_missing_config_and_provider_error_are_sanitized(self):
        with self.env():
            _url, state = self._state()
            with self.assertRaises(store.StoreError) as missing:
                tiktok_oauth.complete_callback(self.conn, {"state": [state]}, self.config)
            self.assertEqual(400, missing.exception.status)
            with self.assertRaises(store.StoreError) as replay:
                tiktok_oauth.complete_callback(self.conn, {"state": [state], "code": ["again"]}, self.config)
            self.assertEqual(400, replay.exception.status)
        with self.assertRaises(store.StoreError) as config_error:
            tiktok_oauth.build_login_url(conn=self.conn, config={"clientKey": ""})
        self.assertEqual(503, config_error.exception.status)
        with self.assertRaises(store.StoreError) as request_error:
            tiktok_oauth.request_json("GET", "https://example.test", transport=lambda **_: [])
        self.assertEqual(502, request_error.exception.status)

    def test_refresh_rotates_access_and_refresh_credentials_without_disclosure(self):
        with self.env():
            session_id = parse_qs(urlparse(self._connect()).query)["connectSession"][0]
            tiktok_oauth.select_account(self.conn, session_id, "tt-open-id")
            row = store.get_tiktok_account_token_row(self.conn, "tt-open-id")
            refreshed = TikTokAuthProvider().refresh(self.conn, row, self.config)
            bundle = tiktok_token_vault.get_token_bundle("tt-open-id", conn=self.conn)
            metadata = tiktok_token_vault.list_connected_accounts(conn=self.conn)
            resolved_access_token = auth_provider.get_valid_credential(
                self.conn, "tt-open-id", store.DEMO_MERCHANT_ID, provider="tiktok",
            )
        self.assertEqual("rotated-access-secret", refreshed["access_token"])
        self.assertEqual("rotated-access-secret", bundle["access_token"])
        self.assertEqual("rotated-refresh-secret", bundle["refresh_token"])
        self.assertNotIn("rotated-access-secret", str(metadata))
        self.assertNotIn("ciphertext", metadata[0])
        self.assertEqual("rotated-access-secret", resolved_access_token)

    def test_vault_fails_closed_without_encryption(self):
        os.environ.pop("LOCALPILOT_TOKEN_KEY", None)
        with patch.dict(os.environ, {"LOCALPILOT_ENV": "production"}, clear=False):
            with self.assertRaises(store.StoreError) as context:
                tiktok_token_vault.put_token_bundle("tt-id", {"access_token": "plaintext"}, conn=self.conn)
        self.assertEqual(503, context.exception.status)


if __name__ == "__main__":
    unittest.main()
