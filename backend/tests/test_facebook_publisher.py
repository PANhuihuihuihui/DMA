import json
import sqlite3
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from urllib import error

from backend.app import facebook_publisher, facebook_token_vault, store


USER_TOKEN = "lp-user-token-should-not-persist"
PAGE_TOKEN = "lp-page-token-should-not-persist"
PAGE_ID = "1243605852158721"


class MockResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class FacebookPublisherTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        facebook_token_vault.clear()
        self.temp_dir.cleanup()

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

    def approve_tiktok(self):
        workflow = store.get_workflow(self.conn)
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == "tiktok")
        creator_info = store.get_tiktok_creator_info(self.conn, draft["connectedChannelId"])
        return store.approve_draft(
            self.conn,
            draft["id"],
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "tiktokConfirmations": {
                    "creatorInfoVersion": creator_info["version"],
                    "privacyLevel": "PUBLIC_TO_EVERYONE",
                    "disclosureReviewed": True,
                    "interactionReviewed": True,
                    "allowComment": True,
                },
            },
        )["approval"]

    def successful_opener(self, req, timeout=15):
        url = req.full_url
        if url.endswith("/me/accounts?fields=id,name,category,link,tasks,access_token&limit=100"):
            self.assertEqual(f"Bearer {USER_TOKEN}", req.headers.get("Authorization"))
            return MockResponse(
                {
                    "data": [
                        {
                            "id": PAGE_ID,
                            "name": "Aurora Heating & Cooling",
                            "access_token": PAGE_TOKEN,
                        }
                    ]
                }
            )
        if url.endswith(f"/{PAGE_ID}/feed"):
            self.assertEqual(f"Bearer {PAGE_TOKEN}", req.headers.get("Authorization"))
            body = req.data.decode("utf-8")
            self.assertIn("message=", body)
            return MockResponse({"id": f"{PAGE_ID}_122105698989358443"})
        if f"/{PAGE_ID}_122105698989358443" in url:
            self.assertEqual(f"Bearer {PAGE_TOKEN}", req.headers.get("Authorization"))
            return MockResponse(
                {
                    "id": f"{PAGE_ID}_122105698989358443",
                    "message": "Published message",
                    "created_time": "2026-06-17T18:12:49+0000",
                    "permalink_url": "https://www.facebook.com/122105699001358443/posts/122105698989358443",
                    "is_published": True,
                }
            )
        self.fail(f"Unexpected Graph URL: {url}")

    def missing_permission_opener(self, req, timeout=15):
        payload = {
            "error": {
                "message": "(#200) Requires pages_manage_posts permission",
                "type": "OAuthException",
                "code": 200,
                "fbtrace_id": "trace-meta",
            }
        }
        raise error.HTTPError(req.full_url, 403, "Forbidden", {}, BytesIO(json.dumps(payload).encode("utf-8")))

    def raw_database_payload(self):
        rows = {}
        for table in ["publish_attempts", "publish_events", "publish_outcomes"]:
            rows[table] = [dict(row) for row in self.conn.execute(f"select * from {table}")]
        return json.dumps(rows, sort_keys=True)

    def assert_tokens_not_persisted(self, payload):
        rendered = json.dumps(payload, sort_keys=True) + self.raw_database_payload()
        self.assertNotIn(USER_TOKEN, rendered)
        self.assertNotIn(PAGE_TOKEN, rendered)

    def test_live_facebook_publish_records_post_id_and_permalink_without_persisting_tokens(self):
        approval = self.approve_facebook()

        payload = facebook_publisher.queue_facebook_publish(
            self.conn,
            approval["id"],
            {"userAccessToken": USER_TOKEN, "pageId": PAGE_ID},
            graph_base="https://graph.facebook.test/v20.0",
            opener=self.successful_opener,
        )

        self.assertEqual("ok", payload["status"])
        self.assertEqual("published", payload["job"]["status"])
        self.assertEqual("facebook", payload["job"]["platform"])
        self.assertEqual(["approved", "queued", "publishing", "published"], [event["status"] for event in payload["job"]["events"]])
        diagnostics = payload["job"]["attempts"][0]["diagnostics"]
        self.assertEqual(f"{PAGE_ID}_122105698989358443", diagnostics["postId"])
        self.assertEqual("https://www.facebook.com/122105699001358443/posts/122105698989358443", diagnostics["permalinkUrl"])
        self.assertEqual("facebook", self.conn.execute("select provider from publish_outcomes").fetchone()["provider"])
        self.assert_tokens_not_persisted(payload)

    def test_live_facebook_publish_uses_connected_page_token_without_user_token(self):
        approval = self.approve_facebook()
        facebook_token_vault.put_page_token(PAGE_ID, PAGE_TOKEN, {"id": PAGE_ID, "name": "Aurora Heating & Cooling"})

        payload = facebook_publisher.queue_facebook_publish(
            self.conn,
            approval["id"],
            {"pageId": PAGE_ID},
            graph_base="https://graph.facebook.test/v20.0",
            opener=self.successful_opener,
        )

        self.assertEqual("ok", payload["status"])
        self.assertEqual("published", payload["job"]["status"])
        diagnostics = payload["job"]["attempts"][0]["diagnostics"]
        self.assertEqual(f"{PAGE_ID}_122105698989358443", diagnostics["postId"])
        self.assert_tokens_not_persisted(payload)

    def test_missing_pages_manage_posts_records_redacted_manual_fallback_attempt(self):
        approval = self.approve_facebook()

        payload = facebook_publisher.queue_facebook_publish(
            self.conn,
            approval["id"],
            {"userAccessToken": USER_TOKEN, "pageId": PAGE_ID},
            graph_base="https://graph.facebook.test/v20.0",
            opener=self.missing_permission_opener,
        )

        self.assertEqual("ok", payload["status"])
        self.assertEqual("manual_fallback_required", payload["job"]["status"])
        diagnostics = payload["job"]["attempts"][0]["diagnostics"]
        self.assertEqual("missing_permission", diagnostics["errorClass"])
        self.assertIn("pages_manage_posts", diagnostics["message"])
        self.assertEqual(
            ["approved", "queued", "publishing", "failed", "manual_fallback_required"],
            [event["status"] for event in payload["job"]["events"]],
        )
        self.assert_tokens_not_persisted(payload)

    def test_non_facebook_approval_cannot_use_live_facebook_publish(self):
        approval = self.approve_tiktok()
        with self.assertRaises(store.StoreError) as raised:
            facebook_publisher.queue_facebook_publish(
                self.conn,
                approval["id"],
                {"userAccessToken": USER_TOKEN, "pageId": PAGE_ID},
                graph_base="https://graph.facebook.test/v20.0",
                opener=self.successful_opener,
            )
        self.assertEqual(409, raised.exception.status)


if __name__ == "__main__":
    unittest.main()
