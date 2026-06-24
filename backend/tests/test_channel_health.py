import json
import tempfile
import unittest
from pathlib import Path

from backend.app import store


class ChannelHealthTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        self.conn = store.connect(self.db_path)
        store.initialize_database(self.conn)
        store.seed_demo_data(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def _channels_by_platform(self, payload):
        return {channel["platform"]: channel for channel in payload["channels"]}

    def test_facebook_and_tiktok_expose_canonical_health_states(self):
        payload = store.get_channel_health(self.conn, store.DEMO_MERCHANT_ID)
        channels = self._channels_by_platform(payload)

        self.assertIn("facebook", channels)
        self.assertIn("tiktok", channels)
        for channel in channels.values():
            self.assertIn(channel["health"], store.CHANNEL_HEALTH_STATES)

        self.assertEqual("connected", channels["tiktok"]["health"])
        self.assertTrue(channels["tiktok"]["canPublish"])
        # Content creation must never be blocked by channel health.
        self.assertTrue(channels["tiktok"]["contentCreationAvailable"])

    def test_each_canonical_state_is_reportable(self):
        for state in ("missing_permission", "expired_token", "review_blocked", "reconnect_required"):
            store.set_channel_health(self.conn, store.DEMO_MERCHANT_ID, store.TIKTOK_CHANNEL_ID, state)
            payload = store.get_channel_health(self.conn, store.DEMO_MERCHANT_ID, platform="tiktok")
            tiktok = payload["channels"][0]
            self.assertEqual(state, tiktok["health"])
            self.assertFalse(tiktok["canPublish"])

        # reconnect_required must survive a round trip through the read API.
        self.assertEqual(
            "reconnect_required",
            store.get_channel_health(self.conn, store.DEMO_MERCHANT_ID, platform="tiktok")["channels"][0]["health"],
        )

    def test_unknown_or_stale_status_is_normalized(self):
        self.conn.execute(
            "update connected_channels set status = ? where id = ?",
            ("some-unexpected-provider-state", store.TIKTOK_CHANNEL_ID),
        )
        self.conn.commit()
        payload = store.get_channel_health(self.conn, store.DEMO_MERCHANT_ID, platform="tiktok")
        self.assertIn(payload["channels"][0]["health"], store.CHANNEL_HEALTH_STATES)

    def test_health_payload_is_merchant_scoped_and_redacts_secrets(self):
        other_merchant = "merchant_other"
        empty = store.get_channel_health(self.conn, other_merchant)
        self.assertEqual([], empty["channels"])

        payload = store.get_channel_health(self.conn, store.DEMO_MERCHANT_ID)
        rendered = json.dumps(payload, sort_keys=True).lower()
        for term in ("access" + "_token", "refresh" + "_token", "client" + "_secret", "secretref"):
            self.assertNotIn(term, rendered)


if __name__ == "__main__":
    unittest.main()
