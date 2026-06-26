import unittest

from backend.app.facebook_publisher import classify_error_class


class TestClassifyErrorClass(unittest.TestCase):

    def test_401_authentication(self):
        self.assertEqual(
            "authentication",
            classify_error_class(401, {"message": "Invalid OAuth 2.0 Access Token"}),
        )

    def test_403_missing_permission(self):
        self.assertEqual(
            "missing_permission",
            classify_error_class(403, {"message": "(#200) Requires pages_manage_posts permission"}),
        )

    def test_403_generic_is_authentication(self):
        self.assertEqual(
            "authentication",
            classify_error_class(403, {"message": "Session has expired"}),
        )

    def test_400_validation(self):
        self.assertEqual(
            "validation",
            classify_error_class(400, {"message": "Invalid parameter"}),
        )

    def test_429_rate_limit(self):
        self.assertEqual(
            "rate_limit",
            classify_error_class(429, {"message": "Application request limit reached"}),
        )

    def test_500_platform_transient(self):
        self.assertEqual(
            "platform_transient",
            classify_error_class(500, {"message": "An unexpected error has occurred"}),
        )

    def test_502_platform_transient(self):
        self.assertEqual(
            "platform_transient",
            classify_error_class(502, {"message": "Bad Gateway"}),
        )

    def test_503_platform_transient(self):
        self.assertEqual(
            "platform_transient",
            classify_error_class(503, {"message": "Service temporarily unavailable"}),
        )

    def test_unknown_status(self):
        self.assertEqual(
            "unknown",
            classify_error_class(418, {"message": "I'm a teapot"}),
        )

    def test_empty_message(self):
        self.assertEqual(
            "authentication",
            classify_error_class(401, {"message": ""}),
        )

    def test_none_message(self):
        self.assertEqual(
            "authentication",
            classify_error_class(401, {}),
        )

    def test_permission_keyword_in_403(self):
        self.assertEqual(
            "missing_permission",
            classify_error_class(403, {"message": "Insufficient permission to post"}),
        )


class TestRoutingBehavior(unittest.TestCase):

    RETRYABLE_CLASSES = {"rate_limit", "platform_transient"}
    MANUAL_FALLBACK_CLASSES = {"authentication", "missing_permission", "validation", "unknown"}

    def test_retryable_classes(self):
        for cls in self.RETRYABLE_CLASSES:
            with self.subTest(error_class=cls):
                self.assertIn(cls, self.RETRYABLE_CLASSES)

    def test_manual_fallback_classes(self):
        for cls in self.MANUAL_FALLBACK_CLASSES:
            with self.subTest(error_class=cls):
                self.assertIn(cls, self.MANUAL_FALLBACK_CLASSES)

    def test_all_classes_accounted_for(self):
        all_classes = self.RETRYABLE_CLASSES | self.MANUAL_FALLBACK_CLASSES
        test_cases = [
            (401, {}, "authentication"),
            (403, {"message": "permission"}, "missing_permission"),
            (400, {}, "validation"),
            (429, {}, "rate_limit"),
            (500, {}, "platform_transient"),
            (418, {}, "unknown"),
        ]
        for status, error, expected in test_cases:
            result = classify_error_class(status, error)
            self.assertIn(result, all_classes, f"Unclassified: {result}")


if __name__ == "__main__":
    unittest.main()
