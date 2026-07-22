import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib import request
from urllib.parse import parse_qs, urlparse

from backend.app import store, tiktok_oauth, token_crypto
from backend.app.tiktok_content_api import TikTokContentApi
from backend.app.tiktok_publisher import queue_tiktok_publish, refresh_creator_info
from backend.tests.test_fake_publish_lifecycle import ApiCase, assert_no_forbidden_terms


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class TikTokAssemblyTest(ApiCase):
    secret_values = [
        "callback-code-private", "access-private", "refresh-private", "rotated-access-private",
        "rotated-refresh-private", "tt-client-secret", "pkce-private", "signature=private",
    ]

    def setUp(self):
        super().setUp()
        self.key = token_crypto.generate_dev_key()
        self.oauth_calls = []
        self.content_calls = []
        self.status = "PUBLISH_COMPLETE"
        self.fail_next_creator_auth = False
        self.config = {
            "clientKey": "tt-client-key", "clientSecret": "tt-client-secret",
            "redirectUri": "http://127.0.0.1:8787/api/v1/tiktok/oauth/callback",
            "returnUrl": "http://127.0.0.1:5173/app",
            "authorizeBase": "https://tiktok.test/v2/auth/authorize/",
            "tokenUrl": "https://tiktok.test/v2/oauth/token/", "apiBase": "https://open.tiktok.test",
            "httpTransport": self.oauth_transport,
        }
        self.env = patch.dict(os.environ, {"LOCALPILOT_TOKEN_KEY": self.key}, clear=False)
        self.config_patch = patch.object(tiktok_oauth, "oauth_config", return_value=self.config)
        self.env.start()
        self.config_patch.start()

    def tearDown(self):
        self.config_patch.stop()
        self.env.stop()
        super().tearDown()

    def oauth_transport(self, *, method, url, data=None, headers=None):
        self.oauth_calls.append({"method": method, "url": url, "data": data or {}, "headers": headers or {}})
        if (data or {}).get("grant_type") == "refresh_token":
            return {"access_token": "rotated-access-private", "refresh_token": "rotated-refresh-private", "expires_in": 7200, "refresh_expires_in": 86400}
        if method == "POST":
            self.assertEqual("authorization_code", data["grant_type"])
            self.assertTrue(data["code_verifier"])
            return {"access_token": "access-private", "refresh_token": "refresh-private", "expires_in": 7200, "refresh_expires_in": 86400}
        if "/v2/user/info/" in url:
            return {"data": {"user": {"open_id": "tt-assembly", "display_name": "Aurora HVAC"}}}
        raise AssertionError(f"unexpected OAuth request {method} {url}")

    def content_transport(self, **kwargs):
        self.content_calls.append(kwargs)
        if kwargs["url"].endswith("creator_info/query/"):
            if self.fail_next_creator_auth:
                self.fail_next_creator_auth = False
                return {"data": {}, "error": {"code": "access_token_expired"}}
            return {"data": {"creator_nickname": "Aurora", "privacy_level_options": ["PUBLIC_TO_EVERYONE"], "max_video_post_duration_sec": 180}, "error": {"code": "ok"}}
        if kwargs["url"].endswith("status/fetch/"):
            return {"data": {"status": self.status}, "error": {"code": "ok"}}
        return {"data": {"publish_id": "provider-publish-assembly"}, "error": {"code": "ok"}}

    def request_redirect(self, path):
        opener = request.build_opener(NoRedirect())
        with self.assertRaises(Exception) as raised:
            opener.open(f"{self.base_url}{path}", timeout=5)
        return raised.exception.headers["Location"]

    def api(self):
        return TikTokContentApi(transport=self.content_transport, api_base=self.config["apiBase"])

    def assert_redacted(self, payload):
        rendered = json.dumps(payload, sort_keys=True).lower()
        assert_no_forbidden_terms(self, "tiktok assembly", payload)
        for value in self.secret_values:
            self.assertNotIn(value, rendered)
        self.assertNotIn("signature", rendered)

    def connect(self):
        start = self.request_redirect("/api/v1/tiktok/oauth/start?returnTo=https://evil.test/steal")
        query = parse_qs(urlparse(start).query)
        self.assertEqual("S256", query["code_challenge_method"][0])
        self.assertNotIn("tt-client-secret", start)
        state = query["state"][0]
        callback = self.request_redirect(f"/api/v1/tiktok/oauth/callback?state={state}&code=callback-code-private")
        self.assertEqual(["1"], parse_qs(urlparse(callback).query)["tiktokConnected"])
        self.assertNotIn("evil.test", callback)
        self.assertNotIn("callback-code-private", callback)
        return state

    def prepare_approved_tiktok(self):
        workflow = self.get_json("/api/v1/workflow")
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == "tiktok")
        with store.connect(self.db_path) as conn:
            conn.execute("update draft_versions set caption = ? where id = ?", ("A local approved offer.", draft["currentVersion"]["id"]))
            conn.commit()
        creator = self.get_json("/api/v1/tiktok/creator-info")["creatorInfo"]
        approval = self.send_json("POST", f"/api/v1/drafts/{draft['id']}/approve", {
            "draftVersionId": draft["currentVersion"]["id"], "confirmation": "APPROVE_EXACT_VERSION",
            "approver": {"name": "Karen Li", "email": "karen@example.com"},
            "tiktokConfirmations": {"creatorInfoVersion": creator["version"], "privacyLevel": "PUBLIC_TO_EVERYONE", "disclosureReviewed": True, "interactionReviewed": True, "allowComment": True},
        })["approval"]
        with store.connect(self.db_path) as conn:
            snapshot = json.loads(store.get_approval(conn, approval["id"])["snapshot_json"])
            snapshot["mediaRefs"] = [{"kind": "video", "storageRef": "media-assembly", "mimeType": "video/mp4", "sizeBytes": 4096}]
            snapshot["providerPayloadSummary"] = {"durationSeconds": 12}
            conn.execute("update approvals set snapshot_json = ? where id = ?", (json.dumps(snapshot), approval["id"]))
            conn.commit()
        return approval

    def publish(self, approval_id, body=None):
        def queue(conn, requested_approval, payload):
            return queue_tiktok_publish(conn, requested_approval, payload, api_client=self.api())
        with patch("backend.app.server.tiktok_publisher.queue_tiktok_publish", side_effect=queue):
            return self.send_json("POST", f"/api/v1/approvals/{approval_id}/publish-tiktok", body or {})

    def test_redirect_store_approval_refresh_publish_and_redaction(self):
        state = self.connect()
        replay = self.request_redirect(f"/api/v1/tiktok/oauth/callback?state={state}&code=callback-code-private")
        self.assertTrue(parse_qs(urlparse(replay).query).get("tiktokDenied") or parse_qs(urlparse(replay).query).get("tiktokReconnect"))
        self.assertNotIn("callback-code-private", replay)
        self.assertEqual(1, sum(call["data"].get("grant_type") == "authorization_code" for call in self.oauth_calls))
        self.assertTrue(all(call["data"].get("code_verifier") for call in self.oauth_calls if call["data"].get("grant_type") == "authorization_code"))

        status = self.get_json("/api/v1/tiktok/connection")
        self.assertIn("tt-assembly", [account["accountId"] for account in status["connectedAccounts"]])
        self.assert_redacted(status)
        with store.connect(self.db_path) as conn:
            row = store.get_tiktok_account_token_row(conn, "tt-assembly")
            self.assertNotIn(b"access-private", row["ciphertext"])
            self.assertNotIn(b"refresh-private", row["ciphertext"])
            self.fail_next_creator_auth = True
            refresh_creator_info(conn, store.TIKTOK_CHANNEL_ID, api_client=self.api())
            refreshed = store.get_tiktok_account_token_row(conn, "tt-assembly")
            self.assertNotIn(b"rotated-access-private", refreshed["ciphertext"])
            self.assertNotIn(b"rotated-refresh-private", refreshed["ciphertext"])
            conn.commit()
        self.assertTrue(any(call["data"].get("grant_type") == "refresh_token" for call in self.oauth_calls))
        approval = self.prepare_approved_tiktok()
        published = self.publish(approval["id"], {"publishMode": "direct_post", "directPostEligibility": {"appAuditApproved": True, "scopesGranted": True}})
        job = published["job"]
        self.assertEqual("published", job["status"])
        self.assertEqual("provider-publish-assembly", job["attempts"][0]["diagnostics"]["publishId"])
        self.assertEqual(["approved", "queued", "publishing", "published"], [event["status"] for event in job["events"]])
        self.assertTrue(any(call["url"].endswith("/v2/post/publish/video/init/") for call in self.content_calls))
        self.assert_redacted(published)
        self.assert_redacted(self.get_json(f"/api/v1/publish-jobs/{job['id']}"))

        resumed = self.publish(approval["id"], {"publishMode": "direct_post", "directPostEligibility": {"appAuditApproved": True, "scopesGranted": True}})
        self.assertEqual(job["id"], resumed["job"]["id"])
        self.assertEqual(1, sum(not call["url"].endswith("status/fetch/") and not call["url"].endswith("creator_info/query/") for call in self.content_calls))

    def test_pending_and_terminal_failure_remain_truthful_and_redacted(self):
        self.connect()
        approval = self.prepare_approved_tiktok()
        self.status = "PROCESSING"
        pending = self.publish(approval["id"])
        self.assertEqual("pending", pending["job"]["status"])
        self.assertEqual("pending", pending["job"]["attempts"][0]["status"])
        self.assert_redacted(pending)
        self.status = "FAILED"
        resumed = self.publish(approval["id"])
        self.assertEqual("failed", resumed["job"]["status"])
        self.assertEqual("provider-publish-assembly", resumed["job"]["attempts"][0]["diagnostics"]["publishId"])
        self.assert_redacted(resumed)

    def test_direct_post_without_approval_gates_falls_back_to_inbox(self):
        self.connect()
        approval = self.prepare_approved_tiktok()
        payload = self.publish(approval["id"], {"publishMode": "direct_post"})
        self.assertEqual("upload_to_inbox", payload["route"]["route"])
        self.assertTrue(payload["route"]["fellBack"])
        self.assertTrue(any(call["url"].endswith("/v2/post/publish/inbox/video/init/") for call in self.content_calls))
        self.assert_redacted(payload)


if __name__ == "__main__":
    unittest.main()
