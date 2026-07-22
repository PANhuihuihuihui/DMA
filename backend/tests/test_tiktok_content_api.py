import unittest

from backend.app import store
from backend.app.tiktok_content_api import TikTokContentApi, normalized_creator_info


class TikTokContentApiTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.api = TikTokContentApi(transport=self.transport)

    def transport(self, **kwargs):
        self.calls.append(kwargs)
        return {"data": {"publish_id": "provider-publish-42"}, "error": {"code": "ok"}}

    def test_inbox_init_has_official_path_bearer_and_source_shape(self):
        data = self.api.init_inbox_video("token-value", {"source": "PULL_FROM_URL", "video_url": "https://cdn.example.test/a.mp4"})
        self.assertEqual("provider-publish-42", data["publish_id"])
        call = self.calls[0]
        self.assertEqual("POST", call["method"])
        self.assertTrue(call["url"].endswith("/v2/post/publish/inbox/video/init/"))
        self.assertEqual("Bearer token-value", call["headers"]["Authorization"])
        self.assertEqual("PULL_FROM_URL", call["body"]["source_info"]["source"])

    def test_direct_post_and_status_use_documented_endpoints(self):
        self.api.init_direct_post_video("token", {"title": "Approved caption", "privacy_level": "PUBLIC_TO_EVERYONE"}, {"source": "PULL_FROM_URL", "video_url": "https://cdn.example.test/a.mp4"})
        self.api.fetch_status("token", "provider-publish-42")
        self.assertTrue(self.calls[0]["url"].endswith("/v2/post/publish/video/init/"))
        self.assertEqual("Approved caption", self.calls[0]["body"]["post_info"]["title"])
        self.assertTrue(self.calls[1]["url"].endswith("/v2/post/publish/status/fetch/"))
        self.assertEqual({"publish_id": "provider-publish-42"}, self.calls[1]["body"])

    def test_provider_error_is_normalized_without_response_body(self):
        api = TikTokContentApi(transport=lambda **_: {"error": {"code": "access_token_invalid", "message": "secret"}, "data": {}})
        with self.assertRaises(store.StoreError) as raised:
            api.creator_info("token")
        self.assertEqual(401, raised.exception.status)
        self.assertNotIn("secret", raised.exception.message)

    def test_creator_info_normalizes_provider_facts(self):
        info = normalized_creator_info({"privacy_level_options": ["PUBLIC_TO_EVERYONE"], "comment_disabled": True, "max_video_post_duration_sec": 180}, 3, "2026-01-01T00:00:00Z")
        self.assertEqual(3, info["version"])
        self.assertTrue(info["commentDisabled"])
        self.assertEqual(180, info["maxVideoPostDurationSec"])


if __name__ == "__main__":
    unittest.main()
