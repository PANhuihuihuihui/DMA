import tempfile
import unittest
from pathlib import Path

from backend.app import store


def _confirmations(creator_info):
    return {
        "creatorInfoVersion": creator_info["version"],
        "privacyLevel": "PUBLIC_TO_EVERYONE",
        "disclosureReviewed": True,
        "interactionReviewed": True,
        "allowComment": True,
    }


class TiktokCreatorInfoTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        self.conn = store.connect(self.db_path)
        store.initialize_database(self.conn)
        store.seed_demo_data(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def _tiktok_draft(self):
        workflow = store.get_workflow(self.conn)
        return next(item for item in workflow["platformDrafts"] if item["platform"] == "tiktok")

    def test_creator_info_is_persisted_and_versioned(self):
        info = store.get_tiktok_creator_info(self.conn, store.TIKTOK_CHANNEL_ID)
        self.assertEqual(1, info["version"])
        self.assertIn("PUBLIC_TO_EVERYONE", info["privacyLevelOptions"])

        refreshed = store.refresh_tiktok_creator_info(self.conn, store.TIKTOK_CHANNEL_ID)
        self.assertEqual(2, refreshed["version"])

        # Persisted across reads.
        self.assertEqual(2, store.get_tiktok_creator_info(self.conn, store.TIKTOK_CHANNEL_ID)["version"])

    def test_approval_embeds_creator_info_snapshot(self):
        draft = self._tiktok_draft()
        creator_info = store.get_tiktok_creator_info(self.conn, draft["connectedChannelId"])
        approval = store.approve_draft(
            self.conn,
            draft["id"],
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "tiktokConfirmations": _confirmations(creator_info),
            },
        )["approval"]

        snapshot = approval["snapshot"]
        self.assertIn("creatorInfoSnapshot", snapshot)
        self.assertEqual(creator_info["version"], snapshot["creatorInfoSnapshot"]["version"])
        self.assertEqual("PUBLIC_TO_EVERYONE", snapshot["tiktokConfirmations"]["privacyLevel"])

    def test_refresh_does_not_mutate_historical_approval_snapshot(self):
        draft = self._tiktok_draft()
        creator_info = store.get_tiktok_creator_info(self.conn, draft["connectedChannelId"])
        approval = store.approve_draft(
            self.conn,
            draft["id"],
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "tiktokConfirmations": _confirmations(creator_info),
            },
        )["approval"]
        frozen_version = approval["snapshot"]["creatorInfoSnapshot"]["version"]

        store.refresh_tiktok_creator_info(self.conn, draft["connectedChannelId"])

        stored = store.get_approval(self.conn, approval["id"])
        snapshot = store.json_loads(stored["snapshot_json"], {}) if hasattr(store, "json_loads") else None
        # json_loads is imported into store from contracts; fall back if not exposed.
        if snapshot is None:
            from backend.app.contracts import json_loads as _json_loads

            snapshot = _json_loads(stored["snapshot_json"], {})
        self.assertEqual(frozen_version, snapshot["creatorInfoSnapshot"]["version"])
        self.assertNotEqual(
            frozen_version,
            store.get_tiktok_creator_info(self.conn, draft["connectedChannelId"])["version"],
        )


if __name__ == "__main__":
    unittest.main()
