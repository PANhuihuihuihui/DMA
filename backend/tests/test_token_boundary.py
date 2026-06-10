import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.app.store import connect, initialize_database, seed_demo_data
from backend.app.token_boundary import create_token_boundary, serialize_token_boundary_ref


FORBIDDEN_TERMS = [
    "access" + "_token",
    "refresh" + "_token",
    "author" + "ization",
    "coo" + "kie",
    "client" + "_secret",
    "api" + "_key",
    "oauth" + "_payload",
    "provider" + "_raw",
]


def rendered(payload):
    return json.dumps(payload, sort_keys=True).lower()


class TokenBoundaryContractTest(unittest.TestCase):
    def test_boundary_models_external_secret_reference_and_redacts_public_shape(self):
        boundary = create_token_boundary(
            provider="facebook",
            connected_channel_id="channel-facebook-page",
            secret_ref="localpilot/provider/facebook/channel-facebook-page",
        )

        self.assertEqual("external_secret_ref", boundary["storageMode"])
        self.assertEqual("facebook", boundary["provider"])
        self.assertEqual("channel-facebook-page", boundary["connectedChannelId"])
        self.assertEqual("localpilot/provider/facebook/channel-facebook-page", boundary["secretRef"])
        self.assertIn("rotation", boundary)
        self.assertEqual("active", boundary["rotation"]["status"])

        public_ref = serialize_token_boundary_ref(boundary)
        self.assertEqual(boundary["id"], public_ref["id"])
        self.assertEqual("facebook", public_ref["provider"])
        self.assertEqual("external_secret_ref", public_ref["storageMode"])
        self.assertEqual("redacted", public_ref["visibility"])
        self.assertNotIn("secretRef", public_ref)

        output = rendered(public_ref)
        for term in FORBIDDEN_TERMS:
            self.assertNotIn(term, output)

    def test_seeded_boundaries_store_no_browser_readable_token_material(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "workflow.sqlite")
            conn = connect(db_path)
            try:
                initialize_database(conn)
                seed_demo_data(conn)

                rows = conn.execute(
                    """
                    select provider, connected_channel_id, storage_mode, secret_ref,
                           rotation_status, credential_fingerprint
                    from provider_token_boundaries
                    order by provider
                    """
                ).fetchall()
                self.assertGreaterEqual(len(rows), 2)
                for row in rows:
                    self.assertEqual("external_secret_ref", row["storage_mode"])
                    self.assertTrue(row["secret_ref"].startswith("localpilot/provider/"))
                    self.assertEqual("active", row["rotation_status"])
                    self.assertTrue(row["credential_fingerprint"].startswith("sha256:"))

                columns = {
                    row["name"]
                    for row in conn.execute("pragma table_info(provider_token_boundaries)")
                }
                for term in FORBIDDEN_TERMS:
                    self.assertNotIn(term, columns)

                payload = [dict(row) for row in rows]
                for term in FORBIDDEN_TERMS:
                    self.assertNotIn(term, rendered(payload))
            finally:
                conn.close()

    def test_fake_adapter_contract_uses_only_boundary_references(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "workflow.sqlite")
            conn = connect(db_path)
            try:
                initialize_database(conn)
                seed_demo_data(conn)
                channels = [
                    dict(row)
                    for row in conn.execute(
                        """
                        select id, provider, provider_channel_id, token_boundary_id, status
                        from connected_channels
                        order by provider
                        """
                    )
                ]
            finally:
                conn.close()

        self.assertGreaterEqual(len(channels), 2)
        for channel in channels:
            self.assertIn("token_boundary_id", channel)
            self.assertNotIn("secret_ref", channel)
            self.assertNotIn("credential", rendered(channel))
        for term in FORBIDDEN_TERMS:
            self.assertNotIn(term, rendered(channels))


if __name__ == "__main__":
    unittest.main()
