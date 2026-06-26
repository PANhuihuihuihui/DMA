---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Created generation_dispatch.py skeleton — server now starts without ImportError

Create backend/app/generation_dispatch.py exporting the two functions server.py calls: start_async_dispatch(db_path, job_id) and retry_generation_job(db_path, merchant_id, job_id, dispatch). start_async_dispatch spawns a threading.Thread targeting a _run_dispatch worker; retry_generation_job creates a new attempt and optionally dispatches. Goal is to unblock server startup and establish the module boundary. No real provider calls yet.

## Inputs

- `backend/app/server.py lines 179,193 — exact function signatures required`
- `backend/app/store.py — create_generation_job, get_generation_job, serialize_generation_job`

## Expected Output

- `backend/app/generation_dispatch.py`

## Verification

cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -c 'from backend.app import generation_dispatch; print("ok")'
