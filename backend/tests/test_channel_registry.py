import tempfile
import unittest
from pathlib import Path

from backend.app.store import connect, initialize_database, seed_demo_data


class ChannelRegistryTest(unittest.TestCase):
    def test_channel_registry_is_seeded_and_connected_channels_are_extended(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "workflow.sqlite")
            conn = connect(db_path)
            try:
                initialize_database(conn)
                seed_demo_data(conn)

                registry_rows = conn.execute(
                    "select id, status from channel_registry order by id"
                ).fetchall()
                registry = {row["id"]: row["status"] for row in registry_rows}
                self.assertEqual("enabled", registry["facebook"])
                self.assertEqual("enabled", registry["tiktok"])
                self.assertEqual("coming_soon", registry["xiaohongshu"])

                columns = {
                    row["name"]
                    for row in conn.execute("pragma table_info(connected_channels)")
                }
                self.assertIn("channel_registry_id", columns)
                self.assertIn("connected_by_user_id", columns)
                self.assertIn("capabilities_json", columns)

                seeded_channels = conn.execute(
                    """
                    select id, channel_registry_id, connected_by_user_id, capabilities_json
                    from connected_channels
                    order by id
                    """
                ).fetchall()
                self.assertTrue(seeded_channels)
                for row in seeded_channels:
                    self.assertIn(
                        row["channel_registry_id"],
                        {"facebook", "tiktok", "instagram", "google_business"},
                    )
                    self.assertEqual("user_karen", row["connected_by_user_id"])
                    self.assertEqual("{}", row["capabilities_json"])
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
