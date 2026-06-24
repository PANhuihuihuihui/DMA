import tempfile
import unittest
from pathlib import Path

from backend.app import store


class ScheduledPostsTest(unittest.TestCase):
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

    def test_calendar_slots_migrate_without_row_loss(self):
        slot_rows = self.conn.execute(
            "select id, status from calendar_slots order by created_at, id"
        ).fetchall()
        scheduled_rows = self.conn.execute(
            "select id, status from scheduled_posts order by created_at, id"
        ).fetchall()

        self.assertGreaterEqual(len(scheduled_rows), len(slot_rows))
        for slot in slot_rows:
            scheduled = self.conn.execute(
                "select * from scheduled_posts where id = ?",
                (store.scheduled_post_id_for_slot(slot["id"]),),
            ).fetchone()
            self.assertIsNotNone(scheduled)
            expected_status = {
                "scheduled": "queued",
                "in_review": "draft",
                "assisted": "draft",
            }.get(slot["status"], "draft")
            self.assertEqual(expected_status, scheduled["status"])

    def test_scheduled_post_requires_connected_channel_to_queue(self):
        row = self.conn.execute(
            "select * from scheduled_posts order by created_at, id limit 1"
        ).fetchone()
        self.assertIsNotNone(row)

        store.advance_scheduled_post_status(self.conn, row["id"], "approved")
        self.conn.execute(
            "update connected_channels set status = 'disconnected' where id = ?",
            (row["connected_channel_id"],),
        )
        self.conn.commit()

        with self.assertRaises(store.StoreError) as raised:
            store.advance_scheduled_post_status(self.conn, row["id"], "queued")
        self.assertEqual(409, raised.exception.status)

        self.conn.execute(
            "update connected_channels set status = 'connected' where id = ?",
            (row["connected_channel_id"],),
        )
        self.conn.commit()
        updated = store.advance_scheduled_post_status(self.conn, row["id"], "queued")
        self.assertEqual("queued", updated["status"])


if __name__ == "__main__":
    unittest.main()
