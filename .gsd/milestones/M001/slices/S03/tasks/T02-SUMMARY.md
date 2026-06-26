---
id: T02
parent: S03
milestone: M001
key_files:
  - backend/app/generation_dispatch.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T06:04:48.263Z
blocker_discovered: false
---

# T02: Wired materialize_video_package into both _dispatch_job (async) and dispatch_generation_job (sync) succeeded branches

**Wired materialize_video_package into both _dispatch_job (async) and dispatch_generation_job (sync) succeeded branches**

## What Happened

Read generation_dispatch.py and store.py to understand the existing carousel wiring pattern. In _dispatch_job (async succeeded branch): replaced the bare _insert_output loop with a version that collects output_ids, then after all outputs are inserted checks if job["capability"] in store.VIDEO_CAPABILITIES and output_ids, fetches the first output row, and calls store.materialize_video_package(conn, job["merchant_id"], job, first_row) with an INFO log on success. In dispatch_generation_job (sync succeeded branch): added elif capability in store.VIDEO_CAPABILITIES and output_rows: store.materialize_video_package(conn, merchant_id, job_row, output_rows[0]); conn.commit() after the existing carousel block. Both paths follow the same structural pattern as the carousel materialization. Materialization placed before status/credit updates within the same conn block for atomicity — consistent with carousel pattern. Guarded by `if first_row is not None` in async path to avoid crash on output-less edge case.

## Verification

Ran python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short — 15 passed in 7.92s, exit 0. The existing CreditLedgerTest.test_success_path_settles_credits now exercises materialize_video_package via the async path. No regressions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short` | 0 | 15 passed | 8116ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/app/generation_dispatch.py`
