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
        with self.assertLogs("backend.app.facebook_oauth", level="INFO") as logs:
            with self.env(), patch.object(facebook_oauth, "graph_get", side_effect=self.graph_get):
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
        self.assertTrue(any("facebook_page_token_stored" in line for line in logs.output))
        self.assertFalse(any("page_token_should_not_escape" in line for line in logs.output))

        with self.assertRaises(store.StoreError):
            facebook_oauth.list_pages_for_session(session_id, conn=self.conn)

    def test_oauth_session_helpers_require_a_database_connection_and_have_no_legacy_maps(self):
        with self.assertRaises(store.StoreError) as build_error:
            facebook_oauth.build_login_url()
        self.assertEqual(500, build_error.exception.status)

        with self.assertRaises(store.StoreError) as state_error:
            facebook_oauth.pop_valid_state("missing")
        self.assertEqual(500, state_error.exception.status)

        source = Path(facebook_oauth.__file__).read_text()
        self.assertNotIn("_OAUTH_STATES", source)
        self.assertNotIn("_CONNECT_SESSIONS", source)
        self.assertIn("create_oauth_session", source)
        self.assertIn("consume_oauth_session", Path(store.__file__).read_text())

    def test_reset_for_tests_clears_db_oauth_sessions(self):
        with self.env():
            login_url = facebook_oauth.build_login_url(conn=self.conn)
        state = parse_qs(urlparse(login_url).query)["state"][0]
        self.assertEqual("http://127.0.0.1:5173/app?facebookConnected=1", store.get_oauth_session(self.conn, state, "state")["returnUrl"])

        facebook_oauth.reset_for_tests(conn=self.conn)

        with self.assertRaises(store.StoreError):
            store.get_oauth_session(self.conn, state, "state")

    def test_long_lived_exchange_failure_falls_back_without_logging_token(self):
        with self.env(), self.assertLogs("backend.app.facebook_oauth", level="WARNING") as logs:
            with patch.object(
                facebook_oauth,
                "graph_get",
                side_effect=store.StoreError(502, "provider response included short_user_token"),
            ):
                result = facebook_oauth.exchange_for_long_lived_user_token(
                    "short_user_token",
                    facebook_oauth.oauth_config(),
                )

        self.assertEqual(result, {})
        self.assertTrue(any("facebook_long_lived_exchange_fallback" in line for line in logs.output))
        self.assertFalse(any("short_user_token" in line for line in logs.output))

    def test_provider_rejects_missing_authorization_token(self):
        provider = facebook_auth_provider.FacebookAuthProvider()
        config = {"appId": "app_123", "appSecret": "secret_123"}
        with patch.object(facebook_oauth, "exchange_code_for_user_token", return_value={}):
            with self.assertRaises(store.StoreError) as ctx:
                provider.exchange_code(self.conn, "oauth_code", config)

        self.assertEqual(ctx.exception.status, 502)
        self.assertNotIn("oauth_code", ctx.exception.message)

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
            self.assertEqual("https://example.test/oauth", provider.build_auth_url(config, conn=self.conn))
            token_payload = provider.exchange_code(self.conn, "oauth_code", config)
            profile = provider.get_profile("page_token", config)
            pages = provider.list_selectable_accounts("page_token", config)

        build_login_url.assert_called_once_with(return_url=config["returnUrl"], conn=self.conn, config=config)
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
