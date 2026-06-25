import tempfile
import unittest
from pathlib import Path

from backend.app import store, tiktok_publisher


class TiktokFailureTaxonomyTest(unittest.TestCase):
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

    def test_each_failure_class_is_recorded_with_retry_disposition(self):
        retryable = {"rate_limit", "platform_transient"}
        for failure_class in (
            "authentication",
            "scope",
            "creator_setting",
            "rate_limit",
            "audit_or_visibility_block",
            "platform_transient",
            "unknown",
        ):
            approval = self.approve_tiktok()
            payload = tiktok_publisher.queue_tiktok_publish(
                self.conn, approval["id"], {"simulateFailure": failure_class}
            )
            job = payload["job"]
            diagnostics = job["attempts"][0]["diagnostics"]
            self.assertEqual(failure_class, diagnostics["errorClass"])
            if failure_class in retryable:
                self.assertEqual("retry_needed", job["status"])
                self.assertEqual("automatic_retry_needed", job["attempts"][0]["retryClassification"])
            else:
                self.assertEqual("manual_fallback_required", job["status"])
                self.assertEqual("manual_review", job["attempts"][0]["retryClassification"])
            # reset for the next class (FK-safe order)
            self.conn.execute("delete from publish_outcomes")
            self.conn.execute("delete from publish_events")
            self.conn.execute("delete from publish_attempts")
            self.conn.execute("update scheduled_posts set approval_id = null, publish_job_id = null")
            self.conn.execute("delete from publish_jobs")
            self.conn.execute("delete from idempotency_keys")
            self.conn.execute("delete from approvals")
            self.conn.execute("update platform_drafts set status = 'draft' where platform = 'tiktok'")
            self.conn.commit()

    def test_classifier_maps_status_codes_to_taxonomy(self):
        self.assertEqual("authentication", tiktok_publisher.classify_tiktok_failure(401))
        self.assertEqual("scope", tiktok_publisher.classify_tiktok_failure(403))
        self.assertEqual("media_validation", tiktok_publisher.classify_tiktok_failure(400))
        self.assertEqual("rate_limit", tiktok_publisher.classify_tiktok_failure(429))
        self.assertEqual("audit_or_visibility_block", tiktok_publisher.classify_tiktok_failure(451))
        self.assertEqual("platform_transient", tiktok_publisher.classify_tiktok_failure(503))
        self.assertEqual("unknown", tiktok_publisher.classify_tiktok_failure(418))

    def test_media_generation_defaults_to_strictest_channel(self):
        policy = store.strictest_channel_media_policy(self.conn)
        self.assertFalse(policy["generateVariants"])
        self.assertEqual("strictest_relevant_channel_first", policy["variantPolicy"])
        # Among enabled channels (facebook, tiktok), TikTok has the strictest caption limit.
        self.assertEqual("tiktok", policy["strictestChannel"])
        self.assertEqual(2200, policy["maxCaptionLength"])
        self.assertEqual(["video"], policy["supportedMedia"])


if __name__ == "__main__":
    unittest.main()
