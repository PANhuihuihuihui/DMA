import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app import google_auth, store
from backend.app.store import connect, initialize_database, seed_demo_data


def make_verifier(payload):
    def verifier(credential, client_id):
        return payload
    return verifier


SAMPLE_CLAIMS = {
    "sub": "google_112233",
    "email": "alice@example.com",
    "email_verified": True,
    "name": "Alice Test",
    "iss": "https://accounts.google.com",
}


class VerifyGoogleIdTokenTest(unittest.TestCase):
    def test_valid_token_returns_claims(self):
        result = google_auth.verify_google_id_token(
            "fake_cred",
            verifier=make_verifier(SAMPLE_CLAIMS),
        )
        self.assertEqual(result["sub"], "google_112233")
        self.assertEqual(result["email"], "alice@example.com")
        self.assertTrue(result["email_verified"])
        self.assertEqual(result["name"], "Alice Test")

    def test_invalid_issuer_raises(self):
        bad = {**SAMPLE_CLAIMS, "iss": "https://evil.com"}
        with self.assertRaises(store.StoreError) as ctx:
            google_auth.verify_google_id_token(
                "fake_cred",
                verifier=make_verifier(bad),
            )
        self.assertEqual(ctx.exception.status, 401)

    def test_verifier_exception_raises_401(self):
        def bad_verifier(cred, cid):
            raise ValueError("bad token")

        with self.assertRaises(store.StoreError) as ctx:
            google_auth.verify_google_id_token("bad", verifier=bad_verifier)
        self.assertEqual(ctx.exception.status, 401)

    def test_missing_client_id_and_verifier_raises_500(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(store.StoreError) as ctx:
                google_auth.verify_google_id_token("cred")
            self.assertEqual(ctx.exception.status, 500)


class ResolveOrCreateIdentityTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.sqlite")
        self.conn = connect(self.db_path)
        initialize_database(self.conn)
        seed_demo_data(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_create_new_user(self):
        claims = {"sub": "new_sub_1", "email": "new@example.com", "email_verified": True, "name": "New User"}
        user = google_auth.resolve_or_create_identity(self.conn, claims)
        self.assertEqual(user["email"], "new@example.com")
        self.assertEqual(user["google_sub"], "new_sub_1")
        self.assertEqual(user["role"], "owner")

    def test_existing_google_sub_returns_same_user(self):
        claims = {"sub": "repeat_sub", "email": "a@b.com", "email_verified": True, "name": "A"}
        user1 = google_auth.resolve_or_create_identity(self.conn, claims)
        user2 = google_auth.resolve_or_create_identity(self.conn, claims)
        self.assertEqual(user1["id"], user2["id"])

    def test_link_existing_email_user(self):
        demo_user = self.conn.execute("select * from users where id = ?", (store.DEMO_USER_ID,)).fetchone()
        claims = {
            "sub": "google_karen",
            "email": demo_user["email"],
            "email_verified": True,
            "name": "Karen Li",
        }
        user = google_auth.resolve_or_create_identity(self.conn, claims)
        self.assertEqual(user["id"], store.DEMO_USER_ID)
        self.assertEqual(user["google_sub"], "google_karen")

    def test_unverified_email_creates_new(self):
        claims = {
            "sub": "unverified_sub",
            "email": "karen@example.com",
            "email_verified": False,
            "name": "Imposter",
        }
        user = google_auth.resolve_or_create_identity(self.conn, claims)
        self.assertNotEqual(user["id"], store.DEMO_USER_ID)


class DevLoginEnabledTest(unittest.TestCase):
    def test_enabled_when_dev_flag_set(self):
        with patch.dict(os.environ, {"LOCALPILOT_DEV_LOGIN": "1"}, clear=False):
            env = os.environ.copy()
            env.pop("GOOGLE_CLIENT_ID", None)
            with patch.dict(os.environ, env, clear=True):
                self.assertTrue(google_auth.dev_login_enabled())

    def test_disabled_when_client_id_set(self):
        with patch.dict(os.environ, {"LOCALPILOT_DEV_LOGIN": "1", "GOOGLE_CLIENT_ID": "some_id"}):
            self.assertFalse(google_auth.dev_login_enabled())

    def test_disabled_when_no_flag(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(google_auth.dev_login_enabled())


if __name__ == "__main__":
    unittest.main()
