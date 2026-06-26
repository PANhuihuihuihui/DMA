---
id: T02
parent: S03
milestone: M001
key_files:
  - backend/app/generation_dispatch.py
key_decisions:
  - Materialization placed before status/credit updates within the same conn block so DB writes are atomic — consistent with carousel pattern
  - Guarded by `if first_row is not None` in async path to avoid crash on output-less edge case
duration: 
verification_result: passed
completed_at: 2026-06-26T03:24:07.757Z
blocker_discovered: false
---

# T02: Wired materialize_video_package into both _dispatch_job (async) and dispatch_generation_job (sync) succeeded branches so video jobs produce a generated_creative record on success.

**Wired materialize_video_package into both _dispatch_job (async) and dispatch_generation_job (sync) succeeded branches so video jobs produce a generated_creative record on success.**

## What Happened

Read generation_dispatch.py and store.py to understand the existing carousel wiring pattern. In _dispatch_job (async succeeded branch, lines 193-212): replaced the bare _insert_output loop with a version that collects output_ids, then after all outputs are inserted checks if job["capability"] in store.VIDEO_CAPABILITIES and output_ids, fetches the first output row, and calls store.materialize_video_package(conn, job["merchant_id"], job, first_row) with an INFO log on success. In dispatch_generation_job (sync succeeded branch, lines 331-345): added elif capability in store.VIDEO_CAPABILITIES and output_rows: store.materialize_video_package(conn, merchant_id, job_row, output_rows[0]); conn.commit() after the existing carousel block. Both paths follow the same structural pattern as the carousel materialization. All 15 existing tests in test_generation_dispatch.py pass, including the credit-ledger success path which uses OPENAI_VIDEO_MODEL_ID (capability="video") and now exercises the new materialization code path.

## Verification

Ran python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short — 15 passed in 7.92s, exit 0. The existing CreditLedgerTest.test_success_path_settles_credits now exercises materialize_video_package via the async path (uses openai:video MockSuccessAdapter). No regressions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short` | 0 | 15 passed | 8116ms |

## Deviations

None.

## Known Issues

None. T03 will add explicit tests asserting a generated_creative record exists after sync dispatch of a video job.

## Files Created/Modified

- `backend/app/generation_dispatch.py`
