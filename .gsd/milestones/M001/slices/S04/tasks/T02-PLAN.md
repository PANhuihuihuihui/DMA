---
estimated_steps: 13
estimated_files: 1
skills_used: []
---

# T02: Created backend/scripts/smoke_s04.py with 5 checks (3 PASS, 2 SKIP); smoke_s04_report.json written successfully.

Why: The milestone deliverable requires a 'smoke diagnostics file captured' artifact and evidence that the full pipeline runs end-to-end. The smoke script is the single runnable entry point: it validates all pre-release gates and writes backend/scripts/smoke_s04_report.json. When real API keys are absent (expected in CI), provider checks are SKIP and the script exits 0. When OPENAI_API_KEY or HEYGEN_API_KEY are present, it dispatches real generation jobs and records credit deltas.

Do:
1. Create backend/scripts/ directory (by writing the file) and backend/scripts/smoke_s04.py.
2. Import: store, generation_dispatch, threading, json, os, tempfile, closing, time, sys; from backend.app.server import create_app; from pathlib import Path; from contextlib import closing.
3. Each check is a function returning dict(name=str, status='PASS'|'SKIP'|'FAIL', detail=str, elapsed_ms=int).
4. Check CATALOG_COSTS: create temp DB with store.ensure_database, open conn, query both model rows by OPENAI_VIDEO_MODEL_ID and CCDANCE_AVATAR_MODEL_ID, assert credit_cost==180 and credit_cost==220 respectively. FAIL with detail if either value differs.
5. Check INSUFFICIENT_BALANCE: create temp DB, call store.create_generation_job with a fresh merchant_id='test_merchant_zero' (no ledger entries), catch store.StoreError and assert status==409 and 'Insufficient' in message. FAIL if no error or wrong status.
6. Check MODEL_API_SURFACE: start create_app on port 0 in a daemon thread, GET /api/v1/generation/models, verify creditCost field present and correct (180 for Sora 2, 220 for HeyGen). Shutdown server. FAIL if missing or wrong.
7. Check SORA2_REAL_GEN: if os.environ.get('OPENAI_API_KEY') is not set, return SKIP. Else create temp DB, record balance before, call store.create_generation_job for OPENAI_VIDEO_MODEL_ID with DEMO_MERCHANT_ID, call generation_dispatch.start_async_dispatch, poll store.get_generation_job every 10s until status in ('succeeded','failed') or 300s elapsed. Record terminal_status, credit_delta=(balance_before - balance_after), failure_reason. PASS if terminal_status=='succeeded', FAIL otherwise.
8. Check HEYGEN_REAL_GEN: same as above using HEYGEN_API_KEY env var and CCDANCE_AVATAR_MODEL_ID.
9. Write backend/scripts/smoke_s04_report.json: {timestamp, checks: [...], summary: {total, pass, skip, fail}}.
10. Print each check result to stdout. Exit sys.exit(0) if fail==0 else sys.exit(1).

Done when: python3 backend/scripts/smoke_s04.py exits 0 and backend/scripts/smoke_s04_report.json exists with CATALOG_COSTS, INSUFFICIENT_BALANCE, MODEL_API_SURFACE as PASS.

## Inputs

- `backend/app/store.py`
- `backend/app/generation_dispatch.py`
- `backend/app/generation_providers/openai_adapter.py`
- `backend/app/generation_providers/heygen_adapter.py`
- `backend/app/server.py`
- `backend/tests/test_generation_dispatch.py`

## Expected Output

- `backend/scripts/smoke_s04.py`
- `backend/scripts/smoke_s04_report.json`

## Verification

python3 backend/scripts/smoke_s04.py && test -f backend/scripts/smoke_s04_report.json
