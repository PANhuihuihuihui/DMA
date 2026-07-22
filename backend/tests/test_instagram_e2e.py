import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib import request
from urllib.parse import parse_qs, urlparse

from backend.app import instagram_oauth, store, token_crypto
from backend.app.instagram_publisher import queue_instagram_publish
from backend.tests.test_fake_publish_lifecycle import ApiCase, assert_no_forbidden_terms


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Response:
    def __init__(self, payload=None, headers=None):
        self.payload = payload or {}
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class InstagramAssemblyTest(ApiCase):
    secret_values = [
        "callback-code-private",
        "short-token-private",
        "long-token-private",
        "fresh-token-private",
        "ig-secret-private",
        "signature=private",
    ]

    def setUp(self):
        super().setUp()
        self.key = token_crypto.generate_dev_key()
        self.oauth_calls = []
        self.graph_calls = []
        self.polls = {}
        self.config = {
            "appId": "ig-app",
            "appSecret": "ig-secret-private",
            "redirectUri": "http://127.0.0.1:8787/api/v1/instagram/oauth/callback",
            "returnUrl": "http://127.0.0.1:5173/app",
            "authorizeBase": "https://instagram.test/oauth/authorize",
            "tokenUrl": "https://instagram.test/oauth/access_token",
            "graphBase": "https://graph.test",
            "httpTransport": self.oauth_transport,
        }
        self.env = patch.dict(os.environ, {"LOCALPILOT_TOKEN_KEY": self.key}, clear=False)
        self.config_patch = patch.object(instagram_oauth, "oauth_config", return_value=self.config)
        self.env.start()
        self.config_patch.start()

    def tearDown(self):
        self.config_patch.stop()
        self.env.stop()
        super().tearDown()

    def oauth_transport(self, *, method, url, data):
        self.oauth_calls.append((method, url))
        if method == "POST":
            return {"access_token": "short-token-private"}
        if "ig_exchange_token" in url:
            return {"access_token": "long-token-private", "expires_in": 5183944}
        if "refresh_access_token" in url:
            return {"access_token": "fresh-token-private", "expires_in": 7200}
        if "/me?" in url:
            return {"id": "ig-123", "username": "aurora", "account_type": "BUSINESS"}
        raise AssertionError(f"unexpected OAuth request: {method} {url}")

    def request_redirect(self, path):
        opener = request.build_opener(NoRedirect())
        with self.assertRaises(Exception) as raised:
            opener.open(f"{self.base_url}{path}", timeout=5)
        return raised.exception.headers["Location"]

    def graph_opener(self, req, timeout=15):
        self.graph_calls.append((req.method, req.full_url))
        if req.method == "HEAD":
            return Response(headers={"Content-Type": "image/jpeg", "Content-Length": "120"})
        if req.method == "POST" and req.full_url.endswith("/media"):
            return Response({"id": f"container-{sum('/media' in url for _, url in self.graph_calls)}"})
        if req.method == "GET":
            container = req.full_url.split("?")[0].rsplit("/", 1)[-1]
            self.polls[container] = self.polls.get(container, 0) + 1
            return Response({"status_code": "IN_PROGRESS" if self.polls[container] == 1 else "FINISHED"})
        if req.method == "POST" and req.full_url.endswith("/media_publish"):
            return Response({"id": "media-published-1"})
        self.fail(req.full_url)

    def prepare_instagram_draft(self):
        workflow = self.get_json("/api/v1/workflow")
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == "facebook")
        with store.connect(self.db_path) as conn:
            conn.execute(
                "update platform_drafts set platform = ?, connected_channel_id = ? where id = ?",
                ("instagram", store.INSTAGRAM_CHANNEL_ID, draft["id"]),
            )
            conn.execute(
                """update draft_versions
                   set platform = ?, caption = ?, body = ?, cta = ? where id = ?""",
                ("instagram", "A locally approved offer.", "Schedule today.", "Book now", draft["currentVersion"]["id"]),
            )
            conn.commit()
        return draft["id"], draft["currentVersion"]["id"]

    def approve(self, draft_id, version_id):
        return self.send_json("POST", f"/api/v1/drafts/{draft_id}/approve", {
            "draftVersionId": version_id,
            "confirmation": "APPROVE_EXACT_VERSION",
            "approver": {"name": "Karen Li", "email": "karen@example.com"},
        })["approval"]

    def expand_approval_to_carousel(self, approval_id):
        with store.connect(self.db_path) as conn:
            approval = store.get_approval(conn, approval_id)
            snapshot = json.loads(approval["snapshot_json"])
            snapshot["mediaRefs"] = [
                {"kind": "image", "url": f"https://cdn.example.test/{index}.jpg?signature=private"}
                for index in range(10)
            ]
            conn.execute("update approvals set snapshot_json = ? where id = ?", (json.dumps(snapshot), approval_id))
            conn.commit()

    def assert_redacted(self, payload):
        rendered = json.dumps(payload, sort_keys=True).lower()
        assert_no_forbidden_terms(self, "instagram assembly", payload)
        for value in self.secret_values:
            self.assertNotIn(value, rendered)
        self.assertNotIn("signature", rendered)

    def test_redirect_store_approve_and_publish_ten_image_carousel(self):
        start = self.request_redirect("/api/v1/instagram/oauth/start")
        state = parse_qs(urlparse(start).query)["state"][0]
        callback = self.request_redirect(
            f"/api/v1/instagram/oauth/callback?state={state}&code=callback-code-private"
        )
        self.assertEqual(["1"], parse_qs(urlparse(callback).query)["instagramConnected"])
        replay = self.request_redirect(
            f"/api/v1/instagram/oauth/callback?state={state}&code=callback-code-private"
        )
        replay_query = parse_qs(urlparse(replay).query)
        self.assertEqual(["1"], replay_query.get("instagramDenied") or replay_query.get("instagramReconnect"))
        self.assertNotIn("callback-code-private", replay)

        status = self.get_json("/api/v1/instagram/connection")
        self.assertEqual("ig-123", status["connectedAccounts"][0]["accountId"])
        self.assert_redacted(status)
        with store.connect(self.db_path) as conn:
            row = store.get_instagram_account_token_row(conn, "ig-123")
            self.assertNotIn(b"long-token-private", row["ciphertext"])
            conn.execute(
                "update instagram_account_tokens set token_expires_at = ? where account_id = ?",
                ((datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat().replace("+00:00", "Z"), "ig-123"),
            )
            conn.commit()

        draft_id, version_id = self.prepare_instagram_draft()
        self.assert_http_error("POST", "/api/v1/approvals/not-approved/publish-instagram", {"igUserId": "ig-123"}, {400, 404, 409})
        approval = self.approve(draft_id, version_id)
        self.expand_approval_to_carousel(approval["id"])

        def queue_with_local_transport(conn, approval_id, payload):
            return queue_instagram_publish(
                conn, approval_id, payload, opener=self.graph_opener,
                graph_base="https://graph.test", sleep=lambda _: None,
                poll_interval=0,
            )

        with patch("backend.app.server.instagram_publisher.queue_instagram_publish", side_effect=queue_with_local_transport):
            published = self.send_json("POST", f"/api/v1/approvals/{approval['id']}/publish-instagram", {"igUserId": "ig-123"})
        job = published["job"]
        self.assertEqual("published", job["status"])
        self.assertEqual(["approved", "queued", "publishing", "published"], [event["status"] for event in job["events"]])
        diagnostics = job["attempts"][0]["diagnostics"]
        self.assertEqual("media-published-1", diagnostics["providerResultRef"])
        self.assertEqual(10, len(diagnostics["childContainerIds"]))
        self.assertEqual(2, diagnostics["pollAttempts"])
        self.assertLessEqual(sum(method == "GET" for method, _ in self.graph_calls), 22)
        self.assertTrue(any("refresh_access_token" in url for _, url in self.oauth_calls))
        self.assert_redacted(published)
        self.assert_redacted(self.get_json(f"/api/v1/publish-jobs/{job['id']}"))

    def test_terminal_container_failure_is_a_sanitized_failed_job(self):
        start = self.request_redirect("/api/v1/instagram/oauth/start")
        state = parse_qs(urlparse(start).query)["state"][0]
        self.request_redirect(f"/api/v1/instagram/oauth/callback?state={state}&code=callback-code-private")
        draft_id, version_id = self.prepare_instagram_draft()
        approval = self.approve(draft_id, version_id)
        self.expand_approval_to_carousel(approval["id"])

        def terminal_opener(req, timeout=15):
            if req.method == "HEAD":
                return Response(headers={"Content-Type": "image/jpeg", "Content-Length": "120"})
            if req.method == "POST" and req.full_url.endswith("/media"):
                return Response({"id": "terminal-container"})
            if req.method == "GET":
                return Response({"status_code": "ERROR"})
            self.fail(req.full_url)

        with patch("backend.app.server.instagram_publisher.queue_instagram_publish", side_effect=lambda conn, approval_id, payload: queue_instagram_publish(conn, approval_id, payload, opener=terminal_opener, graph_base="https://graph.test", sleep=lambda _: None, poll_interval=0)):
            failed = self.send_json("POST", f"/api/v1/approvals/{approval['id']}/publish-instagram", {"igUserId": "ig-123"})
        job = failed["job"]
        self.assertEqual("manual_fallback_required", job["status"])
        self.assertEqual("container_terminal_failure", job["attempts"][0]["diagnostics"]["result"])
        self.assertEqual(
            ["approved", "queued", "publishing", "failed", "manual_fallback_required"],
            [event["status"] for event in job["events"]],
        )
        self.assert_redacted(failed)
        self.assert_redacted(self.get_json(f"/api/v1/publish-jobs/{job['id']}"))


if __name__ == "__main__":
    unittest.main()
