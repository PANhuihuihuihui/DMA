import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib import error, request

from backend.app import sessions, store, tiktok_publisher
from backend.app.server import create_app
from backend.tests.test_fake_publish_lifecycle import assert_no_forbidden_terms


FULL_ELIGIBILITY = {"appAuditApproved": True, "scopesGranted": True}


class EvidenceExportStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def approve_tiktok(self):
        workflow = store.get_workflow(self.conn)
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == "tiktok")
        info = store.get_tiktok_creator_info(self.conn, draft["connectedChannelId"])
        return store.approve_draft(
            self.conn,
            draft["id"],
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "tiktokConfirmations": {
                    "creatorInfoVersion": info["version"],
                    "privacyLevel": "PUBLIC_TO_EVERYONE",
                    "disclosureReviewed": True,
                    "interactionReviewed": True,
                    "allowComment": True,
                },
            },
        )["approval"]

    def test_build_publish_job_evidence_returns_redacted_bundle(self):
        approval = self.approve_tiktok()
        payload = tiktok_publisher.queue_tiktok_publish(
            self.conn,
            approval["id"],
            {"publishMode": "direct_post", "directPostEligibility": FULL_ELIGIBILITY},
        )

        evidence = store.build_publish_job_evidence(self.conn, payload["job"]["id"])

        self.assertIn("job", evidence)
        self.assertIn("appReview", evidence)
        self.assertIn("exportedAt", evidence)
        self.assertEqual("direct_post", evidence["appReview"]["route"])
        self.assertEqual("direct_post", evidence["appReview"]["deliveryMode"])
        self.assertTrue(evidence["appReview"]["directPost"]["eligible"])
        self.assertEqual("PUBLIC_TO_EVERYONE", evidence["appReview"]["tiktokConfirmations"]["privacyLevel"])
        assert_no_forbidden_terms(self, "evidence bundle", evidence)

    def test_build_publish_job_evidence_missing_job_is_404(self):
        with self.assertRaises(store.StoreError) as raised:
            store.build_publish_job_evidence(self.conn, "publish_job_missing")
        self.assertEqual(404, raised.exception.status)


class EvidenceExportApiTest(unittest.TestCase):
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

    def json_request(self, method, path, body=None, headers=None):
        data = None
        request_headers = {"Accept": "application/json", **(headers or {})}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        req = request.Request(f"{self.base_url}{path}", data=data, method=method, headers=request_headers)
        with request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def assert_http_error(self, method, path, expected_status, body=None, headers=None):
        data = None
        request_headers = {"Accept": "application/json", **(headers or {})}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        req = request.Request(f"{self.base_url}{path}", data=data, method=method, headers=request_headers)
        with self.assertRaises(error.HTTPError) as raised:
            request.urlopen(req, timeout=5)
        self.assertEqual(expected_status, raised.exception.code)

    def create_viewer_session(self):
        conn = store.connect(self.db_path)
        try:
            now = store.utc_now()
            conn.execute(
                "insert into users (id, merchant_id, name, email, role, created_at) values (?, ?, ?, ?, ?, ?)",
                ("user_viewer", store.DEMO_MERCHANT_ID, "Viewer User", "viewer@example.com", "viewer", now),
            )
            token = sessions.create_session(conn, "user_viewer", store.DEMO_MERCHANT_ID)
        finally:
            conn.close()
        return token

    def approve_tiktok(self):
        workflow = self.json_request("GET", "/api/v1/workflow")
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == "tiktok")
        info = self.json_request("GET", "/api/v1/tiktok/creator-info")["creatorInfo"]
        return self.json_request(
            "POST",
            f"/api/v1/drafts/{draft['id']}/approve",
            {
                "draftVersionId": draft["currentVersion"]["id"],
                "confirmation": "APPROVE_EXACT_VERSION",
                "approver": {"name": "Karen Li", "email": "karen@example.com"},
                "tiktokConfirmations": {
                    "creatorInfoVersion": info["version"],
                    "privacyLevel": "PUBLIC_TO_EVERYONE",
                    "disclosureReviewed": True,
                    "interactionReviewed": True,
                    "allowComment": True,
                },
            },
        )["approval"]

    def create_direct_post_job(self):
        approval = self.approve_tiktok()
        return self.json_request(
            "POST",
            f"/api/v1/approvals/{approval['id']}/publish-tiktok",
            {"publishMode": "direct_post", "directPostEligibility": FULL_ELIGIBILITY},
        )["job"]

    def test_admin_evidence_endpoint_returns_redacted_bundle(self):
        job = self.create_direct_post_job()

        payload = self.json_request("GET", f"/api/v1/admin/publish-jobs/{job['id']}/evidence")

        self.assertEqual("ok", payload["status"])
        self.assertEqual(job["id"], payload["evidence"]["job"]["id"])
        self.assertEqual("direct_post", payload["evidence"]["appReview"]["route"])
        assert_no_forbidden_terms(self, "admin evidence payload", payload)

    def test_admin_evidence_endpoint_rejects_non_operator(self):
        job = self.create_direct_post_job()
        viewer_token = self.create_viewer_session()
        headers = {"X-LocalPilot-Session": viewer_token}

        self.assert_http_error("GET", f"/api/v1/admin/publish-jobs/{job['id']}/evidence", 403, headers=headers)


if __name__ == "__main__":
    unittest.main()
