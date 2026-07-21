import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app import auth_provider, store, token_crypto
from backend.app.facebook_auth_provider import FacebookAuthProvider


class DummyProvider(auth_provider.AuthProvider):
    def __init__(self, refreshed_payload=None):
        self.refreshed_payload = refreshed_payload or {"access_token": "refreshed-token"}
        self.refresh_calls = 0

    def build_auth_url(self, config):
        return "https://example.test/oauth"

    def exchange_code(self, conn, code, config):
        return {"access_token": "code-token"}

    def refresh(self, conn, credential_row, config):
        self.refresh_calls += 1
        return self.refreshed_payload

    def revoke(self, conn, credential_row, config):
        return None

    def get_profile(self, token, config):
        return {"id": "profile_123"}

    def list_selectable_accounts(self, token, config):
        return []


class TempDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        self.conn = store.connect(self.db_path)
        store.initialize_database(self.conn)
        store.seed_demo_data(self.conn)
        self.env_patch = patch.dict(
            os.environ,
            {"LOCALPILOT_TOKEN_KEY": token_crypto.generate_dev_key()},
            clear=False,
        )
        self.env_patch.start()

    def tearDown(self):
        self.conn.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def _iso_after(self, seconds):
        return (
            datetime.now(timezone.utc) + timedelta(seconds=seconds)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _seed_credential(self, token="valid-token", expires_in_seconds=3600, page_id="page_123"):
        ciphertext = token_crypto.encrypt_secret(token)
        expires_at = None if expires_in_seconds is None else self._iso_after(expires_in_seconds)
        store.upsert_facebook_page_token(
            self.conn,
            store.DEMO_MERCHANT_ID,
            store.FACEBOOK_CHANNEL_ID,
            page_id,
            ciphertext,
            "fp_test",
            expires_at=expires_at,
            issued_at=self._iso_after(-60),
        )
        return store.get_facebook_page_token_row(self.conn, page_id, store.DEMO_MERCHANT_ID)


class TestAuthProviderABC(TempDatabaseTestCase):
    def test_cannot_instantiate_abc(self):
        with self.assertRaises(TypeError):
            auth_provider.AuthProvider()

    def test_facebook_provider_is_auth_provider(self):
        self.assertIsInstance(FacebookAuthProvider(), auth_provider.AuthProvider)


class TestOAuthSessionDB(TempDatabaseTestCase):
    def test_create_and_fetch_session(self):
        with self.assertLogs("backend.app.store", level="INFO") as logs:
            session_id = store.create_oauth_session(
                self.conn,
                "facebook",
                "state",
                {"merchant_id": "merchant_1", "nonce": "n_123"},
                ttl_seconds=600,
            )
            payload = store.get_oauth_session(self.conn, session_id, "state")

        self.assertEqual(payload, {"merchant_id": "merchant_1", "nonce": "n_123"})
        self.assertTrue(any("oauth_session_created" in line for line in logs.output))
        self.assertTrue(any("oauth_session_loaded" in line for line in logs.output))

    def test_consume_session_removes_row(self):
        session_id = store.create_oauth_session(
            self.conn,
            "facebook",
            "state",
            {"merchant_id": "merchant_1"},
            ttl_seconds=600,
        )

        payload = store.get_oauth_session(self.conn, session_id, "state", consume=True)

        self.assertEqual(payload, {"merchant_id": "merchant_1"})
        with self.assertRaises(store.StoreError) as exc:
            store.get_oauth_session(self.conn, session_id, "state")
        self.assertEqual(exc.exception.status, 400)

    def test_expired_session_raises(self):
        session_id = store.create_oauth_session(
            self.conn,
            "facebook",
            "connect",
            {"step": "connect"},
            ttl_seconds=0,
        )

        time.sleep(1.1)

        with self.assertRaises(store.StoreError) as exc:
            store.get_oauth_session(self.conn, session_id, "connect")
        self.assertEqual(exc.exception.status, 400)
        self.assertEqual(exc.exception.message, "OAuth session expired.")

    def test_invalid_session_id_raises(self):
        with self.assertRaises(store.StoreError) as exc:
            store.get_oauth_session(self.conn, "oauth_missing", "state")
        self.assertEqual(exc.exception.status, 400)
        self.assertEqual(exc.exception.message, "OAuth session not found.")

    def test_cleanup_removes_expired(self):
        expired_session_id = store.create_oauth_session(
            self.conn,
            "facebook",
            "connect",
            {"step": "expired"},
            ttl_seconds=0,
        )
        valid_session_id = store.create_oauth_session(
            self.conn,
            "facebook",
            "state",
            {"step": "valid"},
            ttl_seconds=600,
        )

        time.sleep(1.1)

        with self.assertLogs("backend.app.store", level="INFO") as logs:
            removed = store.cleanup_expired_oauth_sessions(self.conn)

        self.assertEqual(removed, 1)
        self.assertTrue(any("oauth_session_cleanup removed=1" in line for line in logs.output))
        self.assertEqual(
            store.get_oauth_session(self.conn, valid_session_id, "state"),
            {"step": "valid"},
        )
        with self.assertRaises(store.StoreError) as exc:
            store.get_oauth_session(self.conn, expired_session_id, "connect")
        self.assertEqual(exc.exception.status, 400)


class TestGetValidCredential(TempDatabaseTestCase):
    def test_valid_token_returns_plaintext(self):
        self._seed_credential(token="page-token", expires_in_seconds=3600)

        token = auth_provider.get_valid_credential(
            self.conn,
            "page_123",
            store.DEMO_MERCHANT_ID,
        )

        self.assertEqual(token, "page-token")

    def test_expired_token_raises_401(self):
        self._seed_credential(expires_in_seconds=-60)

        with self.assertRaises(store.StoreError) as exc:
            auth_provider.get_valid_credential(
                self.conn,
                "page_123",
                store.DEMO_MERCHANT_ID,
            )

        self.assertEqual(exc.exception.status, 401)
        self.assertEqual(exc.exception.message, "Facebook credential expired.")

    def test_near_expiry_within_buffer_raises(self):
        self._seed_credential(expires_in_seconds=30)

        with self.assertRaises(store.StoreError) as exc:
            auth_provider.get_valid_credential(
                self.conn,
                "page_123",
                store.DEMO_MERCHANT_ID,
                buffer_seconds=60,
            )

        self.assertEqual(exc.exception.status, 401)
        self.assertEqual(exc.exception.message, "Facebook credential expired.")

    def test_no_expiry_set_returns_token(self):
        self._seed_credential(token="page-token", expires_in_seconds=None)

        token = auth_provider.get_valid_credential(
            self.conn,
            "page_123",
            store.DEMO_MERCHANT_ID,
        )

        self.assertEqual(token, "page-token")

    def test_warns_when_token_within_300_seconds(self):
        self._seed_credential(expires_in_seconds=240)

        with self.assertLogs("backend.app.auth_provider", level="WARNING") as logs:
            token = auth_provider.get_valid_credential(
                self.conn,
                "page_123",
                store.DEMO_MERCHANT_ID,
            )

        self.assertEqual(token, "valid-token")
        self.assertTrue(any("facebook_credential_expiring_soon" in line for line in logs.output))


class TestRunWithCredentialRefresh(TempDatabaseTestCase):
    def test_success_without_refresh(self):
        credential_row = self._seed_credential(token="valid-token")
        provider = DummyProvider({"access_token": "unused-token"})
        seen_tokens = []

        def operation(token):
            seen_tokens.append(token)
            return {"token": token, "status": "ok"}

        result = auth_provider.run_with_credential_refresh(
            self.conn,
            provider,
            credential_row,
            {},
            operation,
        )

        self.assertEqual(result, {"token": "valid-token", "status": "ok"})
        self.assertEqual(seen_tokens, ["valid-token"])
        self.assertEqual(provider.refresh_calls, 0)

    def test_retries_on_auth_failure(self):
        credential_row = self._seed_credential(token="stale-token")
        provider = DummyProvider({"access_token": "fresh-token"})
        seen_tokens = []

        def operation(token):
            seen_tokens.append(token)
            if token == "stale-token":
                raise store.StoreError(401, "expired")
            return {"token": token, "status": "ok"}

        result = auth_provider.run_with_credential_refresh(
            self.conn,
            provider,
            credential_row,
            {},
            operation,
        )

        self.assertEqual(result, {"token": "fresh-token", "status": "ok"})
        self.assertEqual(seen_tokens, ["stale-token", "fresh-token"])
        self.assertEqual(provider.refresh_calls, 1)

    def test_refresh_without_token_raises_502(self):
        credential_row = self._seed_credential(token="stale-token")
        provider = DummyProvider({"refresh_token": "missing-access-token"})

        def operation(token):
            raise store.StoreError(401, "expired")

        with self.assertRaises(store.StoreError) as exc:
            auth_provider.run_with_credential_refresh(
                self.conn,
                provider,
                credential_row,
                {},
                operation,
            )

        self.assertEqual(exc.exception.status, 502)
        self.assertEqual(exc.exception.message, "Provider refresh did not return an access token.")
        self.assertEqual(provider.refresh_calls, 1)

    def test_raises_on_second_failure(self):
        credential_row = self._seed_credential(token="stale-token")
        provider = DummyProvider({"access_token": "still-bad-token"})
        attempts = []

        def operation(token):
            attempts.append(token)
            if len(attempts) == 1:
                raise store.StoreError(401, "first failure")
            raise store.StoreError(401, "second failure")

        with self.assertRaises(store.StoreError) as exc:
            auth_provider.run_with_credential_refresh(
                self.conn,
                provider,
                credential_row,
                {},
                operation,
            )

        self.assertEqual(exc.exception.status, 401)
        self.assertEqual(exc.exception.message, "second failure")
        self.assertEqual(attempts, ["stale-token", "still-bad-token"])
        self.assertEqual(provider.refresh_calls, 1)

    def test_non_auth_error_not_retried(self):
        credential_row = self._seed_credential(token="valid-token")
        provider = DummyProvider({"access_token": "should-not-be-used"})
        seen_tokens = []

        def operation(token):
            seen_tokens.append(token)
            raise store.StoreError(500, "boom")

        with self.assertRaises(store.StoreError) as exc:
            auth_provider.run_with_credential_refresh(
                self.conn,
                provider,
                credential_row,
                {},
                operation,
            )

        self.assertEqual(exc.exception.status, 500)
        self.assertEqual(exc.exception.message, "boom")
        self.assertEqual(seen_tokens, ["valid-token"])
        self.assertEqual(provider.refresh_calls, 0)


if __name__ == "__main__":
    unittest.main()
