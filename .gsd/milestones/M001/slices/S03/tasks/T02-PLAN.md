---
estimated_steps: 5
estimated_files: 1
skills_used: []
---

# T02: Wired materialize_video_package into both _dispatch_job (async) and dispatch_generation_job (sync) succeeded branches so video jobs produce a generated_creative record on success.

Why: store.py now has the function but nothing calls it from the dispatch engine; without wiring, no creative is created when a video job succeeds.

Do:
1. In _dispatch_job (async path, succeeded branch): replace the bare _insert_output loop with a version that captures the returned output_id strings. After all outputs are inserted, if job["capability"] in store.VIDEO_CAPABILITIES and output_ids: load first output row via conn.execute("select * from generation_outputs where id = ?", (output_ids[0],)).fetchone(); if row is not None call store.materialize_video_package(conn, job["merchant_id"], job, row). Log at INFO on success.
2. In dispatch_generation_job (sync/test path): after the carousel materialization block (if request_payload.get("workflowType") == "carousel"), add elif capability in store.VIDEO_CAPABILITIES and output_rows: store.materialize_video_package(conn, merchant_id, job_row, output_rows[0]).

Done when: python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short exits 0; a video job dispatched synchronously via dispatch_generation_job with a mock adapter produces a generated_creative record in DB (verified by T03 tests).

## Inputs

- `backend/app/generation_dispatch.py`
- `backend/app/store.py`

## Expected Output

- `backend/app/generation_dispatch.py`

## Verification

python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short
