import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from backend.app import facebook_oauth, facebook_token_vault, store


class FacebookOAuthTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)
        facebook_oauth.reset_for_tests()

    def tearDown(self):
        self.conn.close()
        facebook_oauth.reset_for_tests()
        self.temp_dir.cleanup()

    def env(self):
        return patch.dict(
            "os.environ",
            {
                "FACEBOOK_APP_ID": "app_123",
                "FACEBOOK_APP_SECRET": "secret_should_not_escape",
                "FACEBOOK_REDIRECT_URI": "http://127.0.0.1:8787/api/v1/facebook/oauth/callback",
                "FACEBOOK_OAUTH_RETURN_URL": "http://127.0.0.1:5173/app",
                "FACEBOOK_GRAPH_API_BASE": "https://graph.facebook.test/v25.0",
                "FACEBOOK_DIALOG_BASE": "https://www.facebook.test/v25.0/dialog/oauth",
                "FACEBOOK_DEMO_PAGE_ID": "1243605852158721",
            },
            clear=False,
        )

    def graph_get(self, url):
        if "/oauth/access_token" in url and "grant_type=fb_exchange_token" not in url:
            return {"access_token": "short_user_token"}
        if "/oauth/access_token" in url and "grant_type=fb_exchange_token" in url:
            return {"access_token": "long_user_token", "expires_in": 5183944}
        if "/me/accounts" in url:
            return {
                "data": [
                    {
                        "id": "1243605852158721",
                        "name": "Aurora Heating & Cooling",
                        "category": "Local service",
                        "link": "https://www.facebook.com/1243605852158721",
                        "tasks": ["CREATE_CONTENT", "MANAGE"],
                        "access_token": "page_token_should_not_escape",
                    }
                ]
            }
        self.fail(f"Unexpected graph URL: {url}")

    def test_login_url_uses_code_flow_scopes_redirect_uri_and_state(self):
        with self.env():
            login_url = facebook_oauth.build_login_url()

        parsed = urlparse(login_url)
        query = parse_qs(parsed.query)
        self.assertEqual("www.facebook.test", parsed.netloc)
        self.assertEqual("app_123", query["client_id"][0])
        self.assertEqual("code", query["response_type"][0])
        self.assertEqual("http://127.0.0.1:8787/api/v1/facebook/oauth/callback", query["redirect_uri"][0])
        self.assertIn("state", query)
        scopes = set(query["scope"][0].split(","))
        self.assertEqual({"pages_show_list", "pages_read_engagement", "pages_manage_posts"}, scopes)

    def test_callback_returns_connect_session_without_auto_committing(self):
        with self.env(), patch.object(facebook_oauth, "graph_get", side_effect=self.graph_get):
            login_url = facebook_oauth.build_login_url()
            state = parse_qs(urlparse(login_url).query)["state"][0]
            return_url = facebook_oauth.complete_callback(self.conn, {"state": [state], "code": ["oauth_code"]})

        self.assertIn("connectSession=", return_url)
        self.assertTrue(return_url.startswith("http://127.0.0.1:5173/app"))
        session_id = parse_qs(urlparse(return_url).query)["connectSession"][0]
        pages = facebook_oauth.list_pages_for_session(session_id)
        self.assertEqual(1, len(pages))
        self.assertEqual("1243605852158721", pages[0]["id"])
        self.assertNotIn("access_token", pages[0])
        self.assertIsNone(facebook_token_vault.get_page_token("1243605852158721"))

    def test_select_page_commits_active_token_and_hides_secrets(self):
        with self.env(), patch.object(facebook_oauth, "graph_get", side_effect=self.graph_get):
            login_url = facebook_oauth.build_login_url()
            state = parse_qs(urlparse(login_url).query)["state"][0]
            return_url = facebook_oauth.complete_callback(self.conn, {"state": [state], "code": ["oauth_code"]})
            session_id = parse_qs(urlparse(return_url).query)["connectSession"][0]
            result = facebook_oauth.select_page(self.conn, session_id, "1243605852158721")

        self.assertEqual("page_token_should_not_escape", facebook_token_vault.get_page_token("1243605852158721"))
        workflow = store.get_workflow(self.conn)
        facebook_channel = next(ch for ch in workflow["connectedChannels"] if ch["platform"] == "facebook")
        self.assertEqual("Aurora Heating & Cooling", facebook_channel["displayName"])

        rendered = json.dumps(result, sort_keys=True)
        self.assertNotIn("page_token_should_not_escape", rendered)
        self.assertNotIn("short_user_token", rendered)
        self.assertNotIn("long_user_token", rendered)
        self.assertNotIn("secret_should_not_escape", rendered)

    def test_callback_rejects_invalid_state(self):
        with self.env():
            with self.assertRaises(store.StoreError) as raised:
                facebook_oauth.complete_callback(self.conn, {"state": ["bad"], "code": ["oauth_code"]})
        self.assertEqual(400, raised.exception.status)


if __name__ == "__main__":
    unittest.main()
