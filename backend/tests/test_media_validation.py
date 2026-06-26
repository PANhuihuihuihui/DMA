import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock

from backend.app import facebook_publisher, store


def _make_snapshot(media_refs=None, link=None):
    s = {"caption": "Test post", "body": "Body text"}
    if media_refs is not None:
        s["mediaRefs"] = media_refs
    if link is not None:
        s["link"] = link
    return s


def _image_ref(url, kind="image"):
    return {"kind": kind, "url": url}


def _successful_head(content_type="image/jpeg", content_length=50000):
    def opener(req, timeout=10):
        resp = MagicMock()
        resp.__enter__ = lambda self: self
        resp.__exit__ = lambda self, *a: False
        resp.headers = {
            "Content-Type": content_type,
            "Content-Length": str(content_length),
        }
        return resp
    return opener


class TestValidateFacebookMedia(unittest.TestCase):

    def test_text_only_returns_text_kind(self):
        result = facebook_publisher.validate_facebook_media(_make_snapshot())
        self.assertEqual("text", result["kind"])

    def test_link_only_returns_link_kind(self):
        result = facebook_publisher.validate_facebook_media(
            _make_snapshot(link="https://example.com/promo")
        )
        self.assertEqual("link", result["kind"])
        self.assertEqual("https://example.com/promo", result["link"])

    def test_single_image_passes(self):
        result = facebook_publisher.validate_facebook_media(
            _make_snapshot(media_refs=[_image_ref("https://cdn.example.com/photo.jpg")]),
            opener=_successful_head(),
        )
        self.assertEqual("image", result["kind"])
        self.assertEqual("https://cdn.example.com/photo.jpg", result["imageUrl"])

    def test_multiple_images_rejected(self):
        with self.assertRaises(store.StoreError) as ctx:
            facebook_publisher.validate_facebook_media(
                _make_snapshot(media_refs=[
                    _image_ref("https://cdn.example.com/a.jpg"),
                    _image_ref("https://cdn.example.com/b.jpg"),
                ])
            )
        self.assertEqual(400, ctx.exception.status)
        self.assertIn("one image", str(ctx.exception).lower())

    def test_ftp_scheme_filtered_out_as_non_image(self):
        result = facebook_publisher.validate_facebook_media(
            _make_snapshot(media_refs=[_image_ref("ftp://files.example.com/photo.jpg")])
        )
        self.assertEqual("text", result["kind"])

    def test_private_host_rejected(self):
        with self.assertRaises(store.StoreError) as ctx:
            facebook_publisher.validate_facebook_media(
                _make_snapshot(media_refs=[_image_ref("https://127.0.0.1/photo.jpg")])
            )
        self.assertEqual(400, ctx.exception.status)
        self.assertIn("public", str(ctx.exception).lower())

    def test_localhost_rejected(self):
        with self.assertRaises(store.StoreError) as ctx:
            facebook_publisher.validate_facebook_media(
                _make_snapshot(media_refs=[_image_ref("https://localhost/photo.jpg")])
            )
        self.assertEqual(400, ctx.exception.status)

    def test_bad_extension_rejected(self):
        with self.assertRaises(store.StoreError) as ctx:
            facebook_publisher.validate_facebook_media(
                _make_snapshot(media_refs=[_image_ref("https://cdn.example.com/file.bmp")])
            )
        self.assertEqual(400, ctx.exception.status)
        self.assertIn("JPG", str(ctx.exception))

    def test_oversized_image_rejected(self):
        with self.assertRaises(store.StoreError) as ctx:
            facebook_publisher.validate_facebook_media(
                _make_snapshot(media_refs=[_image_ref("https://cdn.example.com/huge.jpg")]),
                opener=_successful_head(content_length=11 * 1024 * 1024),
            )
        self.assertEqual(400, ctx.exception.status)
        self.assertIn("large", str(ctx.exception).lower())

    def test_bad_content_type_rejected(self):
        with self.assertRaises(store.StoreError) as ctx:
            facebook_publisher.validate_facebook_media(
                _make_snapshot(media_refs=[_image_ref("https://cdn.example.com/file.jpg")]),
                opener=_successful_head(content_type="application/pdf"),
            )
        self.assertEqual(400, ctx.exception.status)

    def test_non_image_kind_ignored(self):
        result = facebook_publisher.validate_facebook_media(
            _make_snapshot(media_refs=[{"kind": "video", "url": "https://cdn.example.com/v.mp4"}])
        )
        self.assertEqual("text", result["kind"])

    def test_png_extension_passes(self):
        result = facebook_publisher.validate_facebook_media(
            _make_snapshot(media_refs=[_image_ref("https://cdn.example.com/photo.png")]),
            opener=_successful_head(content_type="image/png"),
        )
        self.assertEqual("image", result["kind"])

    def test_gif_extension_passes(self):
        result = facebook_publisher.validate_facebook_media(
            _make_snapshot(media_refs=[_image_ref("https://cdn.example.com/anim.gif")]),
            opener=_successful_head(content_type="image/gif"),
        )
        self.assertEqual("image", result["kind"])


if __name__ == "__main__":
    unittest.main()
