---
id: T01
parent: S01
milestone: M001
key_files:
  - backend/app/generation_dispatch.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T00:25:58.665Z
blocker_discovered: false
---

# T01: Created generation_dispatch.py skeleton — server now starts without ImportError

**Created generation_dispatch.py skeleton — server now starts without ImportError**

## What Happened

Created backend/app/generation_dispatch.py exporting the two functions server.py requires: start_async_dispatch(db_path, job_id) and retry_generation_job(db_path, merchant_id, job_id, dispatch). The module defines the full dispatch loop skeleton: _run_dispatch spawns via threading.Thread, _dispatch_job loads the job, looks up the provider adapter from _PROVIDER_REGISTRY (empty until T02/T03), and runs the submit→poll→settle/release lifecycle with exponential backoff (2s→30s cap). Credit release on failure calls store.release_generation_credits; credit settle on success calls store.settle_generation_credits. Job and attempt status transitions update generation_jobs and generation_attempts tables directly via SQL. retry_generation_job inserts a new attempt row, resets job status to queued, and optionally dispatches. Provider registry is empty; any job dispatched now will fail cleanly with "no adapter registered" and release credits — safe stub behavior.

## Verification

python3 -c 'from backend.app import generation_dispatch; print("ok")' → ok; python3 -c 'from backend.app.server import create_app; print("server importable")' → server importable

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -c 'from backend.app import generation_dispatch; print("ok")'` | 0 | module imports cleanly | 320ms |
| 2 | `python3 -c 'from backend.app.server import create_app; print("server importable")'` | 0 | server no longer fails at startup | 410ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/app/generation_dispatch.py`
