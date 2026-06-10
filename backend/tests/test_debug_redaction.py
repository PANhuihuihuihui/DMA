import json
import unittest

from backend.tests.test_fake_publish_lifecycle import ApiCase, assert_no_forbidden_terms
from backend.tests.test_retry_redaction_idempotency import (
    SECRET_VALUES,
    assert_no_secret_values,
    forbidden_diagnostics_fixture,
)


class DebugRedactionTest(ApiCase):
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

    def assert_support_row_contract(self, row):
        for key in [
            "merchant",
            "platform",
            "jobStatus",
            "attemptCount",
            "latestTraceId",
            "errorClass",
            "updatedAt",
            "nextAction",
            "approver",
            "draftVersion",
            "mediaRefs",
            "tokenBoundaryRef",
            "approvalSnapshotSummary",
            "attempts",
            "events",
            "redactedDiagnostics",
        ]:
            self.assertIn(key, row)

        self.assertEqual("Northstar Local Growth", row["merchant"]["name"])
        self.assertEqual("Karen Li", row["approver"]["name"])
        self.assertTrue(row["approver"]["email"].endswith("@example.com"))
        self.assertEqual(1, row["draftVersion"]["versionNumber"])
        self.assertTrue(row["draftVersion"]["id"].startswith("version_"))
        self.assertTrue(row["mediaRefs"])
        self.assertEqual("redacted", row["tokenBoundaryRef"]["visibility"])
        self.assertNotIn("secretRef", row["tokenBoundaryRef"])
        self.assertNotIn("credentialFingerprint", row["tokenBoundaryRef"])
        self.assertEqual(row["attemptCount"], len(row["attempts"]))
        self.assertTrue(row["latestTraceId"].startswith("trace_"))
        self.assertTrue(row["updatedAt"])
        self.assertTrue(row["events"])
        self.assertIn(row["jobStatus"], ["published", "retry_needed"])
        self.assertIn(row["nextAction"], ["none", "retry_publish"])
        self.assertIn(row["errorClass"], ["none", "platform_transient"])
        self.assertEqual(row["latestTraceId"], row["attempts"][-1]["traceId"])
        self.assertEqual(row["redactedDiagnostics"], row["attempts"][-1]["diagnostics"])

        summary = row["approvalSnapshotSummary"]
        self.assertEqual(row["platform"], summary["platform"])
        self.assertEqual(row["approver"]["name"], summary["approver"]["name"])
        self.assertEqual(row["draftVersion"]["id"], summary["draftVersionId"])
        self.assertTrue(summary["idempotencyKeySuffix"])
        self.assertTrue(summary["mediaRefs"])
        self.assertEqual("redacted", summary["tokenBoundaryRef"]["visibility"])

    def test_debug_publish_jobs_return_redacted_support_diagnostics(self):
        _facebook_approval, facebook_job = self.publish_platform("facebook")
        _tiktok_approval, tiktok_job = self.publish_platform("tiktok")

        self.assertEqual("published", facebook_job["status"])
        self.assertEqual("retry_needed", tiktok_job["status"])

        payload = self.get_json("/api/v1/debug/publish-jobs")

        self.assertEqual("ok", payload["status"])
        self.assertIn("publishJobs", payload)
        rows = payload["publishJobs"]
        self.assertEqual(2, len(rows))

        by_platform = {row["platform"]: row for row in rows}
        self.assertEqual("published", by_platform["facebook"]["jobStatus"])
        self.assertEqual("retry_needed", by_platform["tiktok"]["jobStatus"])
        self.assertEqual(1, by_platform["facebook"]["attemptCount"])
        self.assertEqual(1, by_platform["tiktok"]["attemptCount"])

        for row in rows:
            self.assert_support_row_contract(row)
        assert_no_forbidden_terms(self, "debug payload", payload)

    def test_debug_publish_jobs_redact_retry_provider_diagnostics(self):
        _approval, tiktok_job = self.publish_platform("tiktok")
        retry_payload = self.retry_job(tiktok_job["id"])
        self.assertEqual("published", retry_payload["job"]["status"])

        payload = self.get_json("/api/v1/debug/publish-jobs")
        rows = payload["publishJobs"]
        self.assertEqual(1, len(rows))
        row = rows[0]

        self.assertEqual("published", row["jobStatus"])
        self.assertEqual(2, row["attemptCount"])
        self.assertEqual([1, 2], [attempt["attemptNumber"] for attempt in row["attempts"]])
        self.assertEqual("none", row["errorClass"])
        self.assertEqual("none", row["nextAction"])
        self.assert_support_row_contract(row)
        assert_no_forbidden_terms(self, "debug retry payload", payload)
        assert_no_secret_values(self, "debug retry payload", payload)

        rendered = json.dumps(payload, sort_keys=True).lower()
        for value in SECRET_VALUES:
            self.assertNotIn(value, rendered)


if __name__ == "__main__":
    unittest.main()
