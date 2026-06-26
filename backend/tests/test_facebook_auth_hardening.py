from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib import error

from backend.app import facebook_oauth, facebook_token_vault, store
from backend.app.facebook_auth_provider import FacebookAuthProvider
from backend.tests.test_auth_provider import TempDatabaseTestCase


class _BadJsonResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b"{not-json"


class TestFacebookRefreshRevoke(TempDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.provider = FacebookAuthProvider()
        self.config = {
            "appId": "app-123",
            "appSecret": "secret-456",
            "graphBase": "https://graph.facebook.test",
        }
        self.page_id = "page-123"
        self.merchant_id = store.DEMO_MERCHANT_ID
        self.original_token = "old-page-token"
        self.original_expires_at = (
            datetime.now(timezone.utc) + timedelta(days=7)
        ).replace(microsecond=0).isoformat()
        facebook_token_vault.put_page_token(
            self.page_id,
            self.original_token,
            conn=self.conn,
            merchant_id=self.merchant_id,
            connected_channel_id=store.FACEBOOK_CHANNEL_ID,
            expires_at=self.original_expires_at,
            issued_at="2026-01-01T00:00:00+00:00",
        )

    def _credential_row(self):
        row = store.get_facebook_page_token_row(
            self.conn,
            self.page_id,
            merchant_id=self.merchant_id,
        )
        self.assertIsNotNone(row)
        return row

    def test_refresh_calls_graph_and_persists_new_token(self):
        refreshed_token = "new-page-token"
        with self.assertLogs("backend.app.facebook_auth_provider", level="INFO") as logs:
            with patch(
                "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
                return_value={"access_token": refreshed_token, "expires_in": 7200},
            ) as graph_get:
                result = self.provider.refresh(self.conn, self._credential_row(), self.config)

        self.assertEqual(result, {"access_token": refreshed_token, "expires_in": 7200})
        self.assertEqual(
            facebook_token_vault.get_page_token(
                self.page_id,
                conn=self.conn,
                merchant_id=self.merchant_id,
            ),
            refreshed_token,
        )
        refreshed_row = self._credential_row()
        self.assertEqual(refreshed_row["status"], "active")
        self.assertIsNotNone(refreshed_row["issued_at"])
        self.assertIsNotNone(refreshed_row["token_expires_at"])
        self.assertNotEqual(refreshed_row["issued_at"], "2026-01-01T00:00:00+00:00")
        self.assertNotEqual(refreshed_row["token_expires_at"], self.original_expires_at)
        called_url = graph_get.call_args.args[0]
        self.assertIn("/oauth/access_token?", called_url)
        self.assertIn("grant_type=fb_exchange_token", called_url)
        self.assertIn("client_id=app-123", called_url)
        self.assertIn("client_secret=secret-456", called_url)
        self.assertIn("fb_exchange_token=old-page-token", called_url)
        self.assertTrue(
            any(
                f"facebook_token_refreshed merchant_id={self.merchant_id} page_id={self.page_id}" in line
                for line in logs.output
            )
        )

    def test_revoke_calls_graph_delete_and_marks_reconnect_required(self):
        with self.assertLogs("backend.app.facebook_auth_provider", level="INFO") as logs:
            with patch(
                "backend.app.facebook_auth_provider.facebook_oauth.graph_delete",
                return_value={"success": True},
            ) as graph_delete:
                result = self.provider.revoke(self.conn, self._credential_row(), self.config)

        self.assertEqual(result, {"revoked": True})
        revoked_row = self._credential_row()
        self.assertEqual(revoked_row["status"], "reconnect_required")
        called_url = graph_delete.call_args.args[0]
        self.assertIn("/me/permissions?", called_url)
        self.assertIn("access_token=old-page-token", called_url)
        self.assertTrue(
            any(f"facebook_token_revoked page_id={self.page_id}" in line for line in logs.output)
        )

    def test_refresh_raises_store_error_when_graph_response_has_no_access_token(self):
        with patch(
            "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
            return_value={"expires_in": 7200},
        ):
            with self.assertRaises(store.StoreError) as ctx:
                self.provider.refresh(self.conn, self._credential_row(), self.config)

        self.assertEqual(ctx.exception.status, 502)
        self.assertIn("refreshed Page access token", ctx.exception.message)
        self.assertEqual(
            facebook_token_vault.get_page_token(
                self.page_id,
                conn=self.conn,
                merchant_id=self.merchant_id,
            ),
            self.original_token,
        )

    def test_revoke_raises_store_error_when_graph_delete_reports_failure(self):
        with patch(
            "backend.app.facebook_auth_provider.facebook_oauth.graph_delete",
            return_value={"success": False},
        ):
            with self.assertRaises(store.StoreError) as ctx:
                self.provider.revoke(self.conn, self._credential_row(), self.config)

        self.assertEqual(ctx.exception.status, 502)
        self.assertIn("did not revoke", ctx.exception.message)
        self.assertEqual(self._credential_row()["status"], "active")

    def test_graph_delete_wraps_network_failure_as_store_error(self):
        with patch(
            "backend.app.facebook_oauth.request.urlopen",
            side_effect=error.URLError("connection dropped"),
        ):
            with self.assertRaises(store.StoreError) as ctx:
                facebook_oauth.graph_delete("https://graph.facebook.test/me/permissions?access_token=token")

        self.assertEqual(ctx.exception.status, 502)
        self.assertEqual(ctx.exception.message, "Facebook OAuth request failed.")

    def test_graph_get_wraps_malformed_json_as_store_error(self):
        with patch("backend.app.facebook_oauth.request.urlopen", return_value=_BadJsonResponse()):
            with self.assertRaises(store.StoreError) as ctx:
                facebook_oauth.graph_get("https://graph.facebook.test/oauth/access_token")

        self.assertEqual(ctx.exception.status, 502)
        self.assertEqual(ctx.exception.message, "Facebook OAuth returned malformed JSON.")
