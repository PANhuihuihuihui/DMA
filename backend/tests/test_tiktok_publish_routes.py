import json
import tempfile
import unittest
from pathlib import Path

from backend.app import store, tiktok_publisher


class TiktokPublishRoutesTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def approve_tiktok(self):
        workflow = store.get_workflow(self.conn)
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == "tiktok")
        info = store.get_tiktok_creator_info(self.conn, draft["connectedChannelId"])
        return store.approve_draft(
            self.conn,
            draft["id"],
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "tiktokConfirmations": {
                    "creatorInfoVersion": info["version"],
                    "privacyLevel": "PUBLIC_TO_EVERYONE",
                    "disclosureReviewed": True,
                    "interactionReviewed": True,
                    "allowComment": True,
                },
            },
        )["approval"]

    def test_default_route_is_upload_to_inbox_with_full_lifecycle(self):
        approval = self.approve_tiktok()
        payload = tiktok_publisher.queue_tiktok_publish(self.conn, approval["id"], {})

        self.assertEqual("ok", payload["status"])
        self.assertEqual("Send to TikTok", payload["ctaCopy"])
        job = payload["job"]
        self.assertEqual("published", job["status"])
        self.assertEqual("tiktok", job["platform"])
        self.assertEqual(
            ["approved", "queued", "publishing", "published"],
            [event["status"] for event in job["events"]],
        )

        diagnostics = job["attempts"][0]["diagnostics"]
        self.assertEqual("upload_to_inbox", diagnostics["route"])
        self.assertEqual("upload_to_inbox", diagnostics["deliveryMode"])
        self.assertTrue(diagnostics["publishId"].startswith("tiktok:upload_to_inbox:"))

        outcome = self.conn.execute("select provider from publish_outcomes").fetchone()
        self.assertEqual("tiktok", outcome["provider"])

    def test_route_choice_is_recorded_per_attempt_and_secret_free(self):
        approval = self.approve_tiktok()
        payload = tiktok_publisher.queue_tiktok_publish(
            self.conn, approval["id"], {"publishMode": "upload_to_inbox"}
        )
        self.assertEqual("upload_to_inbox", payload["route"]["route"])

        rendered = json.dumps(payload, sort_keys=True).lower()
        for term in ("access" + "_token", "refresh" + "_token", "client" + "_secret"):
            self.assertNotIn(term, rendered)

    def test_publish_blocked_when_channel_disconnected(self):
        approval = self.approve_tiktok()
        store.disconnect_channel(self.conn, store.DEMO_MERCHANT_ID, store.TIKTOK_CHANNEL_ID)
        with self.assertRaises(store.StoreError) as raised:
            tiktok_publisher.queue_tiktok_publish(self.conn, approval["id"], {})
        self.assertEqual(409, raised.exception.status)


if __name__ == "__main__":
    unittest.main()
