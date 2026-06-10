import json
import sqlite3
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
]


def assert_no_forbidden_terms(test_case, payload):
    rendered = json.dumps(payload, sort_keys=True).lower()
    for term in FORBIDDEN_TERMS:
        test_case.assertNotIn(term, rendered)


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

    def send_json(self, method, path, body):
        req = request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def assert_http_error(self, method, path, body, status):
        req = request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(error.HTTPError) as raised:
            request.urlopen(req, timeout=5)
        self.assertEqual(status, raised.exception.code)


class PublishApprovalContractTest(ApiCase):
    def test_workflow_includes_media_assets_and_safe_channel_refs(self):
        workflow = self.get_json("/api/v1/workflow")

        self.assertEqual("ok", workflow["status"])
        self.assertIn("campaigns", workflow)
        self.assertGreaterEqual(len(workflow["connectedChannels"]), 2)
        self.assertGreaterEqual(len(workflow["platformDrafts"]), 2)

        media_refs = [
            media
            for draft in workflow["platformDrafts"]
            for version in draft["versions"]
            for media in version["mediaRefs"]
        ]
        self.assertTrue(media_refs)
        for media in media_refs:
            self.assertEqual("server_media_ref", media["storageMode"])
            self.assertIn("mediaAssetId", media)
            self.assertIn("storageRef", media)

        for channel in workflow["connectedChannels"]:
            self.assertIn("tokenBoundaryRef", channel)
            self.assertNotIn("secretRef", channel["tokenBoundaryRef"])
            assert_no_forbidden_terms(self, channel)

        assert_no_forbidden_terms(self, workflow)

        with sqlite3.connect(self.db_path) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "select name from sqlite_master where type = 'table'"
                )
            }
            self.assertIn("media_assets", tables)
            self.assertIn("provider_token_boundaries", tables)
            self.assertGreater(
                conn.execute("select count(*) from media_assets").fetchone()[0],
                0,
            )

    def test_approval_snapshot_freezes_exact_draft_version_contract(self):
        workflow = self.get_json("/api/v1/workflow")
        facebook_draft = next(
            draft for draft in workflow["platformDrafts"] if draft["platform"] == "facebook"
        )
        version = facebook_draft["currentVersion"]

        approval = self.send_json(
            "POST",
            f"/api/v1/drafts/{facebook_draft['id']}/approve",
            {
                "draftVersionId": version["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
            },
        )

        snapshot = approval["approval"]["snapshot"]
        self.assertEqual("approved", approval["approval"]["status"])
        self.assertEqual("facebook", snapshot["platform"])
        self.assertEqual(version["id"], snapshot["draftVersionId"])
        self.assertEqual(version["versionNumber"], snapshot["versionNumber"])
        self.assertEqual(version["caption"], snapshot["caption"])
        self.assertEqual(version["body"], snapshot["body"])
        self.assertEqual(version["cta"], snapshot["cta"])
        self.assertTrue(snapshot["mediaRefs"])
        self.assertIn("connectedChannelRef", snapshot)
        self.assertIn("tokenBoundaryRef", snapshot)
        self.assertIn("providerPayloadSummary", snapshot)
        self.assertIn("disclosureSettingsRef", snapshot)
        self.assertEqual({"name": "Karen Li", "email": "karen@example.com"}, snapshot["approver"])
        self.assertIn("approvedAt", snapshot)
        self.assertIn("createdAt", snapshot)
        self.assertTrue(snapshot["idempotencyKey"].startswith("lp:facebook:"))
        assert_no_forbidden_terms(self, approval)

        updated = self.send_json(
            "PATCH",
            f"/api/v1/drafts/{facebook_draft['id']}",
            {
                "caption": "Updated caption for a later review cycle.",
                "body": "This edit must create a new draft version, not mutate the snapshot.",
                "cta": "Book now",
            },
        )
        self.assertNotEqual(version["id"], updated["draft"]["currentVersion"]["id"])

        refreshed = self.get_json("/api/v1/workflow")
        frozen = next(
            item
            for item in refreshed["approvals"]
            if item["id"] == approval["approval"]["id"]
        )
        self.assertEqual(version["caption"], frozen["snapshot"]["caption"])
        self.assertEqual(version["id"], frozen["snapshot"]["draftVersionId"])
        self.assertNotEqual(
            updated["draft"]["currentVersion"]["caption"],
            frozen["snapshot"]["caption"],
        )

    def test_approval_rejects_missing_confirmation_wrong_version_and_bad_media(self):
        workflow = self.get_json("/api/v1/workflow")
        draft = workflow["platformDrafts"][0]
        version = draft["currentVersion"]

        self.assert_http_error(
            "POST",
            f"/api/v1/drafts/{draft['id']}/approve",
            {
                "draftVersionId": version["id"],
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
            },
            400,
        )
        self.assert_http_error(
            "POST",
            f"/api/v1/drafts/{draft['id']}/approve",
            {
                "draftVersionId": "version-does-not-match",
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
            },
            409,
        )
        self.assert_http_error(
            "POST",
            f"/api/v1/drafts/{draft['id']}/approve",
            {
                "draftVersionId": version["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "mediaRefs": ["missing-media-ref"],
            },
            400,
        )


if __name__ == "__main__":
    unittest.main()
