import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from backend.app import instagram_oauth, instagram_token_vault, store, token_crypto
from backend.app.instagram_auth_provider import InstagramAuthProvider


class InstagramOAuthTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)
        instagram_oauth.reset_for_tests(conn=self.conn)
        self.key = token_crypto.generate_dev_key()
        self.config = {
            "appId": "ig-app", "appSecret": "ig-secret",
            "redirectUri": "https://local.test/api/v1/instagram/oauth/callback",
            "returnUrl": "https://local.test/app?instagramConnected=1",
            "httpTransport": self.transport,
        }
        self.calls = []

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def env(self, **extra):
        values = {"LOCALPILOT_TOKEN_KEY": self.key, **extra}
        return patch.dict(os.environ, values, clear=False)

    def transport(self, *, method, url, data):
        self.calls.append((method, url, data))
        if method == "POST":
            return {"access_token": "short-token-should-not-leak"}
        if "grant_type=ig_exchange_token" in url:
            return {"access_token": "long-token-should-not-leak", "expires_in": 5183944}
        if "/refresh_access_token" in url:
            return {"access_token": "fresh-token-should-not-leak", "expires_in": 7200}
        if method == "DELETE":
            return {"success": True}
        if "/me?" in url:
            return {"id": "ig-123", "username": "aurora", "account_type": "BUSINESS"}
        raise AssertionError(f"unexpected request {method} {url}")

    def _state(self):
        url = instagram_oauth.build_login_url(conn=self.conn, config=self.config)
        return parse_qs(urlparse(url).query)["state"][0]

    def _connect(self):
        return instagram_oauth.complete_callback(
            self.conn, {"state": [self._state()], "code": ["callback-code-should-not-leak"]}, self.config,
        )

    def test_login_url_uses_required_scopes_and_db_backed_state(self):
        url = instagram_oauth.build_login_url(conn=self.conn, config=self.config)
        query = parse_qs(urlparse(url).query)
        self.assertEqual("code", query["response_type"][0])
        self.assertEqual(self.config["redirectUri"], query["redirect_uri"][0])
        self.assertEqual(set(instagram_oauth.REQUIRED_SCOPES), set(query["scope"][0].split(",")))
        self.assertEqual(self.config["returnUrl"], store.get_oauth_session(self.conn, query["state"][0], "state")["returnUrl"])

    def test_callback_returns_redacted_connect_session_then_selection_stores_ciphertext(self):
        with self.env(), self.assertLogs("backend.app.instagram_oauth", level="INFO") as logs:
            returned_url = self._connect()
            session_id = parse_qs(urlparse(returned_url).query)["connectSession"][0]
            accounts = instagram_oauth.list_accounts_for_session(session_id, conn=self.conn)
            staged_session = store.get_oauth_session(self.conn, session_id, "connect")
            status = instagram_oauth.select_account(self.conn, session_id, "ig-123")
        self.assertIn("connectSession=", returned_url)
        self.assertEqual([{"id": "ig-123", "username": "aurora", "accountType": "BUSINESS"}], accounts)
        self.assertNotIn("long-token-should-not-leak", str(staged_session))
        self.assertIn("credentialCiphertext", staged_session)
        self.assertEqual("ig-123", status["connectedAccounts"][0]["accountId"])
        channel = self.conn.execute("select * from connected_channels where id = ?", (store.INSTAGRAM_CHANNEL_ID,)).fetchone()
        self.assertEqual("connected", channel["status"])
        self.assertEqual("ig-123", channel["provider_channel_id"])
        self.assertEqual(["POST", "GET", "GET"], [call[0] for call in self.calls])
        self.assertIn("ig_exchange_token", self.calls[1][1])
        row = store.get_instagram_account_token_row(self.conn, "ig-123")
        self.assertIsNotNone(row)
        self.assertNotIn(b"long-token-should-not-leak", row["ciphertext"])
        self.assertNotIn("long-token-should-not-leak", str(dict(row)))
        self.assertIsNotNone(row["issued_at"])
        self.assertIsNotNone(row["token_expires_at"])
        expires_at = datetime.fromisoformat(row["token_expires_at"].replace("Z", "+00:00"))
        issued_at = datetime.fromisoformat(row["issued_at"].replace("Z", "+00:00"))
        self.assertGreater((expires_at - issued_at).total_seconds(), 5_000_000)
        self.assertTrue(any("instagram_account_token_stored" in line for line in logs.output))
        self.assertFalse(any("long-token-should-not-leak" in line or "callback-code-should-not-leak" in line for line in logs.output))
        with self.assertRaises(store.StoreError):
            instagram_oauth.list_accounts_for_session(session_id, conn=self.conn)

    def test_callback_replay_and_missing_code_are_rejected(self):
        with self.env():
            state = self._state()
            with self.assertRaises(store.StoreError) as missing:
                instagram_oauth.complete_callback(self.conn, {"state": [state]}, self.config)
            self.assertEqual(400, missing.exception.status)
            with self.assertRaises(store.StoreError) as replay:
                instagram_oauth.complete_callback(self.conn, {"state": [state], "code": ["again"]}, self.config)
        self.assertEqual(400, replay.exception.status)

    def test_expired_state_and_missing_configuration_are_rejected(self):
        expired = store.create_oauth_session(self.conn, "instagram", "state", {"returnUrl": "https://local.test"}, 0)
        with self.assertRaises(store.StoreError):
            instagram_oauth.complete_callback(self.conn, {"state": [expired], "code": ["x"]}, self.config)
        with self.assertRaises(store.StoreError) as ctx:
            instagram_oauth.build_login_url(conn=self.conn, config={"appId": ""})
        self.assertEqual(503, ctx.exception.status)

    def test_personal_account_and_malformed_responses_are_sanitized(self):
        provider = InstagramAuthProvider()
        personal = {**self.config, "httpTransport": lambda **_: {"id": "ig-1", "account_type": "PERSONAL"}}
        with self.assertRaises(store.StoreError) as personal_error:
            provider.list_selectable_accounts("secret-token", personal)
        self.assertEqual(403, personal_error.exception.status)
        with self.assertRaises(store.StoreError) as malformed:
            instagram_oauth.request_json("GET", "https://example.test", transport=lambda **_: [])
        self.assertEqual(502, malformed.exception.status)
        self.assertNotIn("secret-token", personal_error.exception.message)

    def test_exchange_rejects_missing_short_or_long_lived_token_without_secret_echo(self):
        provider = InstagramAuthProvider()
        missing_short = {**self.config, "httpTransport": lambda **_: {}}
        with self.assertRaises(store.StoreError) as short_error:
            provider.exchange_code(self.conn, "callback-code-private", missing_short)
        self.assertEqual(502, short_error.exception.status)
        calls = []
        def missing_long(**kwargs):
            calls.append(kwargs)
            return {"access_token": "short-private"} if kwargs["method"] == "POST" else {}
        with self.assertRaises(store.StoreError) as long_error:
            provider.exchange_code(self.conn, "callback-code-private", {**self.config, "httpTransport": missing_long})
        self.assertEqual(502, long_error.exception.status)
        self.assertEqual(2, len(calls))
        self.assertNotIn("callback-code-private", long_error.exception.message)

    def test_transport_provider_message_is_sanitized(self):
        def provider_failure(**_):
            raise store.StoreError(429, "provider said token=raw-secret")
        with self.assertRaises(store.StoreError) as ctx:
            instagram_oauth.request_json("GET", "https://example.test", transport=provider_failure)
        self.assertEqual(429, ctx.exception.status)
        self.assertEqual("Instagram OAuth request failed.", ctx.exception.message)

    def test_refresh_and_revoke_use_vault_and_redacted_metadata(self):
        with self.env():
            session_id = parse_qs(urlparse(self._connect()).query)["connectSession"][0]
            instagram_oauth.select_account(self.conn, session_id, "ig-123")
            provider = InstagramAuthProvider()
            row = store.get_instagram_account_token_row(self.conn, "ig-123")
            refreshed = provider.refresh(self.conn, row, self.config)
            self.assertEqual("fresh-token-should-not-leak", refreshed["access_token"])
            updated = store.get_instagram_account_token_row(self.conn, "ig-123")
            self.assertEqual("fresh-token-should-not-leak", instagram_token_vault.get_account_token("ig-123", conn=self.conn))
            self.assertTrue(provider.revoke(self.conn, updated, self.config)["revoked"])
            self.assertEqual("reconnect_required", store.get_instagram_account_token_row(self.conn, "ig-123")["status"])
            metadata = instagram_token_vault.list_connected_accounts(conn=self.conn)
        self.assertNotIn("fresh-token-should-not-leak", str(metadata))
        self.assertNotIn("ciphertext", metadata[0])

    def test_refresh_without_replacement_token_does_not_mutate_vault(self):
        with self.env():
            session_id = parse_qs(urlparse(self._connect()).query)["connectSession"][0]
            instagram_oauth.select_account(self.conn, session_id, "ig-123")
            row = store.get_instagram_account_token_row(self.conn, "ig-123")
            bad_config = {**self.config, "httpTransport": lambda **_: {}}
            with self.assertRaises(store.StoreError) as ctx:
                InstagramAuthProvider().refresh(self.conn, row, bad_config)
            self.assertEqual(502, ctx.exception.status)
            self.assertEqual("long-token-should-not-leak", instagram_token_vault.get_account_token("ig-123", conn=self.conn))

    def test_vault_fails_closed_without_encryption_and_has_no_memory_map(self):
        os.environ.pop("LOCALPILOT_TOKEN_KEY", None)
        with patch.dict(os.environ, {"LOCALPILOT_ENV": "production"}, clear=False):
            with self.assertRaises(store.StoreError) as ctx:
                instagram_token_vault.put_account_token("ig-1", "plaintext", conn=self.conn)
        self.assertEqual(503, ctx.exception.status)
        source = Path(instagram_oauth.__file__).read_text() + Path(instagram_token_vault.__file__).read_text()
        self.assertNotIn("_OAUTH_STATES", source)
        self.assertNotIn("_CONNECT_SESSIONS", source)
        self.assertNotIn("_PAGE_TOKENS", source)
        self.assertIn("consume_oauth_session", source)


if __name__ == "__main__":
    unittest.main()
