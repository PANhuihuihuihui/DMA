import json
import os
from datetime import datetime, timedelta, timezone
from io import BytesIO
from unittest.mock import patch
from urllib import error

from backend.app import facebook_oauth, facebook_publisher, facebook_token_vault, store
from backend.app.facebook_auth_provider import FacebookAuthProvider
from backend.tests.test_auth_provider import TempDatabaseTestCase


class _BadJsonResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b"{not-json"


class _JsonResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


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


class TestPublishCredentialIntegration(TempDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.graph_base = "https://graph.facebook.test"
        self.facebook_env = patch.dict(
            os.environ,
            {
                "FACEBOOK_APP_ID": "app-123",
                "FACEBOOK_APP_SECRET": "secret-456",
                "FACEBOOK_GRAPH_API_BASE": self.graph_base,
            },
            clear=False,
        )
        self.facebook_env.start()

    def tearDown(self):
        facebook_token_vault.clear()
        self.facebook_env.stop()
        super().tearDown()

    def approve_facebook(self):
        workflow = store.get_workflow(self.conn)
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == "facebook")
        return store.approve_draft(
            self.conn,
            draft["id"],
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
            },
        )["approval"]

    def approval_snapshot(self):
        approval = self.approve_facebook()
        approval_row = store.get_approval(self.conn, approval["id"])
        return json.loads(approval_row["snapshot_json"]), approval, approval_row

    def seed_page_token(self, snapshot, token="old-page-token", expires_in_seconds=3600):
        merchant_id = snapshot.get("merchantId") or store.DEMO_MERCHANT_ID
        page_id = str((snapshot.get("connectedChannelRef") or {}).get("providerChannelId"))
        facebook_token_vault.put_page_token(
            page_id,
            token,
            conn=self.conn,
            merchant_id=merchant_id,
            connected_channel_id=store.FACEBOOK_CHANNEL_ID,
            expires_at=self._iso_after(expires_in_seconds),
            issued_at=self._iso_after(-60),
        )
        return page_id, merchant_id

    def raise_auth_http_error(self, req, message="Invalid OAuth access token."):
        payload = {"error": {"message": message, "code": 190}}
        raise error.HTTPError(
            req.full_url,
            401,
            "Unauthorized",
            {},
            BytesIO(json.dumps(payload).encode("utf-8")),
        )

    def test_publish_approved_snapshot_refreshes_expired_token_before_graph_publish(self):
        snapshot, _, _ = self.approval_snapshot()
        page_id, merchant_id = self.seed_page_token(snapshot, expires_in_seconds=-30)
        auth_headers = []

        def opener(req, timeout=15):
            auth_header = req.headers.get("Authorization")
            auth_headers.append(auth_header)
            if auth_header == "Bearer old-page-token":
                raise AssertionError("expired token reached the Graph publish call")
            if req.full_url.endswith("/feed"):
                self.assertEqual(auth_header, "Bearer refreshed-token")
                return _JsonResponse({"id": "post_123"})
            if "fields=permalink_url,is_published,created_time" in req.full_url:
                self.assertEqual(auth_header, "Bearer refreshed-token")
                return _JsonResponse(
                    {
                        "permalink_url": "https://facebook.test/posts/post_123",
                        "is_published": True,
                        "created_time": "2026-01-01T00:00:00+0000",
                    }
                )
            raise AssertionError(f"Unexpected request {req.full_url}")

        with patch(
            "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
            return_value={"access_token": "refreshed-token", "expires_in": 7200},
        ):
            result = facebook_publisher.publish_approved_snapshot(
                snapshot,
                user_token=None,
                page_id=page_id,
                publish_mode="publish_now",
                scheduled_publish_time=None,
                graph_base=self.graph_base,
                conn=self.conn,
                opener=opener,
                media_info={"kind": "text"},
            )

        self.assertEqual(result["postId"], "post_123")
        self.assertEqual(
            facebook_token_vault.get_page_token(page_id, conn=self.conn, merchant_id=merchant_id),
            "refreshed-token",
        )
        self.assertEqual(auth_headers, ["Bearer refreshed-token", "Bearer refreshed-token"])

    def test_publish_approved_snapshot_retries_once_after_graph_auth_failure(self):
        snapshot, _, _ = self.approval_snapshot()
        page_id, merchant_id = self.seed_page_token(snapshot, expires_in_seconds=3600)
        feed_auth_headers = []

        def opener(req, timeout=15):
            auth_header = req.headers.get("Authorization")
            if req.full_url.endswith("/feed"):
                feed_auth_headers.append(auth_header)
                if auth_header == "Bearer old-page-token":
                    self.raise_auth_http_error(req)
                self.assertEqual(auth_header, "Bearer refreshed-token")
                return _JsonResponse({"id": "post_retry"})
            if "fields=permalink_url,is_published,created_time" in req.full_url:
                self.assertEqual(auth_header, "Bearer refreshed-token")
                return _JsonResponse(
                    {
                        "permalink_url": "https://facebook.test/posts/post_retry",
                        "is_published": True,
                        "created_time": "2026-01-01T00:00:00+0000",
                    }
                )
            raise AssertionError(f"Unexpected request {req.full_url}")

        with self.assertLogs("backend.app.facebook_publisher", level="WARNING") as logs:
            with patch(
                "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
                return_value={"access_token": "refreshed-token", "expires_in": 7200},
            ):
                result = facebook_publisher.publish_approved_snapshot(
                    snapshot,
                    user_token=None,
                    page_id=page_id,
                    publish_mode="publish_now",
                    scheduled_publish_time=None,
                    graph_base=self.graph_base,
                    conn=self.conn,
                    opener=opener,
                    media_info={"kind": "text"},
                )

        self.assertEqual(result["postId"], "post_retry")
        self.assertEqual(feed_auth_headers, ["Bearer old-page-token", "Bearer refreshed-token"])
        self.assertTrue(
            any("facebook_publish_auth_retry" in entry and page_id in entry and merchant_id in entry for entry in logs.output)
        )

    def test_publish_approved_snapshot_marks_reconnect_required_when_refresh_fails(self):
        snapshot, _, _ = self.approval_snapshot()
        page_id, merchant_id = self.seed_page_token(snapshot, expires_in_seconds=3600)

        def opener(req, timeout=15):
            if req.full_url.endswith("/feed"):
                self.raise_auth_http_error(req)
            raise AssertionError(f"Unexpected request {req.full_url}")

        with patch(
            "backend.app.facebook_publisher.FacebookAuthProvider.refresh",
            side_effect=store.StoreError(502, "refresh failed"),
        ):
            with self.assertRaises(facebook_publisher.FacebookProviderError) as ctx:
                facebook_publisher.publish_approved_snapshot(
                    snapshot,
                    user_token=None,
                    page_id=page_id,
                    publish_mode="publish_now",
                    scheduled_publish_time=None,
                    graph_base=self.graph_base,
                    conn=self.conn,
                    opener=opener,
                    media_info={"kind": "text"},
                )

        self.assertEqual(ctx.exception.diagnostics["result"], "credential_retry_failed")
        self.assertEqual(
            store.get_facebook_page_token_row(self.conn, page_id, merchant_id)["status"],
            "reconnect_required",
        )

    def test_queue_facebook_publish_passes_conn_to_publish_snapshot(self):
        snapshot, approval, _ = self.approval_snapshot()
        page_id = str((snapshot.get("connectedChannelRef") or {}).get("providerChannelId"))

        with patch(
            "backend.app.facebook_publisher.publish_approved_snapshot",
            return_value={
                "summary": "published",
                "diagnostics": {"errorClass": "none", "providerResultRef": "post_queue", "postId": "post_queue"},
            },
        ) as publish_snapshot:
            facebook_publisher.queue_facebook_publish(
                self.conn,
                approval["id"],
                {"pageId": page_id, "userAccessToken": "manual-user-token"},
                graph_base=self.graph_base,
            )

        self.assertIs(publish_snapshot.call_args.kwargs["conn"], self.conn)

    def test_retry_facebook_publish_passes_conn_to_publish_snapshot(self):
        snapshot, approval, approval_row = self.approval_snapshot()
        page_id, _ = self.seed_page_token(snapshot, expires_in_seconds=3600)
        job = store.create_publish_job(self.conn, approval_row)
        self.assertIsNotNone(job["id"])

        with patch(
            "backend.app.facebook_publisher.publish_approved_snapshot",
            return_value={
                "summary": "published",
                "diagnostics": {"errorClass": "none", "providerResultRef": "post_retry", "postId": "post_retry"},
            },
        ) as publish_snapshot:
            facebook_publisher.retry_facebook_publish(self.conn, job["id"], graph_base=self.graph_base)

        self.assertIs(publish_snapshot.call_args.kwargs["conn"], self.conn)
