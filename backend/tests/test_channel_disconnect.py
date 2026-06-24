import tempfile
import unittest
from pathlib import Path

from backend.app import store


class ChannelDisconnectTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        self.conn = store.connect(self.db_path)
        store.initialize_database(self.conn)
        store.seed_demo_data(self.conn)
        store.seed_phase3_data(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_disconnect_marks_channel_disconnected_and_preserves_history(self):
        draft_count_before = self.conn.execute(
            "select count(*) from platform_drafts where connected_channel_id = ?",
            (store.TIKTOK_CHANNEL_ID,),
        ).fetchone()[0]

        result = store.disconnect_channel(self.conn, store.DEMO_MERCHANT_ID, store.TIKTOK_CHANNEL_ID)
        self.assertEqual("disconnected", result["health"])
        self.assertFalse(result["canPublish"])

        # Historical drafts are preserved after disconnect.
        draft_count_after = self.conn.execute(
            "select count(*) from platform_drafts where connected_channel_id = ?",
            (store.TIKTOK_CHANNEL_ID,),
        ).fetchone()[0]
        self.assertEqual(draft_count_before, draft_count_after)

    def test_disconnect_blocks_publish_progression_but_not_content_creation(self):
        store.disconnect_channel(self.conn, store.DEMO_MERCHANT_ID, store.TIKTOK_CHANNEL_ID)

        with self.assertRaises(store.StoreError) as raised:
            store.assert_channel_publishable(self.conn, store.TIKTOK_CHANNEL_ID)
        self.assertEqual(409, raised.exception.status)

        # Content authoring (a new draft version) must still work while disconnected.
        updated = store.update_draft(
            self.conn,
            store.TIKTOK_DRAFT_ID,
            {"caption": "Edited while channel is disconnected.", "body": "Still editable.", "cta": "Call"},
        )
        self.assertEqual("Edited while channel is disconnected.", updated["draft"]["currentVersion"]["caption"])

    def test_scheduled_post_cannot_queue_on_disconnected_channel(self):
        row = self.conn.execute(
            "select * from scheduled_posts where connected_channel_id = ? order by created_at, id limit 1",
            (store.TIKTOK_CHANNEL_ID,),
        ).fetchone()
        if row is None:
            row = self.conn.execute("select * from scheduled_posts order by created_at, id limit 1").fetchone()
        self.assertIsNotNone(row)

        store.advance_scheduled_post_status(self.conn, row["id"], "approved")
        store.disconnect_channel(self.conn, store.DEMO_MERCHANT_ID, row["connected_channel_id"])

        with self.assertRaises(store.StoreError) as raised:
            store.advance_scheduled_post_status(self.conn, row["id"], "queued")
        self.assertEqual(409, raised.exception.status)

    def test_reconnect_restores_publishability(self):
        store.disconnect_channel(self.conn, store.DEMO_MERCHANT_ID, store.TIKTOK_CHANNEL_ID)
        restored = store.set_channel_health(
            self.conn, store.DEMO_MERCHANT_ID, store.TIKTOK_CHANNEL_ID, "connected"
        )
        self.assertEqual("connected", restored["health"])
        self.assertTrue(restored["canPublish"])
        store.assert_channel_publishable(self.conn, store.TIKTOK_CHANNEL_ID)


if __name__ == "__main__":
    unittest.main()
