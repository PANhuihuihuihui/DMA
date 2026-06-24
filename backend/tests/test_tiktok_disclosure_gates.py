import tempfile
import unittest
from pathlib import Path

from backend.app import store


class TiktokDisclosureGateTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        self.conn = store.connect(self.db_path)
        store.initialize_database(self.conn)
        store.seed_demo_data(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def _draft(self, platform):
        workflow = store.get_workflow(self.conn)
        return next(item for item in workflow["platformDrafts"] if item["platform"] == platform)

    def _approve_tiktok(self, confirmations):
        draft = self._draft("tiktok")
        return store.approve_draft(
            self.conn,
            draft["id"],
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "tiktokConfirmations": confirmations,
            },
        )

    def _valid_confirmations(self):
        info = store.get_tiktok_creator_info(self.conn, store.TIKTOK_CHANNEL_ID)
        return {
            "creatorInfoVersion": info["version"],
            "privacyLevel": "PUBLIC_TO_EVERYONE",
            "disclosureReviewed": True,
            "interactionReviewed": True,
            "allowComment": True,
        }

    def test_tiktok_approval_requires_disclosure_confirmations(self):
        draft = self._draft("tiktok")
        with self.assertRaises(store.StoreError) as raised:
            store.approve_draft(
                self.conn,
                draft["id"],
                {
                    "draftVersionId": draft["currentVersion"]["id"],
                    "confirmation": "APPROVE_EXACT_VERSION",
                    "approver": {"name": "Karen Li", "email": "karen@example.com"},
                },
            )
        self.assertEqual(400, raised.exception.status)

    def test_missing_disclosure_flag_is_rejected(self):
        confirmations = self._valid_confirmations()
        del confirmations["disclosureReviewed"]
        with self.assertRaises(store.StoreError) as raised:
            self._approve_tiktok(confirmations)
        self.assertEqual(400, raised.exception.status)

    def test_invalid_privacy_level_is_rejected(self):
        confirmations = self._valid_confirmations()
        confirmations["privacyLevel"] = "NOT_A_REAL_LEVEL"
        with self.assertRaises(store.StoreError) as raised:
            self._approve_tiktok(confirmations)
        self.assertEqual(400, raised.exception.status)

    def test_stale_creator_info_version_is_rejected(self):
        confirmations = self._valid_confirmations()
        store.refresh_tiktok_creator_info(self.conn, store.TIKTOK_CHANNEL_ID)
        with self.assertRaises(store.StoreError) as raised:
            self._approve_tiktok(confirmations)
        self.assertEqual(409, raised.exception.status)

    def test_valid_confirmations_approve_and_facebook_unchanged(self):
        approval = self._approve_tiktok(self._valid_confirmations())["approval"]
        self.assertEqual("approved", approval["status"])
        self.assertTrue(approval["snapshot"]["tiktokConfirmations"]["disclosureReviewed"])

        # Facebook approval still works without any TikTok confirmations.
        fb_draft = self._draft("facebook")
        fb_approval = store.approve_draft(
            self.conn,
            fb_draft["id"],
            {
                "draftVersionId": fb_draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
            },
        )["approval"]
        self.assertEqual("approved", fb_approval["status"])
        self.assertNotIn("tiktokConfirmations", fb_approval["snapshot"])


if __name__ == "__main__":
    unittest.main()
