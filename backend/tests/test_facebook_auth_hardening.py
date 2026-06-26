import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backend.app import auth_provider, facebook_publisher, facebook_token_vault, store
from backend.app.facebook_auth_provider import FacebookAuthProvider
from backend.tests.test_auth_provider import TempDatabaseTestCase


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

    def test_refresh_calls_graph_api_and_persists_new_token(self):
        with self.assertLogs("backend.app.facebook_auth_provider", level="INFO") as logs:
            with patch(
                "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
                return_value={"access_token": "new-page-token", "expires_in": 7200},
            ) as graph_get:
                result = self.provider.refresh(self.conn, self._credential_row(), self.config)

        self.assertEqual(result, {"access_token": "new-page-token", "expires_in": 7200})
        self.assertEqual(
            facebook_token_vault.get_page_token(
                self.page_id,
                conn=self.conn,
                merchant_id=self.merchant_id,
            ),
            "new-page-token",
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

    def test_refresh_propagates_graph_api_failure(self):
        with patch(
            "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
            side_effect=store.StoreError(502, "graph refresh failed"),
        ):
            with self.assertRaises(store.StoreError) as ctx:
                self.provider.refresh(self.conn, self._credential_row(), self.config)

        self.assertEqual(ctx.exception.status, 502)
        self.assertEqual(ctx.exception.message, "graph refresh failed")
        self.assertEqual(
            facebook_token_vault.get_page_token(
                self.page_id,
                conn=self.conn,
                merchant_id=self.merchant_id,
            ),
            self.original_token,
        )

    def test_refresh_handles_missing_expires_in(self):
        with patch(
            "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
            return_value={"access_token": "new-page-token"},
        ):
            result = self.provider.refresh(self.conn, self._credential_row(), self.config)

        self.assertEqual(result, {"access_token": "new-page-token", "expires_in": None})
        self.assertEqual(
            facebook_token_vault.get_page_token(
                self.page_id,
                conn=self.conn,
                merchant_id=self.merchant_id,
            ),
            "new-page-token",
        )
        self.assertIsNone(self._credential_row()["token_expires_at"])

    def test_revoke_calls_delete_and_marks_reconnect(self):
        with patch(
            "backend.app.facebook_auth_provider.facebook_token_vault.mark_reconnect_required",
            wraps=facebook_token_vault.mark_reconnect_required,
        ) as mark_reconnect_required:
            with patch(
                "backend.app.facebook_auth_provider.facebook_oauth.graph_delete",
                return_value={"success": True},
            ) as graph_delete:
                result = self.provider.revoke(self.conn, self._credential_row(), self.config)

        self.assertEqual(result, {"revoked": True})
        called_url = graph_delete.call_args.args[0]
        self.assertIn("/me/permissions?", called_url)
        self.assertIn("access_token=old-page-token", called_url)
        mark_reconnect_required.assert_called_once_with(self.page_id, conn=self.conn)
        self.assertEqual(self._credential_row()["status"], "reconnect_required")

    def test_revoke_propagates_api_failure(self):
        with patch(
            "backend.app.facebook_auth_provider.facebook_token_vault.mark_reconnect_required"
        ) as mark_reconnect_required:
            with patch(
                "backend.app.facebook_auth_provider.facebook_oauth.graph_delete",
                side_effect=store.StoreError(502, "graph revoke failed"),
            ):
                with self.assertRaises(store.StoreError) as ctx:
                    self.provider.revoke(self.conn, self._credential_row(), self.config)

        self.assertEqual(ctx.exception.status, 502)
        self.assertEqual(ctx.exception.message, "graph revoke failed")
        mark_reconnect_required.assert_not_called()
        self.assertEqual(self._credential_row()["status"], "active")


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

    def seed_page_token(self, snapshot, token="stored-page-token", expires_in_seconds=3600):
        merchant_id = snapshot.get("merchantId") or store.DEMO_MERCHANT_ID
        page_id = str((snapshot.get("connectedChannelRef") or {}).get("providerChannelId"))
        expires_at = None if expires_in_seconds is None else self._iso_after(expires_in_seconds)
        facebook_token_vault.put_page_token(
            page_id,
            token,
            conn=self.conn,
            merchant_id=merchant_id,
            connected_channel_id=store.FACEBOOK_CHANNEL_ID,
            expires_at=expires_at,
            issued_at=self._iso_after(-60),
        )
        return page_id, merchant_id

    def publish_success_result(self, post_id):
        return [
            {"id": post_id},
            {
                "permalink_url": f"https://facebook.test/posts/{post_id}",
                "is_published": True,
                "created_time": "2026-01-01T00:00:00+0000",
            },
        ]

    def auth_error(self, page_id, result="provider_error"):
        return facebook_publisher.FacebookProviderError(
            401,
            "Invalid OAuth access token.",
            facebook_publisher.provider_diagnostics(
                "authentication",
                result,
                {"pageId": page_id},
            ),
        )

    def test_publish_uses_get_valid_credential(self):
        snapshot, _, _ = self.approval_snapshot()
        page_id, merchant_id = self.seed_page_token(snapshot, token="stored-page-token", expires_in_seconds=3600)

        with patch(
            "backend.app.facebook_publisher.auth_provider.get_valid_credential",
            wraps=auth_provider.get_valid_credential,
        ) as get_valid_credential:
            with patch(
                "backend.app.facebook_publisher.graph_request",
                side_effect=self.publish_success_result("post_123"),
            ) as graph_request:
                result = facebook_publisher.publish_approved_snapshot(
                    snapshot,
                    user_token=None,
                    page_id=page_id,
                    publish_mode="publish_now",
                    scheduled_publish_time=None,
                    graph_base=self.graph_base,
                    conn=self.conn,
                    media_info={"kind": "text"},
                )

        self.assertEqual(result["postId"], "post_123")
        get_valid_credential.assert_called_once_with(self.conn, page_id, merchant_id)
        self.assertEqual(graph_request.call_args_list[0].args[2], "stored-page-token")
        self.assertEqual(graph_request.call_count, 2)

    def test_publish_refreshes_expired_credential_before_graph_publish(self):
        snapshot, _, _ = self.approval_snapshot()
        page_id, merchant_id = self.seed_page_token(snapshot, token="expired-page-token", expires_in_seconds=-30)

        with patch(
            "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
            return_value={"access_token": "refreshed-page-token", "expires_in": 7200},
        ) as graph_get:
            with patch(
                "backend.app.facebook_publisher.graph_request",
                side_effect=self.publish_success_result("post_refresh"),
            ) as graph_request:
                result = facebook_publisher.publish_approved_snapshot(
                    snapshot,
                    user_token=None,
                    page_id=page_id,
                    publish_mode="publish_now",
                    scheduled_publish_time=None,
                    graph_base=self.graph_base,
                    conn=self.conn,
                    media_info={"kind": "text"},
                )

        self.assertEqual(result["postId"], "post_refresh")
        self.assertEqual(graph_get.call_count, 1)
        self.assertEqual(
            [call.args[2] for call in graph_request.call_args_list],
            ["refreshed-page-token", "refreshed-page-token"],
        )
        self.assertEqual(
            facebook_token_vault.get_page_token(page_id, conn=self.conn, merchant_id=merchant_id),
            "refreshed-page-token",
        )

    def test_publish_retries_with_refreshed_credential(self):
        snapshot, _, _ = self.approval_snapshot()
        page_id, merchant_id = self.seed_page_token(snapshot, token="stored-page-token", expires_in_seconds=3600)
        original_refresh = FacebookAuthProvider.refresh

        graph_responses = [
            self.auth_error(page_id),
            {"id": "post_retry"},
            {
                "permalink_url": "https://facebook.test/posts/post_retry",
                "is_published": True,
                "created_time": "2026-01-01T00:00:00+0000",
            },
        ]

        def graph_request_side_effect(*args, **kwargs):
            response = graph_responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        with self.assertLogs("backend.app.facebook_publisher", level="WARNING") as logs:
            with patch(
                "backend.app.facebook_publisher.FacebookAuthProvider.refresh",
                autospec=True,
                side_effect=original_refresh,
            ) as refresh:
                with patch(
                    "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
                    return_value={"access_token": "refreshed-page-token", "expires_in": 7200},
                ):
                    with patch(
                        "backend.app.facebook_publisher.graph_request",
                        side_effect=graph_request_side_effect,
                    ) as graph_request:
                        result = facebook_publisher.publish_approved_snapshot(
                            snapshot,
                            user_token=None,
                            page_id=page_id,
                            publish_mode="publish_now",
                            scheduled_publish_time=None,
                            graph_base=self.graph_base,
                            conn=self.conn,
                            media_info={"kind": "text"},
                        )

        self.assertEqual(result["postId"], "post_retry")
        self.assertEqual(
            [call.args[2] for call in graph_request.call_args_list],
            ["stored-page-token", "refreshed-page-token", "refreshed-page-token"],
        )
        refresh.assert_called_once()
        self.assertTrue(
            any(
                f"facebook_publish_auth_retry merchant_id={merchant_id} page_id={page_id}" in line
                for line in logs.output
            )
        )

    def test_publish_marks_reconnect_on_persistent_auth_failure(self):
        snapshot, _, _ = self.approval_snapshot()
        page_id, merchant_id = self.seed_page_token(snapshot, token="stored-page-token", expires_in_seconds=3600)
        original_refresh = FacebookAuthProvider.refresh

        graph_responses = [self.auth_error(page_id), self.auth_error(page_id)]

        def graph_request_side_effect(*args, **kwargs):
            response = graph_responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        with patch(
            "backend.app.facebook_publisher.FacebookAuthProvider.refresh",
            autospec=True,
            side_effect=original_refresh,
        ) as refresh:
            with patch(
                "backend.app.facebook_auth_provider.facebook_oauth.graph_get",
                return_value={"access_token": "refreshed-page-token", "expires_in": 7200},
            ):
                with patch(
                    "backend.app.facebook_publisher.graph_request",
                    side_effect=graph_request_side_effect,
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
                            media_info={"kind": "text"},
                        )

        self.assertEqual(ctx.exception.status, 403)
        self.assertEqual(ctx.exception.diagnostics["result"], "credential_retry_failed")
        self.assertEqual(
            store.get_facebook_page_token_row(self.conn, page_id, merchant_id)["status"],
            "reconnect_required",
        )
        refresh.assert_called_once()

    def test_publish_with_user_token_bypasses_credential_check(self):
        snapshot, _, _ = self.approval_snapshot()
        page_id = str((snapshot.get("connectedChannelRef") or {}).get("providerChannelId"))
        expected_result = {
            "postId": "post_user_token",
            "permalinkUrl": "https://facebook.test/posts/post_user_token",
            "scheduledPublishTime": None,
            "status": "published",
            "summary": "Facebook Page post published through the official Graph API.",
            "diagnostics": {"providerResultRef": "post_user_token"},
        }

        with patch(
            "backend.app.facebook_publisher.auth_provider.get_valid_credential"
        ) as get_valid_credential:
            with patch(
                "backend.app.facebook_publisher.resolve_page_access_token",
                return_value="user-page-token",
            ) as resolve_page_access_token:
                with patch(
                    "backend.app.facebook_publisher._publish_snapshot_with_token",
                    return_value=expected_result,
                ) as publish_with_token:
                    result = facebook_publisher.publish_approved_snapshot(
                        snapshot,
                        user_token="user-access-token",
                        page_id=page_id,
                        publish_mode="publish_now",
                        scheduled_publish_time=None,
                        graph_base=self.graph_base,
                        conn=self.conn,
                        media_info={"kind": "text"},
                    )

        self.assertEqual(result, expected_result)
        get_valid_credential.assert_not_called()
        resolve_page_access_token.assert_called_once_with(
            "user-access-token",
            page_id,
            self.graph_base,
            opener=None,
        )
        publish_with_token.assert_called_once_with(
            snapshot,
            page_id,
            "publish_now",
            None,
            self.graph_base,
            "user-page-token",
            opener=None,
            media_info={"kind": "text"},
        )
