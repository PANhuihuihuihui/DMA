import json
import os
import unittest
from unittest.mock import patch
from urllib import request
from urllib.parse import parse_qs, urlparse

from backend.app import instagram_oauth
from backend.tests.test_fake_publish_lifecycle import ApiCase


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class InstagramConnectionRoutesTest(ApiCase):
    def request_redirect(self, path):
        opener = request.build_opener(NoRedirect())
        with self.assertRaises(Exception) as raised:
            opener.open(f"{self.base_url}{path}", timeout=5)
        return raised.exception.headers["Location"]

    def test_start_rejects_untrusted_return_url_and_never_exposes_secrets(self):
        env = {"INSTAGRAM_APP_ID": "app", "INSTAGRAM_APP_SECRET": "secret", "INSTAGRAM_OAUTH_RETURN_URL": "http://127.0.0.1:5173/app"}
        with patch.dict(os.environ, env, clear=False), patch.object(instagram_oauth, "build_login_url", return_value="https://www.instagram.com/oauth/authorize?state=safe"):
            location = self.request_redirect("/api/v1/instagram/oauth/start?returnTo=https://evil.test/steal")
        self.assertIn("instagram.com", location)
        self.assertNotIn("secret", location)
        self.assertNotIn("evil.test", location)

    def test_callback_redirect_is_marker_only_and_replay_is_safe(self):
        staged = "http://127.0.0.1:5173/app?connectSession=temporary"
        with patch.object(instagram_oauth, "complete_callback", return_value=staged), patch.object(instagram_oauth, "list_accounts_for_session", return_value=[{"id": "ig-123"}]), patch.object(instagram_oauth, "select_account", return_value={"status": "ok"}):
            location = self.request_redirect("/api/v1/instagram/oauth/callback?state=state-secret&code=code-secret")
        query = parse_qs(urlparse(location).query)
        self.assertEqual(["1"], query["instagramConnected"])
        self.assertNotIn("connectSession", query)
        self.assertNotIn("state", query)
        self.assertNotIn("code", query)
        self.assertNotIn("secret", location)

    def test_connection_status_is_redacted_and_disconnect_requires_reconnect(self):
        payload = self.get_json("/api/v1/instagram/connection")
        self.assertIn("configured", payload)
        self.assertNotIn("access_token", json.dumps(payload).lower())
        disconnected = self.send_json("POST", "/api/v1/instagram/connection/disconnect")
        self.assertEqual("ok", disconnected["status"])

    def test_denied_callback_uses_safe_owner_message_marker(self):
        location = self.request_redirect("/api/v1/instagram/oauth/callback?error=access_denied&error_description=raw-provider-message")
        self.assertEqual(["1"], parse_qs(urlparse(location).query)["instagramDenied"])
        self.assertNotIn("raw-provider-message", location)


if __name__ == "__main__":
    unittest.main()
