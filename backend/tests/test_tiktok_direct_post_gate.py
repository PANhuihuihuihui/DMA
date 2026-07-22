import tempfile
import unittest
from pathlib import Path

from backend.app import store, tiktok_publisher
from backend.tests.tiktok_test_support import install_connected_tiktok, published_api


FULL_ELIGIBILITY = {"appAuditApproved": True, "scopesGranted": True}


class TiktokDirectPostGateTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)
        install_connected_tiktok(self.conn)
        self.api, self.calls = published_api()

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

    def test_direct_post_without_eligibility_falls_back_to_upload(self):
        approval = self.approve_tiktok()
        payload = tiktok_publisher.queue_tiktok_publish(self.conn, approval["id"], {"directPost": True}, api_client=self.api)

        route = payload["route"]
        self.assertEqual("direct_post", route["requestedRoute"])
        self.assertEqual("upload_to_inbox", route["route"])
        self.assertTrue(route["fellBack"])
        self.assertFalse(route["directPost"]["eligible"])
        # App-review and scope eligibility are the blocking reasons.
        self.assertIn("appReviewApproved", route["directPost"]["blockedReasons"])
        self.assertIn("requiredScopesGranted", route["directPost"]["blockedReasons"])

        diagnostics = payload["job"]["attempts"][0]["diagnostics"]
        self.assertEqual("upload_to_inbox", diagnostics["route"])
        self.assertTrue(diagnostics["directPostFellBack"])

    def test_direct_post_allowed_when_all_eligibility_checks_pass(self):
        approval = self.approve_tiktok()
        payload = tiktok_publisher.queue_tiktok_publish(
            self.conn,
            approval["id"],
            {"publishMode": "direct_post", "directPostEligibility": FULL_ELIGIBILITY},
            api_client=self.api,
        )

        route = payload["route"]
        self.assertEqual("direct_post", route["route"])
        self.assertTrue(route["directPost"]["eligible"])
        self.assertEqual([], route["directPost"]["blockedReasons"])
        self.assertEqual("published", payload["job"]["status"])
        self.assertEqual("direct_post", payload["job"]["attempts"][0]["diagnostics"]["deliveryMode"])

    def test_partial_eligibility_still_blocks_direct_post(self):
        approval = self.approve_tiktok()
        payload = tiktok_publisher.queue_tiktok_publish(
            self.conn,
            approval["id"],
            {"directPost": True, "directPostEligibility": {"appAuditApproved": True}},
            api_client=self.api,
        )
        route = payload["route"]
        self.assertEqual("upload_to_inbox", route["route"])
        self.assertIn("requiredScopesGranted", route["directPost"]["blockedReasons"])


if __name__ == "__main__":
    unittest.main()
