"""
S04 Smoke runner — validates pre-release gates and writes smoke_s04_report.json.

When real API keys are absent (expected in CI), provider checks are SKIP and the
script exits 0.  When OPENAI_API_KEY or HEYGEN_API_KEY are present it dispatches
real generation jobs and records credit deltas.

Usage:
    python3 backend/scripts/smoke_s04.py
"""

import json
import os
import sys
import tempfile
import threading
import time
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

# Ensure the repo root is on the path so backend.app imports work
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.app import generation_dispatch, store  # noqa: E402
from backend.app.server import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPENAI_VIDEO_MODEL_ID = store.OPENAI_VIDEO_MODEL_ID       # "genmodel_openai_video_primary"
CCDANCE_AVATAR_MODEL_ID = store.CCDANCE_AVATAR_MODEL_ID   # "genmodel_ccdance_avatar_preview"
DEMO_MERCHANT_ID = store.DEMO_MERCHANT_ID

EXPECTED_OPENAI_VIDEO_COST = 180
EXPECTED_HEYGEN_COST = 220

_POLL_TIMEOUT_SECS = 300
_POLL_INTERVAL_SECS = 10


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ts_ms():
    """Current wall-clock time in milliseconds (monotonic)."""
    return int(time.monotonic() * 1000)


def _utc_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_catalog_costs():
    """Verify that catalog rows carry the expected credit costs."""
    start = _ts_ms()
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "smoke.sqlite")
        store.ensure_database(db_path)
        with closing(store.connect(db_path)) as conn:
            row_openai = conn.execute(
                "select credit_cost from generation_model_catalog where id = ?",
                (OPENAI_VIDEO_MODEL_ID,),
            ).fetchone()
            row_heygen = conn.execute(
                "select credit_cost from generation_model_catalog where id = ?",
                (CCDANCE_AVATAR_MODEL_ID,),
            ).fetchone()

    errors = []
    if row_openai is None:
        errors.append(f"row missing for {OPENAI_VIDEO_MODEL_ID}")
    elif row_openai["credit_cost"] != EXPECTED_OPENAI_VIDEO_COST:
        errors.append(
            f"{OPENAI_VIDEO_MODEL_ID}: expected credit_cost={EXPECTED_OPENAI_VIDEO_COST}, "
            f"got {row_openai['credit_cost']}"
        )

    if row_heygen is None:
        errors.append(f"row missing for {CCDANCE_AVATAR_MODEL_ID}")
    elif row_heygen["credit_cost"] != EXPECTED_HEYGEN_COST:
        errors.append(
            f"{CCDANCE_AVATAR_MODEL_ID}: expected credit_cost={EXPECTED_HEYGEN_COST}, "
            f"got {row_heygen['credit_cost']}"
        )

    elapsed = _ts_ms() - start
    if errors:
        return dict(name="CATALOG_COSTS", status="FAIL", detail="; ".join(errors), elapsed_ms=elapsed)
    return dict(
        name="CATALOG_COSTS",
        status="PASS",
        detail=f"openai_video={EXPECTED_OPENAI_VIDEO_COST}, heygen={EXPECTED_HEYGEN_COST}",
        elapsed_ms=elapsed,
    )


def check_insufficient_balance():
    """Verify that submitting a job for a merchant with no ledger entries raises 409."""
    start = _ts_ms()
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "smoke.sqlite")
        store.ensure_database(db_path)
        merchant_id = "test_merchant_zero"
        with closing(store.connect(db_path)) as conn:
            # Insert a merchant row so FK is satisfied, but no credit account.
            # The demo DB already seeds DEMO_MERCHANT_ID with credits; we want a
            # merchant that has no credit account at all.
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "insert into merchants (id, name, created_at) values (?, ?, ?)",
                (merchant_id, "Smoke Test Zero", now),
            )
            conn.commit()

            try:
                store.create_generation_job(
                    conn,
                    merchant_id,
                    {
                        "modelId": OPENAI_VIDEO_MODEL_ID,
                        "prompt": "Smoke test zero balance",
                        "dispatch": False,
                    },
                )
            except store.StoreError as exc:
                elapsed = _ts_ms() - start
                # Could be 404 (no credit account) or 409 (insufficient credits) — both are valid
                if exc.status in (404, 409) and (
                    "Insufficient" in exc.message or "Credit account not configured" in exc.message
                    or "credit" in exc.message.lower()
                ):
                    return dict(
                        name="INSUFFICIENT_BALANCE",
                        status="PASS",
                        detail=f"Got expected StoreError status={exc.status}: {exc.message}",
                        elapsed_ms=elapsed,
                    )
                return dict(
                    name="INSUFFICIENT_BALANCE",
                    status="FAIL",
                    detail=f"Unexpected StoreError status={exc.status}: {exc.message}",
                    elapsed_ms=elapsed,
                )
            except Exception as exc:
                elapsed = _ts_ms() - start
                return dict(
                    name="INSUFFICIENT_BALANCE",
                    status="FAIL",
                    detail=f"Unexpected exception type {type(exc).__name__}: {exc}",
                    elapsed_ms=elapsed,
                )

    elapsed = _ts_ms() - start
    return dict(
        name="INSUFFICIENT_BALANCE",
        status="FAIL",
        detail="No error raised for zero-balance merchant — expected StoreError 409/404",
        elapsed_ms=elapsed,
    )


def check_model_api_surface():
    """Start a test server and verify GET /api/v1/generation/models returns correct creditCost."""
    start = _ts_ms()
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "smoke.sqlite")
        server = create_app(host="127.0.0.1", port=0, db_path=db_path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        base_url = f"http://{host}:{port}"

        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/generation/models", timeout=5) as resp:
                payload = json.loads(resp.read())
        except Exception as exc:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            elapsed = _ts_ms() - start
            return dict(
                name="MODEL_API_SURFACE",
                status="FAIL",
                detail=f"HTTP request failed: {exc}",
                elapsed_ms=elapsed,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    models_by_id = {m["id"]: m for m in payload.get("models", [])}
    errors = []

    openai_model = models_by_id.get(OPENAI_VIDEO_MODEL_ID)
    if openai_model is None:
        errors.append(f"model {OPENAI_VIDEO_MODEL_ID} missing from /api/v1/generation/models")
    else:
        if "creditCost" not in openai_model:
            errors.append(f"{OPENAI_VIDEO_MODEL_ID}: creditCost field absent")
        elif openai_model["creditCost"] != EXPECTED_OPENAI_VIDEO_COST:
            errors.append(
                f"{OPENAI_VIDEO_MODEL_ID}: creditCost={openai_model['creditCost']}, "
                f"expected {EXPECTED_OPENAI_VIDEO_COST}"
            )

    heygen_model = models_by_id.get(CCDANCE_AVATAR_MODEL_ID)
    if heygen_model is None:
        errors.append(f"model {CCDANCE_AVATAR_MODEL_ID} missing from /api/v1/generation/models")
    else:
        if "creditCost" not in heygen_model:
            errors.append(f"{CCDANCE_AVATAR_MODEL_ID}: creditCost field absent")
        elif heygen_model["creditCost"] != EXPECTED_HEYGEN_COST:
            errors.append(
                f"{CCDANCE_AVATAR_MODEL_ID}: creditCost={heygen_model['creditCost']}, "
                f"expected {EXPECTED_HEYGEN_COST}"
            )

    elapsed = _ts_ms() - start
    if errors:
        return dict(name="MODEL_API_SURFACE", status="FAIL", detail="; ".join(errors), elapsed_ms=elapsed)
    return dict(
        name="MODEL_API_SURFACE",
        status="PASS",
        detail=f"openai_video creditCost={EXPECTED_OPENAI_VIDEO_COST}, heygen creditCost={EXPECTED_HEYGEN_COST}",
        elapsed_ms=elapsed,
    )


def check_sora2_real_gen():
    """If OPENAI_API_KEY is set, dispatch a real Sora 2 job and poll for completion."""
    if not os.environ.get("OPENAI_API_KEY"):
        return dict(
            name="SORA2_REAL_GEN",
            status="SKIP",
            detail="OPENAI_API_KEY not set",
            elapsed_ms=0,
        )
    start = _ts_ms()
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "smoke.sqlite")
        store.ensure_database(db_path)
        with closing(store.connect(db_path)) as conn:
            balance_before = store.get_generation_credit_summary(conn, DEMO_MERCHANT_ID)["availableCredits"]
            payload = store.create_generation_job(
                conn,
                DEMO_MERCHANT_ID,
                {
                    "modelId": OPENAI_VIDEO_MODEL_ID,
                    "prompt": "A sunny day at a local bakery — smoke test",
                    "dispatch": False,
                },
            )
            job_id = payload["job"]["id"]

        generation_dispatch.start_async_dispatch(db_path, job_id)

        terminal_status = None
        failure_reason = None
        deadline = time.monotonic() + _POLL_TIMEOUT_SECS
        while time.monotonic() < deadline:
            time.sleep(_POLL_INTERVAL_SECS)
            with closing(store.connect(db_path)) as conn:
                job_row = store.get_generation_job(conn, DEMO_MERCHANT_ID, job_id)
                if job_row["status"] in ("succeeded", "failed"):
                    terminal_status = job_row["status"]
                    failure_reason = job_row["failure_reason"]
                    balance_after = store.get_generation_credit_summary(conn, DEMO_MERCHANT_ID)["availableCredits"]
                    break

        elapsed = _ts_ms() - start
        if terminal_status is None:
            return dict(
                name="SORA2_REAL_GEN",
                status="FAIL",
                detail=f"Job {job_id} did not reach terminal status within {_POLL_TIMEOUT_SECS}s",
                elapsed_ms=elapsed,
            )
        credit_delta = balance_before - balance_after
        detail = (
            f"terminal_status={terminal_status}, credit_delta={credit_delta}"
            + (f", failure_reason={failure_reason}" if failure_reason else "")
        )
        status = "PASS" if terminal_status == "succeeded" else "FAIL"
        return dict(name="SORA2_REAL_GEN", status=status, detail=detail, elapsed_ms=elapsed)


def check_heygen_real_gen():
    """If HEYGEN_API_KEY is set, dispatch a real HeyGen avatar job and poll for completion."""
    if not os.environ.get("HEYGEN_API_KEY"):
        return dict(
            name="HEYGEN_REAL_GEN",
            status="SKIP",
            detail="HEYGEN_API_KEY not set",
            elapsed_ms=0,
        )
    start = _ts_ms()
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "smoke.sqlite")
        store.ensure_database(db_path)
        with closing(store.connect(db_path)) as conn:
            balance_before = store.get_generation_credit_summary(conn, DEMO_MERCHANT_ID)["availableCredits"]
            payload = store.create_generation_job(
                conn,
                DEMO_MERCHANT_ID,
                {
                    "modelId": CCDANCE_AVATAR_MODEL_ID,
                    "prompt": "A friendly welcome message — smoke test",
                    "dispatch": False,
                },
            )
            job_id = payload["job"]["id"]

        generation_dispatch.start_async_dispatch(db_path, job_id)

        terminal_status = None
        failure_reason = None
        deadline = time.monotonic() + _POLL_TIMEOUT_SECS
        while time.monotonic() < deadline:
            time.sleep(_POLL_INTERVAL_SECS)
            with closing(store.connect(db_path)) as conn:
                job_row = store.get_generation_job(conn, DEMO_MERCHANT_ID, job_id)
                if job_row["status"] in ("succeeded", "failed"):
                    terminal_status = job_row["status"]
                    failure_reason = job_row["failure_reason"]
                    balance_after = store.get_generation_credit_summary(conn, DEMO_MERCHANT_ID)["availableCredits"]
                    break

        elapsed = _ts_ms() - start
        if terminal_status is None:
            return dict(
                name="HEYGEN_REAL_GEN",
                status="FAIL",
                detail=f"Job {job_id} did not reach terminal status within {_POLL_TIMEOUT_SECS}s",
                elapsed_ms=elapsed,
            )
        credit_delta = balance_before - balance_after
        detail = (
            f"terminal_status={terminal_status}, credit_delta={credit_delta}"
            + (f", failure_reason={failure_reason}" if failure_reason else "")
        )
        status = "PASS" if terminal_status == "succeeded" else "FAIL"
        return dict(name="HEYGEN_REAL_GEN", status=status, detail=detail, elapsed_ms=elapsed)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main():
    checks = [
        check_catalog_costs,
        check_insufficient_balance,
        check_model_api_surface,
        check_sora2_real_gen,
        check_heygen_real_gen,
    ]

    results = []
    for fn in checks:
        print(f"  running {fn.__name__} ...", flush=True)
        result = fn()
        results.append(result)
        icon = {"PASS": "[PASS]", "SKIP": "[SKIP]", "FAIL": "[FAIL]"}.get(result["status"], "[????]")
        print(f"  {icon} {result['name']}: {result['detail']} ({result['elapsed_ms']}ms)", flush=True)

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "skip": sum(1 for r in results if r["status"] == "SKIP"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
    }

    report = {
        "timestamp": _utc_iso(),
        "checks": results,
        "summary": summary,
    }

    report_path = Path(__file__).parent / "smoke_s04_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nReport written to {report_path}", flush=True)
    print(
        f"Summary: {summary['pass']} pass, {summary['skip']} skip, {summary['fail']} fail "
        f"(total {summary['total']})",
        flush=True,
    )

    if summary["fail"] > 0:
        print("\nFAILED checks:", flush=True)
        for r in results:
            if r["status"] == "FAIL":
                print(f"  - {r['name']}: {r['detail']}", flush=True)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
