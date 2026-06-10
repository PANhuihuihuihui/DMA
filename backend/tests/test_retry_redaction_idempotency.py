import json
import sqlite3
import unittest
from urllib import error, request

from backend.tests.test_fake_publish_lifecycle import ApiCase, assert_no_forbidden_terms


SECRET_FIELDS = [
    "access" + "_token",
    "refresh" + "_token",
    "author" + "ization",
    "coo" + "kie",
    "client" + "_secret",
    "api" + "_key",
    "oauth" + "_payload",
    "provider" + "_raw",
]

SECRET_VALUES = [
    "lp-secret-alpha",
    "lp-secret-beta",
    "lp-secret-gamma",
    "lp-secret-delta",
    "lp-secret-epsilon",
    "lp-secret-zeta",
    "lp-secret-eta",
    "lp-secret-theta",
]


def forbidden_diagnostics_fixture():
    return {
        SECRET_FIELDS[0]: SECRET_VALUES[0],
        "nested": {
            SECRET_FIELDS[1]: SECRET_VALUES[1],
            "headers": {
                SECRET_FIELDS[2]: f"Bearer {SECRET_VALUES[2]}",
                SECRET_FIELDS[3]: f"session={SECRET_VALUES[3]}",
            },
        },
        "provider": {
            SECRET_FIELDS[4]: SECRET_VALUES[4],
            SECRET_FIELDS[5]: SECRET_VALUES[5],
            SECRET_FIELDS[6]: {"raw": SECRET_VALUES[6]},
            SECRET_FIELDS[7]: {"body": SECRET_VALUES[7]},
        },
        "safe": {
            "provider": "fake",
            "errorClass": "platform_transient",
            "nextAction": "retry_publish",
        },
    }


def assert_no_secret_values(test_case, label, payload):
    rendered = json.dumps(payload, sort_keys=True).lower()
    for value in SECRET_VALUES:
        test_case.assertNotIn(value, rendered, f"{label} exposed secret fixture value")


class RetryRedactionIdempotencyTest(ApiCase):
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

    def publish_platform(self, platform):
        approval = self.approve_platform(platform)
        payload = self.send_json("POST", f"/api/v1/approvals/{approval['id']}/publish")
        return approval, payload["job"]

    def retry_job(self, job_id):
        return self.send_json(
            "POST",
            f"/api/v1/publish-jobs/{job_id}/retry",
            {"diagnosticsFixture": forbidden_diagnostics_fixture()},
        )

    def assert_http_error_payload(self, method, path, body, expected_status):
        req = request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body or {}).encode("utf-8"),
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(error.HTTPError) as raised:
            request.urlopen(req, timeout=5)
        self.assertEqual(expected_status, raised.exception.code)
        return json.loads(raised.exception.read().decode("utf-8"))

    def raw_attempt_rows(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in conn.execute("select * from publish_attempts order by attempt_number")]
        finally:
            conn.close()

    def raw_outcome_rows(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in conn.execute("select * from publish_outcomes order by created_at")]
        finally:
            conn.close()

    def assert_redacted_everywhere(self, label, payload):
        assert_no_forbidden_terms(self, label, payload)
        assert_no_secret_values(self, label, payload)
        for row in self.raw_attempt_rows():
            self.assertNotIn("diagnosticsFixture", row["diagnostics_json"])
            assert_no_forbidden_terms(self, f"{label} raw attempt", row)
            assert_no_secret_values(self, f"{label} raw attempt", row)

    def test_retry_needed_job_creates_second_attempt_append_only_with_same_idempotency_key(self):
        approval, first_job = self.publish_platform("tiktok")

        self.assertEqual("retry_needed", first_job["status"])
        self.assertEqual([1], [attempt["attemptNumber"] for attempt in first_job["attempts"]])
        first_attempt = first_job["attempts"][0]
        first_event_ids = [event["id"] for event in first_job["events"]]
        idempotency_key = approval["idempotencyKey"]

        retry_payload = self.retry_job(first_job["id"])
        retried_job = retry_payload["job"]

        self.assertEqual("ok", retry_payload["status"])
        self.assertEqual("published", retried_job["status"])
        self.assertEqual(idempotency_key, retried_job["approvalSnapshot"]["idempotencyKey"])
        self.assertEqual([1, 2], [attempt["attemptNumber"] for attempt in retried_job["attempts"]])
        self.assertEqual(first_attempt["id"], retried_job["attempts"][0]["id"])
        self.assertEqual(first_attempt["traceId"], retried_job["attempts"][0]["traceId"])
        self.assertNotEqual(first_attempt["traceId"], retried_job["attempts"][1]["traceId"])
        self.assertEqual("published", retried_job["attempts"][1]["status"])
        self.assertEqual("manual_retry", retried_job["attempts"][1]["retryClassification"])
        self.assertEqual(first_event_ids, [event["id"] for event in retried_job["events"][: len(first_event_ids)]])
        self.assertEqual(
            ["approved", "queued", "publishing", "failed", "retry_needed", "queued", "publishing", "published"],
            [event["status"] for event in retried_job["events"]],
        )
        self.assertEqual([2], [row["attempt_number"] for row in self.raw_outcome_rows()])
        self.assert_redacted_everywhere("retry payload", retry_payload)

        fetched = self.get_json(f"/api/v1/publish-jobs/{first_job['id']}")
        self.assertEqual([1, 2], [attempt["attemptNumber"] for attempt in fetched["job"]["attempts"]])
        self.assert_redacted_everywhere("retry fetched job", fetched)

    def test_retry_of_published_job_is_safe_conflict_without_duplicate_outcome(self):
        _approval, published_job = self.publish_platform("facebook")

        self.assertEqual("published", published_job["status"])
        error_payload = self.assert_http_error_payload(
            "POST",
            f"/api/v1/publish-jobs/{published_job['id']}/retry",
            {"diagnosticsFixture": forbidden_diagnostics_fixture()},
            409,
        )
        fetched = self.get_json(f"/api/v1/publish-jobs/{published_job['id']}")

        self.assertEqual("published", fetched["job"]["status"])
        self.assertEqual(1, len(fetched["job"]["attempts"]))
        self.assertEqual(1, len(self.raw_outcome_rows()))
        assert_no_forbidden_terms(self, "published retry conflict", error_payload)
        assert_no_secret_values(self, "published retry conflict", error_payload)
        self.assertIn("already published", error_payload["error"]["message"].lower())


if __name__ == "__main__":
    unittest.main()
