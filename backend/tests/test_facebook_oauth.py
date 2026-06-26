import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from backend.app import facebook_auth_provider, facebook_oauth, facebook_token_vault, store


class FacebookOAuthTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)
        facebook_oauth.reset_for_tests(conn=self.conn)

    def tearDown(self):
        facebook_oauth.reset_for_tests(conn=self.conn)
        self.conn.close()
        self.temp_dir.cleanup()

    def env(self):
        return patch.dict(
            "os.environ",
            {
                "FACEBOOK_APP_ID": "app_123",
                "FACEBOOK_APP_SECRET": "secret_123",
                "FACEBOOK_REDIRECT_URI": "http://127.0.0.1:8787/api/v1/facebook/oauth/callback",
                "FACEBOOK_OAUTH_RETURN_URL": "http://127.0.0.1:5173/app?facebookConnected=1",
                "LOCALPILOT_TOKEN_KEY": "NGHMXKUaLierxbBqmdaTBDMUsJYGYjfLdEvmzJaZrpU=",
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
        if "/me?" in url:
            return {"id": "user_123", "name": "Karen"}
        raise AssertionError(f"Unexpected Graph API URL: {url}")

    def test_login_url_uses_code_flow_scopes_redirect_uri_and_db_state(self):
        with self.env():
            login_url = facebook_oauth.build_login_url(conn=self.conn)

        parsed = urlparse(login_url)
        query = parse_qs(parsed.query)
        self.assertEqual("https", parsed.scheme)
        self.assertEqual("www.facebook.com", parsed.netloc)
        self.assertEqual("app_123", query["client_id"][0])
        self.assertEqual("http://127.0.0.1:8787/api/v1/facebook/oauth/callback", query["redirect_uri"][0])
        self.assertEqual("code", query["response_type"][0])
        self.assertTrue(query["state"][0].startswith("oauth_"))
        scopes = set(query["scope"][0].split(","))
        self.assertEqual({"pages_show_list", "pages_read_engagement", "pages_manage_posts"}, scopes)

        state_record = store.get_oauth_session(self.conn, query["state"][0], "state")
        self.assertEqual("http://127.0.0.1:5173/app?facebookConnected=1", state_record["returnUrl"])

    def test_callback_returns_db_connect_session_and_strips_page_tokens(self):
        with self.env(), patch.object(facebook_oauth, "graph_get", side_effect=self.graph_get):
            login_url = facebook_oauth.build_login_url(conn=self.conn)
            state = parse_qs(urlparse(login_url).query)["state"][0]
            return_url = facebook_oauth.complete_callback(self.conn, {"state": [state], "code": ["oauth_code"]})

        self.assertIn("connectSession=", return_url)
        self.assertTrue(return_url.startswith("http://127.0.0.1:5173/app"))
        session_id = parse_qs(urlparse(return_url).query)["connectSession"][0]
        pages = facebook_oauth.list_pages_for_session(session_id, conn=self.conn)
        self.assertEqual(1, len(pages))
        self.assertEqual("1243605852158721", pages[0]["id"])
        self.assertNotIn("access_token", pages[0])

        connect_session = store.get_oauth_session(self.conn, session_id, "connect")
        self.assertIn("expiresAt", connect_session)
        self.assertIn("issuedAt", connect_session)

        with self.assertRaises(store.StoreError):
            store.get_oauth_session(self.conn, state, "state")

    def test_select_page_persists_expiry_metadata_and_consumes_connect_session(self):
        with self.env(), patch.object(facebook_oauth, "graph_get", side_effect=self.graph_get), patch("builtins.print") as mock_print:
            login_url = facebook_oauth.build_login_url(conn=self.conn)
            state = parse_qs(urlparse(login_url).query)["state"][0]
            return_url = facebook_oauth.complete_callback(self.conn, {"state": [state], "code": ["oauth_code"]})
            session_id = parse_qs(urlparse(return_url).query)["connectSession"][0]
            status = facebook_oauth.select_page(self.conn, session_id, "1243605852158721")

        self.assertEqual("1243605852158721", status["activePage"]["pageId"])
        with self.env():
            self.assertEqual(
                "page_token_should_not_escape",
                facebook_token_vault.get_page_token("1243605852158721", conn=self.conn),
            )

        token_row = store.get_facebook_page_token_row(self.conn, "1243605852158721")
        self.assertIsNotNone(token_row)
        self.assertIsNotNone(token_row["issued_at"])
        self.assertIsNotNone(token_row["token_expires_at"])

        issued_at = datetime.fromisoformat(token_row["issued_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(token_row["token_expires_at"].replace("Z", "+00:00"))
        delta_seconds = int((expires_at - issued_at).total_seconds())
        self.assertGreaterEqual(delta_seconds, 5183943)
        self.assertLessEqual(delta_seconds, 5183944)
        mock_print.assert_called_once_with(
            f"Facebook page token stored, expires at {token_row['token_expires_at']}"
        )

        with self.assertRaises(store.StoreError):
            facebook_oauth.list_pages_for_session(session_id, conn=self.conn)

    def test_reset_for_tests_clears_db_oauth_sessions(self):
        with self.env():
            login_url = facebook_oauth.build_login_url(conn=self.conn)
        state = parse_qs(urlparse(login_url).query)["state"][0]
        self.assertEqual("http://127.0.0.1:5173/app?facebookConnected=1", store.get_oauth_session(self.conn, state, "state")["returnUrl"])

        facebook_oauth.reset_for_tests(conn=self.conn)

        with self.assertRaises(store.StoreError):
            store.get_oauth_session(self.conn, state, "state")

    def test_facebook_auth_provider_delegates_existing_oauth_helpers(self):
        provider = facebook_auth_provider.FacebookAuthProvider()
        config = {
            "appId": "app_123",
            "appSecret": "secret_123",
            "graphBase": "https://graph.facebook.com/v25.0",
            "returnUrl": "http://127.0.0.1:5173/app?facebookConnected=1",
        }

        with patch.object(facebook_oauth, "build_login_url", return_value="https://example.test/oauth") as build_login_url, patch.object(
            facebook_oauth,
            "exchange_code_for_user_token",
            return_value={"access_token": "short_user_token"},
        ) as exchange_code_for_user_token, patch.object(
            facebook_oauth,
            "exchange_for_long_lived_user_token",
            return_value={"access_token": "long_user_token", "expires_in": 5183944},
        ) as exchange_for_long_lived_user_token, patch.object(
            facebook_oauth,
            "fetch_pages",
            return_value=[{"id": "page_1"}],
        ) as fetch_pages, patch.object(
            facebook_oauth,
            "graph_get",
            return_value={"id": "user_123", "name": "Karen"},
        ) as graph_get:
            self.assertEqual("https://example.test/oauth", provider.build_auth_url(config))
            token_payload = provider.exchange_code(self.conn, "oauth_code", config)
            profile = provider.get_profile("page_token", config)
            pages = provider.list_selectable_accounts("page_token", config)

        build_login_url.assert_called_once_with(return_url=config["returnUrl"], config=config)
        exchange_code_for_user_token.assert_called_once_with("oauth_code", config)
        exchange_for_long_lived_user_token.assert_called_once_with("short_user_token", config)
        fetch_pages.assert_called_once_with("page_token", config)
        self.assertIn("/me?", graph_get.call_args.args[0])
        self.assertEqual("long_user_token", token_payload["access_token"])
        self.assertEqual(5183944, token_payload["expires_in"])
        self.assertEqual("Karen", profile["name"])
        self.assertEqual([{"id": "page_1"}], pages)


if __name__ == "__main__":
    unittest.main()
