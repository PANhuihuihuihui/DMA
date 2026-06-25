import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib import error, request

from backend.app import sessions, store, website_crawl
from backend.app.server import create_app


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def read(self, *_args, **_kwargs):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestFetchHomepage(unittest.TestCase):
    def test_successful_fetch_returns_html(self):
        with patch("backend.app.website_crawl._resolve_public_host") as host_check:
            with patch(
                "backend.app.website_crawl.request.urlopen",
                return_value=FakeResponse(b"<html><body>Hello</body></html>"),
            ) as mock_urlopen:
                result = website_crawl.fetch_homepage("https://example.com")
        self.assertIn("Hello", result)
        req = mock_urlopen.call_args.args[0]
        self.assertEqual(req.headers["User-agent"], website_crawl.USER_AGENT)
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], website_crawl.FETCH_TIMEOUT_SECONDS)
        host_check.assert_called_once()

    def test_timeout_raises_crawl_error(self):
        with patch("backend.app.website_crawl._resolve_public_host"):
            with patch("backend.app.website_crawl.request.urlopen", side_effect=socket.timeout):
                with self.assertRaises(website_crawl.CrawlError) as ctx:
                    website_crawl.fetch_homepage("https://example.com")
        self.assertIn("timed out", ctx.exception.message.lower())

    def test_invalid_url_raises_crawl_error(self):
        with self.assertRaises(website_crawl.CrawlError):
            website_crawl.fetch_homepage("file:///tmp/local")

    def test_http_error_raises_crawl_error(self):
        http_error = error.HTTPError("https://example.com", 404, "Not Found", None, None)
        with patch("backend.app.website_crawl._resolve_public_host"):
            with patch(
                "backend.app.website_crawl.request.urlopen",
                side_effect=http_error,
            ):
                with self.assertRaises(website_crawl.CrawlError) as ctx:
                    website_crawl.fetch_homepage("https://example.com")
        self.assertIn("404", ctx.exception.message)
        http_error.close()


class TestCleanHtmlForLlm(unittest.TestCase):
    def test_scripts_styles_and_nav_are_stripped(self):
        html = """
        <html>
          <head>
            <title>Demo Co</title>
            <style>.bad { color: red; }</style>
            <meta name="description" content="Fast local help">
            <meta property="og:image" content="https://example.com/logo.png">
          </head>
          <body>
            <nav>Hidden nav</nav>
            <h1>Visible headline</h1>
            <script>window.alert('x')</script>
          </body>
        </html>
        """
        cleaned = website_crawl.clean_html_for_llm(html)
        self.assertIn("Title: Demo Co", cleaned)
        self.assertIn("description: Fast local help", cleaned)
        self.assertIn("og:image: https://example.com/logo.png", cleaned)
        self.assertIn("Visible headline", cleaned)
        self.assertNotIn("Hidden nav", cleaned)
        self.assertNotIn("window.alert", cleaned)

    def test_json_ld_is_preserved(self):
        html = """
        <html>
          <head>
            <script type="application/ld+json">
              {"@context":"https://schema.org","name":"Demo Co"}
            </script>
          </head>
          <body>Visible text</body>
        </html>
        """
        cleaned = website_crawl.clean_html_for_llm(html)
        self.assertIn("JSON-LD", cleaned)
        self.assertIn('"name":"Demo Co"', cleaned)

    def test_long_content_is_truncated(self):
        html = "<html><body>" + ("hello " * 10000) + "</body></html>"
        cleaned = website_crawl.clean_html_for_llm(html)
        self.assertLessEqual(len(cleaned), website_crawl.MAX_LLM_CHARS)

    def test_plain_text_passes_through(self):
        cleaned = website_crawl.clean_html_for_llm("Simple local business copy")
        self.assertIn("Simple local business copy", cleaned)


class TestExtractBrandProfile(unittest.TestCase):
    def _mock_llm_response(self, payload):
        body = json.dumps({"choices": [{"message": {"content": json.dumps(payload)}}]}).encode("utf-8")
        return FakeResponse(body)

    def test_successful_extraction_returns_all_fields(self):
        payload = {
            "name": "Demo Co",
            "description": "Fast local service",
            "industry": "services",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#AABBCC",
            "secondary_color": "#DDEEFF",
            "accent_color": "#123456",
            "font_family": "Sora",
            "language": "en",
            "timezone": "America/Detroit",
            "tonality": "professional",
            "voiceover": "Warm owner voice",
            "avatar": "Owner-style avatar",
            "target_audience": "Homeowners",
        }
        with patch("backend.app.website_crawl.request.urlopen", return_value=self._mock_llm_response(payload)):
            profile = website_crawl.extract_brand_profile("demo text", api_key="test-key")
        for field in website_crawl.PROFILE_FIELDS:
            self.assertIn(field, profile)
        self.assertEqual(profile["primary_color"], "#aabbcc")
        self.assertEqual(profile["timezone"], "America/Detroit")
        self.assertEqual(profile["voiceover"], "Warm owner voice")
        self.assertEqual(profile["avatar"], "Owner-style avatar")

    def test_partial_response_fills_missing_fields_with_empty_strings(self):
        with patch(
            "backend.app.website_crawl.request.urlopen",
            return_value=self._mock_llm_response({"name": "Demo Co"}),
        ):
            profile = website_crawl.extract_brand_profile("demo text", api_key="test-key")
        self.assertEqual(profile["name"], "Demo Co")
        self.assertEqual(profile["description"], "")
        self.assertEqual(profile["timezone"], "")
        self.assertEqual(profile["voiceover"], "Warm owner voice")
        self.assertEqual(profile["avatar"], "Owner-style avatar")

    def test_llm_failure_returns_empty_defaults(self):
        with patch("backend.app.website_crawl.request.urlopen", side_effect=error.URLError("boom")):
            profile = website_crawl.extract_brand_profile("demo text", api_key="test-key")
        self.assertEqual(profile["name"], "")
        self.assertEqual(profile["raw_extraction_json"], {})

    def test_xss_is_sanitized(self):
        payload = {
            "name": "<script>alert(1)</script>Demo",
            "description": "<b>Local</b> & trusted",
            "logo_url": "javascript:alert(1)",
            "primary_color": "rgb(0,0,0)",
            "language": "EN",
            "timezone": "Bad/Zone",
            "tonality": "PROFESSIONAL",
            "voiceover": "<b>Warm owner voice</b>",
            "avatar": "<img src=x onerror=alert(1)>Owner-style avatar",
            "target_audience": "<img src=x onerror=alert(1)>Owners",
        }
        with patch("backend.app.website_crawl.request.urlopen", return_value=self._mock_llm_response(payload)):
            profile = website_crawl.extract_brand_profile("demo text", api_key="test-key")
        self.assertEqual(profile["name"], "alert(1) Demo")
        self.assertEqual(profile["description"], "Local &amp; trusted")
        self.assertEqual(profile["logo_url"], "")
        self.assertEqual(profile["primary_color"], "")
        self.assertEqual(profile["language"], "en")
        self.assertEqual(profile["timezone"], "")
        self.assertEqual(profile["tonality"], "professional")
        self.assertEqual(profile["voiceover"], "Warm owner voice")
        self.assertEqual(profile["avatar"], "Owner-style avatar")
        self.assertEqual(profile["target_audience"], "Owners")


class TestCarouselStoryExtraction(unittest.TestCase):
    def _mock_llm_response(self, payload):
        body = json.dumps({"choices": [{"message": {"content": json.dumps(payload)}}]}).encode("utf-8")
        return FakeResponse(body)

    def test_extract_carousel_story_brief_returns_content_only_fields(self):
        payload = {
            "sourceTitle": "Nike Running",
            "sourceDomain": "www.nike.com",
            "summary": "Public running collection page.",
            "sourceHealth": "ready",
            "slideSeeds": {
                "cover": "Nike running update",
                "problem": "Runners need the right daily shoe.",
                "proof": "Highlight one source-backed proof cue.",
                "offer": "Show the current collection value.",
                "cta": "Shop the collection.",
            },
        }
        with patch("backend.app.website_crawl.request.urlopen", return_value=self._mock_llm_response(payload)):
            brief = website_crawl.extract_carousel_story_brief("Title: Nike\nBody: Running", api_key="test-key")
        self.assertEqual("Nike Running", brief["sourceTitle"])
        self.assertEqual("www.nike.com", brief["sourceDomain"])
        self.assertEqual("ready", brief["sourceHealth"])
        self.assertEqual("Nike running update", brief["slideSeeds"]["cover"])

    def test_fallback_carousel_story_brief_uses_domain_and_cleaned_text(self):
        brief = website_crawl.fallback_carousel_story_brief(
            "https://www.nike.com/",
            "Title: Nike Running\nBody: Public running collection page.",
            {"offer": "Seasonal running collection"},
        )
        self.assertEqual("Nike Running", brief["sourceTitle"])
        self.assertEqual("www.nike.com", brief["sourceDomain"])
        self.assertEqual("limited", brief["sourceHealth"])
        self.assertIn("Seasonal running collection", brief["slideSeeds"]["cover"])


class TestOnboardingRoutes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "website-crawl.sqlite")
        self.server = create_app(host="127.0.0.1", port=0, db_path=self.db_path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

        conn = store.connect(self.db_path)
        now = store.utc_now()
        self.merchant_id = "merchant_onboarding"
        self.user_id = "user_onboarding"
        conn.execute("insert into merchants values (?, ?, ?)", (self.merchant_id, "Onboarding Co", now))
        conn.execute(
            "insert into users (id, merchant_id, name, email, role, created_at) values (?, ?, ?, ?, ?, ?)",
            (self.user_id, self.merchant_id, "Owner", "owner@example.com", "owner", now),
        )
        self.session_token = sessions.create_session(conn, self.user_id, self.merchant_id)
        conn.close()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def _request(self, method, path, body=None, *, include_token=True):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json"}
        if data:
            headers["Content-Type"] = "application/json"
        if include_token:
            headers["Cookie"] = f"lp_session={self.session_token}"
        req = request.Request(f"{self.base_url}{path}", data=data, method=method, headers=headers)
        with request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_full_crawl_edit_confirm_flow(self):
        extracted = {
            "name": "Onboarding Co",
            "description": "Trusted local service",
            "industry": "services",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#123456",
            "secondary_color": "#abcdef",
            "accent_color": "#fedcba",
            "font_family": "Sora",
            "language": "en",
            "timezone": "America/Detroit",
            "tonality": "professional",
            "voiceover": "Warm owner voice",
            "avatar": "Owner-style avatar",
            "target_audience": "Owners",
            "raw_extraction_json": {"name": "Onboarding Co"},
        }
        with patch("backend.app.server.website_crawl.fetch_homepage", return_value="<html>demo</html>"):
            with patch("backend.app.server.website_crawl.clean_html_for_llm", return_value="demo"):
                with patch("backend.app.server.website_crawl.extract_brand_profile", return_value=extracted):
                    status, payload = self._request(
                        "POST",
                        "/api/v1/onboarding/crawl",
                        {"url": "https://example.com"},
                    )
        self.assertEqual(status, 201)
        self.assertEqual(payload["profile"]["status"], "draft")
        self.assertEqual(payload["profile"]["name"], "Onboarding Co")

        _, payload = self._request("GET", "/api/v1/onboarding/profile")
        self.assertEqual(payload["profile"]["crawlUrl"], "https://example.com")
        self.assertEqual(payload["profile"]["voiceover"], "Warm owner voice")
        self.assertEqual(payload["profile"]["avatar"], "Owner-style avatar")

        _, payload = self._request(
            "PATCH",
            "/api/v1/onboarding/profile",
            {
                "name": "Onboarding Co Updated",
                "voiceover": "Clear service narrator",
                "avatar": "Service expert avatar",
            },
        )
        self.assertEqual(payload["profile"]["name"], "Onboarding Co Updated")
        self.assertEqual(payload["profile"]["voiceover"], "Clear service narrator")
        self.assertEqual(payload["profile"]["avatar"], "Service expert avatar")

        _, payload = self._request("POST", "/api/v1/onboarding/profile/confirm")
        self.assertEqual(payload["profile"]["status"], "confirmed")

        conn = store.connect(self.db_path)
        brand = conn.execute("select * from brand_kits where merchant_id = ?", (self.merchant_id,)).fetchone()
        conn.close()
        self.assertIsNotNone(brand)
        voice = json.loads(brand["voice_json"])
        self.assertEqual(voice["voiceover"], "Clear service narrator")
        self.assertEqual(voice["avatar"], "Service expert avatar")

    def test_recrawl_replaces_existing_draft(self):
        first = {"name": "First Name", "raw_extraction_json": {"name": "First Name"}}
        second = {"name": "Second Name", "raw_extraction_json": {"name": "Second Name"}}
        with patch("backend.app.server.website_crawl.fetch_homepage", return_value="<html>demo</html>"):
            with patch("backend.app.server.website_crawl.clean_html_for_llm", return_value="demo"):
                with patch("backend.app.server.website_crawl.extract_brand_profile", side_effect=[first, second]):
                    _, payload1 = self._request("POST", "/api/v1/onboarding/crawl", {"url": "https://example.com"})
                    _, payload2 = self._request("POST", "/api/v1/onboarding/crawl", {"url": "https://example.com/new"})
        self.assertEqual(payload1["profile"]["id"], payload2["profile"]["id"])
        self.assertEqual(payload2["profile"]["name"], "Second Name")
        self.assertEqual(payload2["profile"]["crawlUrl"], "https://example.com/new")

    def test_confirm_seeds_brand_kits(self):
        with patch("backend.app.server.website_crawl.fetch_homepage", return_value="<html>demo</html>"):
            with patch("backend.app.server.website_crawl.clean_html_for_llm", return_value="demo"):
                with patch(
                    "backend.app.server.website_crawl.extract_brand_profile",
                    return_value={
                        "name": "Brand Seed",
                        "logo_url": "https://example.com/logo.png",
                        "primary_color": "#111111",
                        "font_family": "Sora",
                        "tonality": "professional",
                        "voiceover": "Warm owner voice",
                        "avatar": "Owner-style avatar",
                        "target_audience": "Owners",
                        "language": "en",
                        "description": "Seeded profile",
                        "raw_extraction_json": {"name": "Brand Seed"},
                    },
                ):
                    self._request("POST", "/api/v1/onboarding/crawl", {"url": "https://example.com"})
        self._request("POST", "/api/v1/onboarding/profile/confirm")
        conn = store.connect(self.db_path)
        brand = conn.execute("select * from brand_kits where merchant_id = ?", (self.merchant_id,)).fetchone()
        conn.close()
        self.assertIsNotNone(brand)
        self.assertEqual(json.loads(brand["colors_json"]), ["#111111"])
        self.assertEqual(json.loads(brand["voice_json"])["voiceover"], "Warm owner voice")
        self.assertEqual(json.loads(brand["voice_json"])["avatar"], "Owner-style avatar")

    def test_edit_on_confirmed_profile_returns_409(self):
        conn = store.connect(self.db_path)
        store.upsert_merchant_profile(conn, self.merchant_id, {"name": "Locked"})
        store.confirm_merchant_profile(conn, self.merchant_id)
        conn.close()
        req = request.Request(
            f"{self.base_url}/api/v1/onboarding/profile",
            data=json.dumps({"name": "Nope"}).encode("utf-8"),
            method="PATCH",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Cookie": f"lp_session={self.session_token}",
            },
        )
        with self.assertRaises(error.HTTPError) as ctx:
            request.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 409)
        ctx.exception.close()

    def test_routes_require_authenticated_session(self):
        with self.assertRaises(error.HTTPError) as ctx:
            self._request("GET", "/api/v1/onboarding/profile", include_token=False)
        self.assertEqual(ctx.exception.code, 401)
        ctx.exception.close()

    def test_crawl_failure_returns_warning_and_partial_profile(self):
        with patch(
            "backend.app.server.website_crawl.fetch_homepage",
            side_effect=website_crawl.CrawlError("Website could not be reached."),
        ):
            status, payload = self._request(
                "POST",
                "/api/v1/onboarding/crawl",
                {"url": "https://example.com"},
            )
        self.assertEqual(status, 201)
        self.assertEqual(payload["warning"], "Website could not be reached.")
        self.assertEqual(payload["profile"]["crawlUrl"], "https://example.com")
        self.assertEqual(payload["profile"]["name"], "")
        self.assertEqual(payload["profile"]["voiceover"], "Warm owner voice")
        self.assertEqual(payload["profile"]["avatar"], "Owner-style avatar")


if __name__ == "__main__":
    unittest.main()
