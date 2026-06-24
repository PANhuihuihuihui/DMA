import tempfile
import unittest
from pathlib import Path

from backend.app.contracts import serialize_session
from backend.app.sessions import SessionError, create_session, expire_session, resolve_session
from backend.app.store import DEMO_MERCHANT_ID, DEMO_SESSION_ID, DEMO_USER_ID, connect, initialize_database, seed_demo_data


class SessionAuthTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        self.conn = connect(self.db_path)
        initialize_database(self.conn)
        seed_demo_data(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_create_and_resolve_session(self):
        token = create_session(self.conn, DEMO_USER_ID, DEMO_MERCHANT_ID, user_agent="unit-test")
        resolved = resolve_session(self.conn, token)
        self.assertEqual(
            {"user_id": DEMO_USER_ID, "merchant_id": DEMO_MERCHANT_ID},
            resolved,
        )

    def test_seeded_demo_session_resolves_to_demo_tenant(self):
        resolved = resolve_session(self.conn, DEMO_SESSION_ID)
        self.assertEqual(DEMO_USER_ID, resolved["user_id"])
        self.assertEqual(DEMO_MERCHANT_ID, resolved["merchant_id"])

    def test_unknown_session_is_rejected(self):
        with self.assertRaises(SessionError):
            resolve_session(self.conn, "session_missing")

    def test_expired_session_is_marked_and_rejected(self):
        token = create_session(self.conn, DEMO_USER_ID, DEMO_MERCHANT_ID, ttl_seconds=-1)
        with self.assertRaises(SessionError):
            resolve_session(self.conn, token)
        row = self.conn.execute("select * from sessions where id = ?", (token,)).fetchone()
        self.assertEqual("expired", row["status"])

    def test_logged_out_session_is_rejected(self):
        token = create_session(self.conn, DEMO_USER_ID, DEMO_MERCHANT_ID)
        expire_session(self.conn, token)
        with self.assertRaises(SessionError):
            resolve_session(self.conn, token)

    def test_serialize_session_redacts_token(self):
        row = self.conn.execute("select * from sessions where id = ?", (DEMO_SESSION_ID,)).fetchone()
        payload = serialize_session(row)
        self.assertNotIn("id", payload)
        self.assertEqual("authenticated", payload["status"])
        self.assertEqual(DEMO_MERCHANT_ID, payload["merchantId"])


if __name__ == "__main__":
    unittest.main()
