"""
Pre-release smoke tests for catalog credit costs and credit gating (S04/T01).

Tests three concerns:
  1. CatalogCostTest — Sora 2 and HeyGen rows are seeded with the expected
     credit_cost, readiness_status, capability, model_key, and provider_key.
  2. ModelApiSurfaceTest — GET /api/v1/generation/models exposes creditCost
     for both models in the HTTP response.
  3. InsufficientBalanceTest — create_generation_job raises StoreError(409)
     with the exact message 'Insufficient generation credits.' when a merchant
     has no ledger entries (zero balance).
"""
import tempfile
import threading
import unittest
import json
import urllib.request as urllib_req
from contextlib import closing
from pathlib import Path
from urllib import error

from backend.app import store
from backend.app.server import create_app


# ---------------------------------------------------------------------------
# 1. Catalog cost values (store layer)
# ---------------------------------------------------------------------------


class CatalogCostTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "catalog.sqlite")
        store.ensure_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _get_model_row(self, model_id):
        with closing(store.connect(self.db_path)) as conn:
            row = conn.execute(
                "select * from generation_model_catalog where id = ?", (model_id,)
            ).fetchone()
        self.assertIsNotNone(row, f"Model row not found for id={model_id}")
        return row

    def test_sora2_credit_cost_is_180(self):
        row = self._get_model_row(store.OPENAI_VIDEO_MODEL_ID)
        self.assertEqual(180, row["credit_cost"])

    def test_sora2_readiness_status_is_ready(self):
        row = self._get_model_row(store.OPENAI_VIDEO_MODEL_ID)
        self.assertEqual("ready", row["readiness_status"])

    def test_sora2_capability_is_video(self):
        row = self._get_model_row(store.OPENAI_VIDEO_MODEL_ID)
        self.assertEqual("video", row["capability"])

    def test_sora2_model_key(self):
        row = self._get_model_row(store.OPENAI_VIDEO_MODEL_ID)
        self.assertEqual("sora-2", row["model_key"])

    def test_sora2_provider_key(self):
        row = self._get_model_row(store.OPENAI_VIDEO_MODEL_ID)
        self.assertEqual("openai", row["provider_key"])

    def test_heygen_credit_cost_is_220(self):
        row = self._get_model_row(store.CCDANCE_AVATAR_MODEL_ID)
        self.assertEqual(220, row["credit_cost"])

    def test_heygen_readiness_status_is_ready(self):
        row = self._get_model_row(store.CCDANCE_AVATAR_MODEL_ID)
        self.assertEqual("ready", row["readiness_status"])

    def test_heygen_capability_is_avatar_video(self):
        row = self._get_model_row(store.CCDANCE_AVATAR_MODEL_ID)
        self.assertEqual("avatar_video", row["capability"])

    def test_heygen_model_key(self):
        row = self._get_model_row(store.CCDANCE_AVATAR_MODEL_ID)
        self.assertEqual("heygen-avatar", row["model_key"])

    def test_heygen_provider_key(self):
        row = self._get_model_row(store.CCDANCE_AVATAR_MODEL_ID)
        self.assertEqual("heygen", row["provider_key"])


# ---------------------------------------------------------------------------
# 2. Models API surface (HTTP layer)
# ---------------------------------------------------------------------------


class ModelApiSurfaceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "api.sqlite")
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

    def _get_json(self, path):
        with urllib_req.urlopen(f"{self.base_url}{path}", timeout=5) as resp:
            return json.loads(resp.read())

    def test_models_endpoint_exposes_sora2_credit_cost(self):
        payload = self._get_json("/api/v1/generation/models")
        sora2 = next(
            (m for m in payload["models"] if m["id"] == store.OPENAI_VIDEO_MODEL_ID),
            None,
        )
        self.assertIsNotNone(sora2, "Sora 2 model not found in /api/v1/generation/models")
        self.assertEqual(180, sora2["creditCost"])

    def test_models_endpoint_exposes_heygen_credit_cost(self):
        payload = self._get_json("/api/v1/generation/models")
        heygen = next(
            (m for m in payload["models"] if m["id"] == store.CCDANCE_AVATAR_MODEL_ID),
            None,
        )
        self.assertIsNotNone(heygen, "HeyGen model not found in /api/v1/generation/models")
        self.assertEqual(220, heygen["creditCost"])


# ---------------------------------------------------------------------------
# 3. Insufficient balance gating (store layer)
# ---------------------------------------------------------------------------


class InsufficientBalanceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "gating.sqlite")
        store.ensure_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_zero_balance_merchant_gets_409_with_correct_message(self):
        """A fresh merchant_id with no ledger entries has zero balance; job creation must raise 409."""
        fresh_merchant_id = "merchant_fresh_no_credits"
        with closing(store.connect(self.db_path)) as conn:
            # Insert the merchant row first (FK requirement), then a credit account
            # with zero monthly_credits and no ledger entries → balance = 0.
            from backend.app.contracts import new_id, utc_now
            now = utc_now()
            conn.execute(
                "insert or ignore into merchants values (?, ?, ?)",
                (fresh_merchant_id, "Fresh Test Merchant", now),
            )
            conn.execute(
                """
                insert or ignore into credit_accounts
                  (id, merchant_id, plan_name, monthly_credits, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (new_id("credit_account"), fresh_merchant_id, "No Credits", 0, now, now),
            )
            conn.commit()

            with self.assertRaises(store.StoreError) as ctx:
                store.create_generation_job(
                    conn,
                    fresh_merchant_id,
                    {
                        "modelId": store.OPENAI_VIDEO_MODEL_ID,
                        "prompt": "A test video with no credits",
                    },
                )

        exc = ctx.exception
        self.assertEqual(409, exc.status)
        self.assertIn("Insufficient generation credits", exc.message)
