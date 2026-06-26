"""
Contract tests for the generation dispatch engine (S01/T05).

Tests three concerns:
  1. Adapter registry contract — get_adapter raises for unknown keys; adapters
     instantiate without env vars at import time.
  2. Job lifecycle — POST /api/v1/generation/jobs with dispatch:false returns
     201 with status=queued and a credit reservation; GET returns the job.
  3. Credit correctness — mock adapter success path settles credits; failure
     path releases credits; balance is correct after each.
"""
import json
import tempfile
import threading
import unittest
import urllib.request
from contextlib import closing
from pathlib import Path
from urllib import error, request as urllib_req

from backend.app.server import create_app
from backend.app import generation_dispatch, store
from backend.app.generation_providers import get_adapter, ADAPTER_REGISTRY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MockSuccessAdapter:
    """Simulates a provider that always succeeds immediately."""

    def submit(self, model_key, prompt, request, settings):
        return "mock_provider_job_success"

    def poll(self, provider_job_id):
        return {
            "status": "succeeded",
            "outputs": [
                {
                    "kind": "video",
                    "storageRef": "https://example.com/video.mp4",
                    "previewRef": "https://example.com/thumb.jpg",
                    "metadata": {"providerJobId": provider_job_id},
                }
            ],
            "diagnostics": {"providerStatus": "completed"},
        }


class MockFailureAdapter:
    """Simulates a provider that always fails immediately."""

    def submit(self, model_key, prompt, request, settings):
        return "mock_provider_job_failure"

    def poll(self, provider_job_id):
        return {
            "status": "failed",
            "failureReason": "mock provider failure",
            "diagnostics": {"providerStatus": "error"},
        }


class MockVideoSuccessAdapter:
    """Simulates a text-to-video provider that always succeeds immediately."""

    def submit(self, model_key, prompt, request, settings):
        return "mock_video_job"

    def poll(self, provider_job_id):
        return {
            "status": "succeeded",
            "outputs": [
                {
                    "kind": "video",
                    "storageRef": "https://example.com/video.mp4",
                    "previewRef": "https://example.com/thumb.jpg",
                    "metadata": {"providerJobId": provider_job_id},
                }
            ],
            "diagnostics": {"providerStatus": "completed"},
        }


class MockUgcVideoSuccessAdapter:
    """Simulates a UGC avatar video provider that always succeeds immediately."""

    def submit(self, model_key, prompt, request, settings):
        return "mock_ugc_video_job"

    def poll(self, provider_job_id):
        return {
            "status": "succeeded",
            "outputs": [
                {
                    "kind": "avatar_video",
                    "storageRef": "https://example.com/avatar.mp4",
                    "previewRef": "https://example.com/avatar_thumb.jpg",
                    "metadata": {"providerJobId": provider_job_id},
                }
            ],
            "diagnostics": {"providerStatus": "completed"},
        }


class MockCarouselSuccessAdapter:
    """Simulates a carousel image provider that succeeds via the poll-based path."""

    def submit(self, model_key, prompt, request, settings):
        assert settings.get("aspectRatio") == "3:4"
        assert request.get("workflowType") == "carousel"
        return "mock_carousel_job"

    def poll(self, provider_job_id):
        outputs = []
        for index, role in enumerate(store.CAROUSEL_SLIDE_ROLES, start=1):
            outputs.append(
                {
                    "kind": "image",
                    "storageRef": f"https://example.com/carousel-{index}.jpg",
                    "previewRef": f"https://example.com/carousel-{index}-thumb.jpg",
                    "metadata": {
                        "providerJobId": provider_job_id,
                        "carouselSlide": {
                            "index": index,
                            "role": role,
                        },
                    },
                }
            )
        return {
            "status": "succeeded",
            "outputs": outputs,
            "diagnostics": {"providerStatus": "completed"},
        }


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
        with urllib_req.urlopen(f"{self.base_url}{path}", timeout=5) as resp:
            return json.loads(resp.read())

    def post_json(self, path, body=None, expected_status=None):
        req = urllib_req.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body or {}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib_req.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read())
        except error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def _submit_video_job(self, dispatch=False):
        """Submit a Sora 2 video job and return (status_code, payload)."""
        return self.post_json(
            "/api/v1/generation/jobs",
            {
                "modelId": store.OPENAI_VIDEO_MODEL_ID,
                "prompt": "A sunny day at a local bakery",
                "dispatch": dispatch,
            },
        )

    def _credit_balance(self):
        return self.get_json("/api/v1/generation/credits")["credits"]["availableCredits"]


# ---------------------------------------------------------------------------
# 1. Adapter registry contract
# ---------------------------------------------------------------------------


class AdapterRegistryContractTest(unittest.TestCase):
    def test_known_adapters_instantiate(self):
        for key in ADAPTER_REGISTRY:
            adapter = get_adapter(key)
            self.assertIsNotNone(adapter)

    def test_get_adapter_raises_for_unknown_key(self):
        with self.assertRaises(KeyError):
            get_adapter("unknown_provider:video")

    def test_openai_video_adapter_exists(self):
        adapter = get_adapter("openai:video")
        self.assertTrue(hasattr(adapter, "submit"))
        self.assertTrue(hasattr(adapter, "poll"))

    def test_heygen_avatar_adapter_exists(self):
        adapter = get_adapter("heygen:avatar_video")
        self.assertTrue(hasattr(adapter, "submit"))
        self.assertTrue(hasattr(adapter, "poll"))

    def test_adapter_instantiates_without_env_vars(self):
        # Adapters must not fail at import or instantiation time — only at call time.
        import os
        saved_openai = os.environ.pop("OPENAI_API_KEY", None)
        saved_heygen = os.environ.pop("HEYGEN_API_KEY", None)
        try:
            adapter_ov = get_adapter("openai:video")
            adapter_hg = get_adapter("heygen:avatar_video")
            self.assertIsNotNone(adapter_ov)
            self.assertIsNotNone(adapter_hg)
        finally:
            if saved_openai is not None:
                os.environ["OPENAI_API_KEY"] = saved_openai
            if saved_heygen is not None:
                os.environ["HEYGEN_API_KEY"] = saved_heygen


# ---------------------------------------------------------------------------
# 2. Job lifecycle (HTTP layer)
# ---------------------------------------------------------------------------


class JobLifecycleTest(ApiCase):
    def test_submit_job_returns_201_with_queued_status(self):
        status, payload = self._submit_video_job(dispatch=False)
        self.assertEqual(201, status)
        job = payload["job"]
        self.assertEqual("queued", job["status"])
        self.assertTrue(job["id"].startswith("generation_job_"))
        self.assertEqual(store.OPENAI_VIDEO_MODEL_ID, job["modelId"])

    def test_submit_job_reserves_credits(self):
        balance_before = self._credit_balance()
        status, payload = self._submit_video_job(dispatch=False)
        self.assertEqual(201, status)
        balance_after = self._credit_balance()
        reserved = payload["job"]["reservedCredits"]
        self.assertGreater(reserved, 0)
        self.assertEqual(balance_before - reserved, balance_after)

    def test_get_job_returns_submitted_job(self):
        _, created = self._submit_video_job(dispatch=False)
        job_id = created["job"]["id"]
        fetched = self.get_json(f"/api/v1/generation/jobs/{job_id}")
        self.assertEqual(job_id, fetched["job"]["id"])
        self.assertEqual("queued", fetched["job"]["status"])

    def test_list_models_includes_sora2_and_heygen(self):
        payload = self.get_json("/api/v1/generation/models")
        model_ids = [m["id"] for m in payload["models"]]
        self.assertIn(store.OPENAI_VIDEO_MODEL_ID, model_ids)
        self.assertIn(store.CCDANCE_AVATAR_MODEL_ID, model_ids)

    def test_heygen_model_is_ready(self):
        payload = self.get_json("/api/v1/generation/models")
        heygen = next(m for m in payload["models"] if m["id"] == store.CCDANCE_AVATAR_MODEL_ID)
        self.assertEqual("ready", heygen["readinessStatus"])

    def test_submit_unknown_model_returns_error(self):
        status, _ = self.post_json(
            "/api/v1/generation/jobs",
            {"modelId": "genmodel_does_not_exist", "prompt": "test", "dispatch": False},
        )
        self.assertIn(status, (400, 404, 409))

    def test_submit_insufficient_credits_returns_error(self):
        # Drain credits by submitting many jobs without dispatch, then expect 409.
        for _ in range(20):
            s, _ = self._submit_video_job(dispatch=False)
            if s != 201:
                break
        # At some point balance should be exhausted.
        for _ in range(5):
            s, payload = self._submit_video_job(dispatch=False)
            if s == 409:
                return
        self.fail("Expected 409 after exhausting credits")


# ---------------------------------------------------------------------------
# 3. Credit ledger correctness (via mock adapters in-process)
# ---------------------------------------------------------------------------


class CreditLedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        # ensure_database runs schema migrations and seeds demo data including credit accounts.
        store.ensure_database(self.db_path)
        self.merchant_id = store.DEMO_MERCHANT_ID
        with closing(store.connect(self.db_path)) as conn:
            self.initial_balance = store.get_generation_credit_summary(conn, self.merchant_id)["availableCredits"]

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_job(self):
        with closing(store.connect(self.db_path)) as conn:
            payload = store.create_generation_job(
                conn,
                self.merchant_id,
                {
                    "modelId": store.OPENAI_VIDEO_MODEL_ID,
                    "prompt": "Test video",
                },
            )
        return payload["job"]["id"], payload["job"]["reservedCredits"]

    def _balance(self):
        with closing(store.connect(self.db_path)) as conn:
            return store.get_generation_credit_summary(conn, self.merchant_id)["availableCredits"]

    def _patch_registry(self, adapter_cls):
        """Temporarily replace the registry entry for openai:video."""
        original = generation_dispatch._PROVIDER_REGISTRY.get("openai:video")
        generation_dispatch._PROVIDER_REGISTRY["openai:video"] = adapter_cls
        return original

    def _restore_registry(self, original):
        if original is None:
            generation_dispatch._PROVIDER_REGISTRY.pop("openai:video", None)
        else:
            generation_dispatch._PROVIDER_REGISTRY["openai:video"] = original

    def test_success_path_settles_credits(self):
        balance_before = self._balance()
        job_id, reserved = self._create_job()
        self.assertEqual(balance_before - reserved, self._balance())

        original = self._patch_registry(MockSuccessAdapter)
        try:
            generation_dispatch._dispatch_job(self.db_path, job_id)
        finally:
            self._restore_registry(original)

        with closing(store.connect(self.db_path)) as conn:
            job = conn.execute("select status from generation_jobs where id = ?", (job_id,)).fetchone()
        self.assertEqual("succeeded", job["status"])
        # After settle, balance should remain at (before - reserved) because
        # settle posts a negative-delta entry equal to reserved.
        self.assertEqual(balance_before - reserved, self._balance())

    def test_failure_path_releases_credits(self):
        balance_before = self._balance()
        job_id, reserved = self._create_job()
        self.assertEqual(balance_before - reserved, self._balance())

        original = self._patch_registry(MockFailureAdapter)
        try:
            generation_dispatch._dispatch_job(self.db_path, job_id)
        finally:
            self._restore_registry(original)

        with closing(store.connect(self.db_path)) as conn:
            job = conn.execute("select status from generation_jobs where id = ?", (job_id,)).fetchone()
        self.assertEqual("failed", job["status"])
        # Release restores the reserved amount.
        self.assertEqual(balance_before, self._balance())

    def test_no_adapter_releases_credits(self):
        """A job with an unregistered provider_key must fail cleanly and release credits."""
        # Inject a job with a fake provider_key by bypassing create_generation_job.
        from backend.app.contracts import new_id, utc_now, json_dumps
        now = utc_now()
        job_id = new_id("generation_job")
        with closing(store.connect(self.db_path)) as conn:
            cost = 180
            balance_before = store.get_generation_credit_summary(conn, self.merchant_id)["availableCredits"]
            conn.execute(
                """
                insert into generation_jobs
                  (id, merchant_id, model_catalog_id, provider_key, model_key, capability,
                   prompt, request_json, settings_json, status, reserved_credits, failure_reason,
                   created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id, self.merchant_id, store.OPENAI_VIDEO_MODEL_ID,
                    "no_such_provider", "no_model", "video",
                    "test", "{}", "{}", "queued", cost, None, now, now,
                ),
            )
            conn.execute(
                """insert into generation_attempts
                   (id, generation_job_id, attempt_number, status, diagnostics_json, created_at, updated_at)
                   values (?, ?, ?, ?, ?, ?, ?)""",
                (new_id("generation_attempt"), job_id, 1, "queued", "{}", now, now),
            )
            store.reserve_generation_credits(conn, self.merchant_id, job_id, cost)
            conn.commit()

        generation_dispatch._dispatch_job(self.db_path, job_id)

        with closing(store.connect(self.db_path)) as conn:
            job = conn.execute("select status from generation_jobs where id = ?", (job_id,)).fetchone()
            balance_after = store.get_generation_credit_summary(conn, self.merchant_id)["availableCredits"]
        self.assertEqual("failed", job["status"])
        self.assertEqual(balance_before, balance_after)


# ---------------------------------------------------------------------------
# 4. Video creative materialization (S03/T03)
# ---------------------------------------------------------------------------


class VideoPackageHandoffTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "workflow.sqlite")
        store.ensure_database(self.db_path)
        self.merchant_id = store.DEMO_MERCHANT_ID

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_video_job(self, model_id):
        with closing(store.connect(self.db_path)) as conn:
            payload = store.create_generation_job(
                conn,
                self.merchant_id,
                {"modelId": model_id, "prompt": "A local bakery on a sunny morning"},
            )
        return payload["job"]["id"]

    def _create_carousel_job(self):
        with closing(store.connect(self.db_path)) as conn:
            payload = store.create_generation_job(
                conn,
                self.merchant_id,
                {
                    "modelId": store.MINIMAX_IMAGE_MODEL_ID,
                    "prompt": "Turn one timely local offer into a five-slide owner-ready carousel.",
                    "workflowType": "carousel",
                    "sourceKind": "idea",
                    "sourceText": "Turn one timely local offer into a five-slide owner-ready carousel.",
                },
            )
        return payload["job"]["id"]

    def _patch_and_dispatch(self, registry_key, adapter_cls, job_id):
        original = generation_dispatch._PROVIDER_REGISTRY.get(registry_key)
        generation_dispatch._PROVIDER_REGISTRY[registry_key] = adapter_cls
        try:
            generation_dispatch._dispatch_job(self.db_path, job_id)
        finally:
            if original is None:
                generation_dispatch._PROVIDER_REGISTRY.pop(registry_key, None)
            else:
                generation_dispatch._PROVIDER_REGISTRY[registry_key] = original

    def test_dispatch_video_job_creates_generated_creative(self):
        job_id = self._create_video_job(store.OPENAI_VIDEO_MODEL_ID)
        self._patch_and_dispatch("openai:video", MockVideoSuccessAdapter, job_id)

        with closing(store.connect(self.db_path)) as conn:
            job_row = conn.execute(
                "select * from generation_jobs where id = ?", (job_id,)
            ).fetchone()
            serialized = store.serialize_generation_job(conn, job_row)
            creative_row = conn.execute(
                "select * from generated_creatives where merchant_id = ?",
                (self.merchant_id,),
            ).fetchone()

        self.assertEqual("video", serialized.get("workflowType"))
        self.assertIsNotNone(serialized.get("creativeId"))
        self.assertIsNotNone(creative_row)
        self.assertEqual(self.merchant_id, creative_row["merchant_id"])

    def test_dispatch_carousel_job_materializes_generated_creative(self):
        job_id = self._create_carousel_job()
        self._patch_and_dispatch("minimax:image", MockCarouselSuccessAdapter, job_id)

        with closing(store.connect(self.db_path)) as conn:
            job_row = conn.execute(
                "select * from generation_jobs where id = ?", (job_id,)
            ).fetchone()
            serialized = store.serialize_generation_job(conn, job_row)
            creative_id = serialized.get("creativeId")
            creative_row = conn.execute(
                "select * from generated_creatives where id = ?",
                (creative_id,),
            ).fetchone()
            asset_rows = conn.execute(
                "select * from creative_media_assets where creative_id = ? order by created_at, id",
                (creative_id,),
            ).fetchall()

        self.assertEqual("carousel", serialized.get("workflowType"))
        self.assertEqual("3:4", serialized.get("slideCompositions")[0]["layout"]["aspectRatio"])
        self.assertIsNotNone(creative_row)
        self.assertEqual("carousel", creative_row["format"])
        self.assertEqual(5, len(asset_rows))

    def test_dispatch_ugc_video_job_creates_ugc_creative(self):
        job_id = self._create_video_job(store.CCDANCE_AVATAR_MODEL_ID)
        self._patch_and_dispatch("heygen:avatar_video", MockUgcVideoSuccessAdapter, job_id)

        with closing(store.connect(self.db_path)) as conn:
            job_row = conn.execute(
                "select * from generation_jobs where id = ?", (job_id,)
            ).fetchone()
            serialized = store.serialize_generation_job(conn, job_row)
            creative_id = serialized.get("creativeId")
            creative_row = conn.execute(
                "select * from generated_creatives where id = ?",
                (creative_id,),
            ).fetchone()

        self.assertIsNotNone(creative_id)
        self.assertIsNotNone(creative_row)
        self.assertEqual(self.merchant_id, creative_row["merchant_id"])
        self.assertEqual("ugc_video", creative_row["format"])

    def test_video_creative_has_video_media_asset(self):
        job_id = self._create_video_job(store.OPENAI_VIDEO_MODEL_ID)
        self._patch_and_dispatch("openai:video", MockVideoSuccessAdapter, job_id)

        with closing(store.connect(self.db_path)) as conn:
            job_row = conn.execute(
                "select * from generation_jobs where id = ?", (job_id,)
            ).fetchone()
            serialized = store.serialize_generation_job(conn, job_row)
            creative_id = serialized.get("creativeId")
            asset_row = conn.execute(
                "select * from creative_media_assets where creative_id = ?",
                (creative_id,),
            ).fetchone()

        self.assertIsNotNone(asset_row)
        self.assertEqual("video", asset_row["asset_type"])
        self.assertEqual("https://example.com/video.mp4", asset_row["storage_ref"])
