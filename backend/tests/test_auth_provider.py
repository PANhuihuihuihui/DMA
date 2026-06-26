import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app import auth_provider, store, token_crypto


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


class AuthProviderTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        self.conn = store.connect(self.db_path)
        store.initialize_database(self.conn)
        store.seed_demo_data(self.conn)
        self.env_patch = patch.dict(
            os.environ,
            {"LOCALPILOT_TOKEN_KEY": self._generate_test_key()},
            clear=False,
        )
        self.env_patch.start()

    def tearDown(self):
        self.conn.close()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def _generate_test_key(self):
        from cryptography.fernet import Fernet

        return Fernet.generate_key().decode("utf-8")

    def _iso_after(self, seconds):
        return (
            datetime.now(timezone.utc) + timedelta(seconds=seconds)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _seed_credential(self, token="valid-token", expires_in_seconds=3600, page_id="page_123"):
        ciphertext = token_crypto.encrypt_secret(token)
        store.upsert_facebook_page_token(
            self.conn,
            store.DEMO_MERCHANT_ID,
            store.FACEBOOK_CHANNEL_ID,
            page_id,
            ciphertext,
            "fp_test",
            expires_at=self._iso_after(expires_in_seconds),
            issued_at=self._iso_after(-60),
        )
        return store.get_facebook_page_token_row(self.conn, page_id, store.DEMO_MERCHANT_ID)

    def test_auth_provider_is_abstract(self):
        with self.assertRaises(TypeError):
            auth_provider.AuthProvider()

    def test_get_valid_credential_returns_plaintext_token(self):
        self._seed_credential(token="page-token", expires_in_seconds=900)

        token = auth_provider.get_valid_credential(
            self.conn,
            "page_123",
            store.DEMO_MERCHANT_ID,
        )

        self.assertEqual(token, "page-token")

    def test_get_valid_credential_warns_when_token_near_expiry(self):
        self._seed_credential(expires_in_seconds=240)

        with self.assertLogs("backend.app.auth_provider", level="WARNING") as logs:
            token = auth_provider.get_valid_credential(
                self.conn,
                "page_123",
                store.DEMO_MERCHANT_ID,
            )

        self.assertEqual(token, "valid-token")
        self.assertTrue(any("facebook_credential_expiring_soon" in line for line in logs.output))

    def test_get_valid_credential_raises_401_when_token_inside_buffer(self):
        self._seed_credential(expires_in_seconds=30)

        with self.assertRaises(store.StoreError) as exc:
            auth_provider.get_valid_credential(
                self.conn,
                "page_123",
                store.DEMO_MERCHANT_ID,
            )

        self.assertEqual(exc.exception.status, 401)

    def test_run_with_credential_refresh_retries_once_after_401(self):
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

    def test_run_with_credential_refresh_raises_second_error(self):
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

    def test_initialize_database_creates_oauth_sessions_table(self):
        tables = {
            row[0]
            for row in self.conn.execute(
                "select name from sqlite_master where type = 'table' and name = 'oauth_sessions'"
            )
        }

        self.assertEqual(tables, {"oauth_sessions"})

    def test_oauth_session_round_trip_and_consume(self):
        with self.assertLogs("backend.app.store", level="INFO") as logs:
            session_id = store.create_oauth_session(
                self.conn,
                "facebook",
                "state",
                {"merchant_id": "merchant_1"},
                ttl_seconds=600,
            )
            payload = store.get_oauth_session(self.conn, session_id, "state")
            consumed_payload = store.get_oauth_session(
                self.conn,
                session_id,
                "state",
                consume=True,
            )

        self.assertEqual(payload, {"merchant_id": "merchant_1"})
        self.assertEqual(consumed_payload, {"merchant_id": "merchant_1"})
        self.assertTrue(any("oauth_session_created" in line for line in logs.output))
        self.assertTrue(any("oauth_session_consumed" in line for line in logs.output))

        with self.assertRaises(store.StoreError) as exc:
            store.get_oauth_session(self.conn, session_id, "state")

        self.assertEqual(exc.exception.status, 400)

    def test_expired_oauth_session_is_rejected_and_cleanup_reports_removed_rows(self):
        expired_session_id = store.create_oauth_session(
            self.conn,
            "facebook",
            "connect",
            {"step": "connect"},
            ttl_seconds=-10,
        )
        store.create_oauth_session(
            self.conn,
            "facebook",
            "state",
            {"step": "state"},
            ttl_seconds=-20,
        )

        with self.assertRaises(store.StoreError) as exc:
            store.get_oauth_session(self.conn, expired_session_id, "connect")

        self.assertEqual(exc.exception.status, 400)

        with self.assertLogs("backend.app.store", level="INFO") as logs:
            removed = store.cleanup_expired_oauth_sessions(self.conn)

        self.assertEqual(removed, 1)
        self.assertTrue(any("oauth_session_cleanup removed=1" in line for line in logs.output))


if __name__ == "__main__":
    unittest.main()
