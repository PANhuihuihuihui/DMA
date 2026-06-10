import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib import error, request

from backend.app.server import create_app


FORBIDDEN_TERMS = [
    "access" + "_token",
    "refresh" + "_token",
    "author" + "ization",
    "coo" + "kie",
    "client" + "_secret",
    "api" + "_key",
    "oauth" + "_payload",
    "provider" + "_raw",
    "facebook.com",
    "graph.facebook.com",
    "tiktok.com",
    "postiz",
    "browser_session",
    "selenium",
]


def assert_no_forbidden_terms(test_case, label, payload):
    rendered = json.dumps(payload, sort_keys=True).lower()
    for term in FORBIDDEN_TERMS:
        test_case.assertNotIn(term, rendered, f"{label} exposed {term}")


class ApiCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        self.server = create_app(host="127.0.0.1", port=0, db_path=self.db_path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def get_json(self, path):
        with request.urlopen(f"{self.base_url}{path}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def send_json(self, method, path, body=None):
        req = request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body or {}).encode("utf-8"),
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def assert_http_error(self, method, path, body, expected_statuses):
        req = request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body or {}).encode("utf-8"),
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(error.HTTPError) as raised:
            request.urlopen(req, timeout=5)
        self.assertIn(raised.exception.code, expected_statuses)


class FakePublishLifecycleTest(ApiCase):
    def approve_platform(self, platform):
        workflow = self.get_json("/api/v1/workflow")
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == platform)
        return self.send_json(
            "POST",
            f"/api/v1/drafts/{draft['id']}/approve",
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
            },
        )["approval"]

    def assert_event_contract(self, events, expected_statuses):
        self.assertEqual(expected_statuses, [event["status"] for event in events])
        for index, event in enumerate(events, start=1):
            self.assertIn("id", event)
            self.assertIn("timestamp", event)
            self.assertIn("sourceActor", event)
            self.assertIn("attemptNumber", event)
            self.assertIn("status", event)
            self.assertIn("summary", event)
            self.assertEqual(1, event["attemptNumber"])
            self.assertTrue(event["summary"])
            self.assertGreaterEqual(index, 1)

    def assert_attempt_contract(self, attempt, expected_status):
        self.assertEqual(1, attempt["attemptNumber"])
        self.assertEqual(expected_status, attempt["status"])
        self.assertTrue(attempt["traceId"].startswith("trace_"))
        self.assertTrue(attempt["requestDigest"].startswith("sha256:"))
        self.assertIn("startedAt", attempt)
        self.assertIn("finishedAt", attempt)
        self.assertIn("retryClassification", attempt)
        self.assertIn("diagnostics", attempt)

    def test_publish_requires_approval_id(self):
        self.assert_http_error("POST", "/api/v1/approvals/publish", {}, {404})
        self.assert_http_error("POST", "/api/v1/approvals/not_an_approval/publish", {}, {400, 404, 409})

    def test_facebook_fake_publish_records_published_lifecycle(self):
        approval = self.approve_platform("facebook")

        payload = self.send_json("POST", f"/api/v1/approvals/{approval['id']}/publish")

        self.assertEqual("ok", payload["status"])
        self.assertEqual("Queue fake publish", payload["ctaCopy"])
        self.assertEqual("published", payload["job"]["status"])
        self.assertEqual(approval["id"], payload["job"]["approvalId"])
        self.assertEqual("facebook", payload["job"]["platform"])
        self.assertTrue(payload["job"]["approvalSnapshot"]["mediaRefs"])
        self.assert_event_contract(
            payload["job"]["events"],
            ["approved", "queued", "publishing", "published"],
        )
        self.assertEqual(1, len(payload["job"]["attempts"]))
        self.assert_attempt_contract(payload["job"]["attempts"][0], "published")
        assert_no_forbidden_terms(self, "facebook publish", payload)

        fetched = self.get_json(f"/api/v1/publish-jobs/{payload['job']['id']}")
        self.assertEqual(payload["job"]["id"], fetched["job"]["id"])
        self.assert_event_contract(
            fetched["job"]["events"],
            ["approved", "queued", "publishing", "published"],
        )
        assert_no_forbidden_terms(self, "facebook job", fetched)

    def test_tiktok_fake_publish_records_failed_retry_needed_lifecycle(self):
        approval = self.approve_platform("tiktok")

        payload = self.send_json("POST", f"/api/v1/approvals/{approval['id']}/publish")

        self.assertEqual("ok", payload["status"])
        self.assertEqual("Queue fake publish", payload["ctaCopy"])
        self.assertEqual("retry_needed", payload["job"]["status"])
        self.assertEqual("tiktok", payload["job"]["platform"])
        self.assert_event_contract(
            payload["job"]["events"],
            ["approved", "queued", "publishing", "failed", "retry_needed"],
        )
        self.assertEqual(1, len(payload["job"]["attempts"]))
        self.assert_attempt_contract(payload["job"]["attempts"][0], "failed")
        self.assertEqual("automatic_retry_needed", payload["job"]["attempts"][0]["retryClassification"])
        assert_no_forbidden_terms(self, "tiktok publish", payload)


if __name__ == "__main__":
    unittest.main()
