import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib import error

from backend.app import instagram_publisher, store


class Response:
    def __init__(self, payload=None, headers=None):
        self.payload = payload or {}
        self.headers = headers or {}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.payload).encode()


def image_ref(url):
    return {"kind": "image", "url": url}


def snapshot(refs):
    return {"caption": "Summer tune-up", "body": "Keep cool.", "cta": "Book today", "mediaRefs": refs}


def head_ok(req, timeout=10):
    return Response(headers={"Content-Type": "image/jpeg", "Content-Length": "120"})


class InstagramPublisherTest(unittest.TestCase):
    def test_single_image_uses_container_poll_then_publish(self):
        calls = []
        def opener(req, timeout=15):
            calls.append((req.method, req.full_url, req.data.decode() if req.data else ""))
            if req.method == "POST" and req.full_url.endswith("/media"):
                return Response({"id": "container-1"})
            if req.method == "GET":
                return Response({"status_code": "FINISHED", "permalink": "https://instagram.com/p/ok"})
            if req.full_url.endswith("/media_publish"):
                return Response({"id": "media-1"})
            self.fail(req.full_url)
        media = {"kind": "image", "urls": ["https://cdn.example.test/a.jpg?signature=never-persist"], "caption": "Hello"}
        with patch("backend.app.instagram_publisher.auth_provider.get_valid_credential", return_value="token"), patch("backend.app.instagram_publisher.auth_provider.run_with_credential_refresh", lambda _c, _p, _r, _cfg, op: op("token")):
            result = instagram_publisher.publish_approved_snapshot({}, "ig-user", {"merchant_id": "merchant", "token_expires_at": None}, media, conn=MagicMock(), graph_base="https://graph.test", opener=opener, sleep=lambda _: None)
        self.assertEqual("media-1", result["diagnostics"]["mediaId"])
        self.assertEqual(["POST", "GET", "POST"], [call[0] for call in calls])
        self.assertNotIn("signature=never-persist", json.dumps(result))

    def test_carousel_creates_and_polls_children_before_parent(self):
        sequence = iter([{"id": "child-1"}, {"status_code": "FINISHED"}, {"id": "child-2"}, {"status_code": "FINISHED"}, {"id": "parent"}, {"status_code": "FINISHED"}, {"id": "published"}])
        calls = []
        def opener(req, timeout=15):
            calls.append((req.method, req.full_url, req.data.decode() if req.data else ""))
            return Response(next(sequence))
        media = {"kind": "carousel", "urls": ["https://cdn.example.test/a.jpg", "https://cdn.example.test/b.jpeg"], "caption": "Hello"}
        with patch("backend.app.instagram_publisher.auth_provider.get_valid_credential", return_value="token"), patch("backend.app.instagram_publisher.auth_provider.run_with_credential_refresh", lambda _c, _p, _r, _cfg, op: op("token")):
            result = instagram_publisher.publish_approved_snapshot({}, "ig-user", {"merchant_id": "merchant", "token_expires_at": None}, media, conn=MagicMock(), graph_base="https://graph.test", opener=opener, sleep=lambda _: None)
        self.assertEqual(["child-1", "child-2"], result["diagnostics"]["childContainerIds"])
        self.assertIn("children=child-1%2Cchild-2", calls[4][2])
        self.assertEqual("https://graph.test/ig-user/media_publish", calls[-1][1])

    def test_poll_terminal_and_timeout_are_bounded(self):
        def terminal(req, timeout=15): return Response({"status_code": "EXPIRED"})
        with self.assertRaises(instagram_publisher.InstagramProviderError) as raised:
            instagram_publisher._poll_container("c", "token", "https://graph.test", terminal, lambda _: None, lambda: 0, 3, 0)
        self.assertEqual("container_terminal_failure", raised.exception.diagnostics["result"])
        attempts = []
        def pending(req, timeout=15): attempts.append(req.full_url); return Response({"status_code": "IN_PROGRESS"})
        with self.assertRaises(instagram_publisher.InstagramProviderError) as raised:
            instagram_publisher._poll_container("c", "token", "https://graph.test", pending, lambda _: None, lambda: 0, 3, 0)
        self.assertEqual("container_poll_timeout", raised.exception.diagnostics["result"])
        self.assertEqual(3, len(attempts))

    def test_validation_blocks_private_non_jpeg_oversize_and_bad_counts(self):
        bad = [[], [image_ref("https://127.0.0.1/a.jpg")], [image_ref("https://cdn.example.test/a.png")], [image_ref(f"https://cdn.example.test/{i}.jpg") for i in range(11)]]
        for refs in bad:
            with self.subTest(refs=refs), self.assertRaises(store.StoreError):
                instagram_publisher.validate_instagram_media(snapshot(refs), opener=head_ok)
        with self.assertRaises(store.StoreError):
            instagram_publisher.validate_instagram_media(snapshot([image_ref("https://cdn.example.test/a.jpg")]), opener=lambda *a, **k: Response(headers={"Content-Length": str(9 * 1024 * 1024)}))

    def test_persisted_snapshot_strips_signed_media_query(self):
        safe = instagram_publisher._persistable_snapshot(snapshot([image_ref("https://cdn.example.test/a.jpg?signature=do-not-store")]))
        self.assertEqual("https://cdn.example.test/a.jpg", safe["mediaRefs"][0]["url"])
        self.assertNotIn("signature", json.dumps(safe))

    def test_graph_error_is_classified_without_raw_message_or_token(self):
        def rejected(req, timeout=15):
            payload = {"error": {"message": "raw provider token=secret", "code": 190, "error_subcode": 463, "fbtrace_id": "trace-1"}}
            raise error.HTTPError(req.full_url, 401, "Unauthorized", {}, BytesIO(json.dumps(payload).encode()))
        with self.assertRaises(instagram_publisher.InstagramProviderError) as raised:
            instagram_publisher.graph_request("POST", "https://graph.test/media", "secret-token", {}, rejected)
        details = raised.exception.diagnostics
        self.assertEqual("authentication", details["errorClass"])
        self.assertEqual(190, details["code"])
        self.assertNotIn("message", details)
        self.assertNotIn("secret", json.dumps(details))


if __name__ == "__main__":
    unittest.main()
