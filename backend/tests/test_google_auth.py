import json
import os
import tempfile
import threading
import unittest
from http.cookiejar import CookieJar
from pathlib import Path
from unittest.mock import patch
from urllib import error, request

from backend.app import google_auth, sessions, store
from backend.app.server import create_app
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


class AuthEndpointTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.sqlite")
        self.server = create_app(host="127.0.0.1", port=0, db_path=self.db_path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"
        self.cookie_jar = CookieJar()
        self.opener = request.build_opener(request.HTTPCookieProcessor(self.cookie_jar))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def _request(self, method, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json"}
        if data:
            headers["Content-Type"] = "application/json"
        req = request.Request(f"{self.base_url}{path}", data=data, method=method, headers=headers)
        resp = self.opener.open(req, timeout=5)
        return json.loads(resp.read().decode("utf-8")), resp

    def _session_cookie(self):
        for c in self.cookie_jar:
            if c.name == "lp_session":
                return c.value
        return None

    @patch.dict(os.environ, {"LOCALPILOT_DEV_LOGIN": "1"}, clear=False)
    def test_dev_login_sets_cookie_and_returns_session(self):
        env = os.environ.copy()
        env.pop("GOOGLE_CLIENT_ID", None)
        env["LOCALPILOT_DEV_LOGIN"] = "1"
        with patch.dict(os.environ, env, clear=True):
            payload, resp = self._request("POST", "/api/v1/auth/google", {"devLogin": True})
        self.assertIn("session", payload)
        self.assertNotIn("id", payload["session"])
        self.assertEqual(payload["session"]["status"], "authenticated")
        cookie = self._session_cookie()
        self.assertIsNotNone(cookie)

    @patch.dict(os.environ, {"LOCALPILOT_DEV_LOGIN": "1"}, clear=False)
    def test_session_and_logout_flow(self):
        env = os.environ.copy()
        env.pop("GOOGLE_CLIENT_ID", None)
        env["LOCALPILOT_DEV_LOGIN"] = "1"
        with patch.dict(os.environ, env, clear=True):
            self._request("POST", "/api/v1/auth/google", {"devLogin": True})

        session_payload, _ = self._request("GET", "/api/v1/auth/session")
        self.assertIn("session", session_payload)
        self.assertEqual(session_payload["session"]["status"], "authenticated")

        logout_payload, _ = self._request("POST", "/api/v1/auth/logout")
        self.assertEqual(logout_payload["status"], "ok")

        with self.assertRaises(error.HTTPError) as ctx:
            self._request("GET", "/api/v1/auth/session")
        self.assertIn(ctx.exception.code, (401,))

    def test_no_cookie_returns_401_on_session(self):
        with self.assertRaises(error.HTTPError) as ctx:
            self._request("GET", "/api/v1/auth/session")
        self.assertEqual(ctx.exception.code, 401)

    def test_missing_credential_returns_400(self):
        with self.assertRaises(error.HTTPError) as ctx:
            self._request("POST", "/api/v1/auth/google", {})
        self.assertEqual(ctx.exception.code, 400)

    def test_cookie_auth_resolves_merchant(self):
        conn = store.connect(self.db_path)
        try:
            token = sessions.create_session(conn, store.DEMO_USER_ID, store.DEMO_MERCHANT_ID)
        finally:
            conn.close()
        req = request.Request(
            f"{self.base_url}/api/v1/channels/health",
            headers={"Accept": "application/json", "Cookie": f"lp_session={token}"},
        )
        resp = request.urlopen(req, timeout=5)
        payload = json.loads(resp.read().decode("utf-8"))
        self.assertIn("channels", payload)

    def test_session_response_never_contains_token(self):
        conn = store.connect(self.db_path)
        try:
            token = sessions.create_session(conn, store.DEMO_USER_ID, store.DEMO_MERCHANT_ID)
        finally:
            conn.close()
        req = request.Request(
            f"{self.base_url}/api/v1/auth/session",
            headers={"Accept": "application/json", "Cookie": f"lp_session={token}"},
        )
        resp = request.urlopen(req, timeout=5)
        raw = resp.read().decode("utf-8")
        self.assertNotIn(token, raw)


if __name__ == "__main__":
    unittest.main()
