import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib import error, request

from backend.app import sessions, store, tiktok_publisher
from backend.app.server import create_app
from backend.tests.test_fake_publish_lifecycle import assert_no_forbidden_terms


class AdminConsoleStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def create_viewer_session(self):
        now = store.utc_now()
        self.conn.execute(
            "insert into users (id, merchant_id, name, email, role, created_at) values (?, ?, ?, ?, ?, ?)",
            ("user_viewer", store.DEMO_MERCHANT_ID, "Viewer User", "viewer@example.com", "viewer", now),
        )
        return sessions.create_session(self.conn, "user_viewer", store.DEMO_MERCHANT_ID)

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

    def test_resolve_operator_accepts_owner_and_localhost_allowance(self):
        owner = store.resolve_operator(self.conn, store.DEMO_SESSION_ID)
        self.assertEqual("owner", owner["role"])
        localhost = store.resolve_operator(self.conn, None, allow_localhost=True)
        self.assertEqual(store.DEMO_USER_ID, localhost["userId"])

    def test_resolve_operator_rejects_non_operator_role(self):
        token = self.create_viewer_session()
        with self.assertRaises(store.StoreError) as raised:
            store.resolve_operator(self.conn, token)
        self.assertEqual(403, raised.exception.status)

    def test_mark_publish_job_support_path_adds_operator_event(self):
        approval = self.approve_tiktok()
        payload = tiktok_publisher.queue_tiktok_publish(self.conn, approval["id"], {"simulateFailure": "scope"})

        store.mark_publish_job_support_path(self.conn, payload["job"]["id"], "Coordinate manual posting with merchant.")

        job = store.get_serialized_publish_job(self.conn, payload["job"]["id"])
        self.assertEqual("manual_support", job["events"][-1]["status"])
        self.assertEqual("operator", job["events"][-1]["sourceActor"])
        self.assertIn("manual support path", job["events"][-1]["summary"].lower())


class AdminConsoleApiTest(unittest.TestCase):
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

    def approve_platform(self, platform):
        workflow = self.json_request("GET", "/api/v1/workflow")
        draft = next(item for item in workflow["platformDrafts"] if item["platform"] == platform)
        body = {
            "draftVersionId": draft["currentVersion"]["id"],
            "confirmation": "APPROVE_EXACT_VERSION",
            "approver": {"name": "Karen Li", "email": "karen@example.com"},
        }
        if platform == "tiktok":
            info = self.json_request("GET", "/api/v1/tiktok/creator-info")["creatorInfo"]
            body["tiktokConfirmations"] = {
                "creatorInfoVersion": info["version"],
                "privacyLevel": "PUBLIC_TO_EVERYONE",
                "disclosureReviewed": True,
                "interactionReviewed": True,
                "allowComment": True,
            }
        return self.json_request("POST", f"/api/v1/drafts/{draft['id']}/approve", body)["approval"]

    def create_fake_retry_job(self):
        approval = self.approve_platform("tiktok")
        return self.json_request("POST", f"/api/v1/approvals/{approval['id']}/publish")["job"]

    def create_manual_fallback_job(self):
        approval = self.approve_platform("tiktok")
        return self.json_request(
            "POST",
            f"/api/v1/approvals/{approval['id']}/publish-tiktok",
            {"simulateFailure": "scope"},
        )["job"]

    def test_admin_routes_return_redacted_jobs_with_localhost_allowance(self):
        job = self.create_manual_fallback_job()

        payload = self.json_request("GET", "/api/v1/admin/publish-jobs")
        detail = self.json_request("GET", f"/api/v1/admin/publish-jobs/{job['id']}")

        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["publishJobs"])
        self.assertEqual(job["id"], detail["job"]["id"])
        self.assertEqual("manual_fallback_required", detail["job"]["jobStatus"])
        assert_no_forbidden_terms(self, "admin publish jobs", payload)
        assert_no_forbidden_terms(self, "admin publish job detail", detail)

    def test_admin_routes_reject_non_operator_sessions(self):
        self.create_fake_retry_job()
        viewer_token = self.create_viewer_session()
        headers = {"X-LocalPilot-Session": viewer_token}

        self.assert_http_error("GET", "/api/v1/admin/publish-jobs", 403, headers=headers)

    def test_admin_retry_reuses_existing_retry_behavior(self):
        job = self.create_fake_retry_job()

        payload = self.json_request("POST", f"/api/v1/admin/publish-jobs/{job['id']}/retry", {})

        self.assertEqual("ok", payload["status"])
        self.assertEqual("published", payload["job"]["jobStatus"])
        self.assertEqual(2, payload["job"]["attemptCount"])
        assert_no_forbidden_terms(self, "admin retry payload", payload)

    def test_admin_mark_support_records_operator_event(self):
        job = self.create_manual_fallback_job()

        payload = self.json_request(
            "POST",
            f"/api/v1/admin/publish-jobs/{job['id']}/mark-support",
            {"note": "Coordinate manual posting with the merchant."},
        )

        self.assertEqual("ok", payload["status"])
        self.assertEqual("manual_support", payload["job"]["events"][-1]["status"])
        self.assertEqual("operator", payload["job"]["events"][-1]["sourceActor"])
        assert_no_forbidden_terms(self, "admin mark-support payload", payload)


if __name__ == "__main__":
    unittest.main()
