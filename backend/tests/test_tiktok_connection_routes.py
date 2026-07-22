import json
import os
import unittest
from unittest.mock import patch
from urllib import request
from urllib.parse import parse_qs, urlparse

from backend.app import tiktok_oauth, token_crypto
from backend.tests.test_fake_publish_lifecycle import ApiCase


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class TikTokConnectionRoutesTest(ApiCase):
    def setUp(self):
        super().setUp()
        self.key = token_crypto.generate_dev_key()

    def request_redirect(self, path):
        opener = request.build_opener(NoRedirect())
        with self.assertRaises(Exception) as raised:
            opener.open(f"{self.base_url}{path}", timeout=5)
        return raised.exception.headers["Location"]

    def test_start_rejects_untrusted_return_url_and_never_exposes_secrets(self):
        env = {
            "TIKTOK_CLIENT_KEY": "client-key",
            "TIKTOK_CLIENT_SECRET": "client-secret",
            "TIKTOK_OAUTH_RETURN_URL": "http://127.0.0.1:5173/app",
            "LOCALPILOT_TOKEN_KEY": self.key,
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            tiktok_oauth, "build_login_url", return_value="https://www.tiktok.com/v2/auth/authorize/?state=safe"
        ):
            location = self.request_redirect("/api/v1/tiktok/oauth/start?returnTo=https://evil.test/steal")
        self.assertIn("tiktok.com", location)
        self.assertNotIn("client-secret", location)
        self.assertNotIn("evil.test", location)

    def test_callback_redirect_is_marker_only_and_replay_is_safe(self):
        staged = "http://127.0.0.1:5173/app?connectSession=temporary"
        with patch.object(tiktok_oauth, "complete_callback", return_value=staged), patch.object(
            tiktok_oauth, "list_accounts_for_session", return_value=[{"id": "tt-123"}]
        ), patch.object(tiktok_oauth, "select_account", return_value={"status": "ok"}):
            location = self.request_redirect("/api/v1/tiktok/oauth/callback?state=state-secret&code=code-secret")
        query = parse_qs(urlparse(location).query)
        self.assertEqual(["1"], query["tiktokConnected"])
        self.assertNotIn("connectSession", query)
        self.assertNotIn("state", query)
        self.assertNotIn("code", query)
        self.assertNotIn("secret", location)

    def test_connection_status_is_redacted_and_disconnect_requires_reconnect(self):
        payload = self.get_json("/api/v1/tiktok/connection")
        self.assertIn("configured", payload)
        self.assertNotIn("access_token", json.dumps(payload).lower())
        disconnected = self.send_json("POST", "/api/v1/tiktok/connection/disconnect")
        self.assertEqual("ok", disconnected["status"])

    def test_denied_callback_uses_safe_owner_message_marker(self):
        location = self.request_redirect("/api/v1/tiktok/oauth/callback?error=access_denied&error_description=raw-provider-message")
        self.assertEqual(["1"], parse_qs(urlparse(location).query)["tiktokDenied"])
        self.assertNotIn("raw-provider-message", location)


if __name__ == "__main__":
    unittest.main()
