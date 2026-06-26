# S01: Dispatch Engine and Provider Adapters

**Goal:** Backend server starts cleanly, generation_dispatch.py drives async job lifecycle with Sora 2 and HeyGen adapters, credits settle on success and release on failure, contract tests pass.
**Demo:** Backend server starts without ImportError. `pytest tests/ -x -q` passes adapter contract tests and job lifecycle state transition tests. A POST /api/v1/generation/jobs with dispatch:false returns a job record with status=queued and credits reserved. A manual dispatch call drives a simulated job to succeeded and confirms credits settled; a simulated failure confirms credits released.

## Must-Haves

- pytest backend/tests/ -x -q passes with no ImportError. POST /api/v1/generation/jobs (dispatch:false) → 201 with status=queued and credits reserved. Simulated dispatch drives job to succeeded → credits settled. Simulated failure → credits released.

## Proof Level

- This slice proves: Contract + Integration: pytest contract tests pass; server starts without ImportError; POST /api/v1/generation/jobs with dispatch:false returns queued job with credits reserved; dispatch:true drives a simulated run to terminal state with correct credit settlement.

## Integration Closure

generation_dispatch exports exactly start_async_dispatch(db_path, job_id) and retry_generation_job(db_path, merchant_id, job_id, dispatch) — matching the two call sites in server.py lines 179 and 193. Provider adapters implement a shared contract (submit/poll/cancel). Credit settle/release calls the existing store functions; no new schema changes.

## Verification

- Dispatch logs job_id, provider_key, attempt_number, status transitions, and error class on each state change to stdout. Failed jobs log normalized error type + credit_release confirmation.

## Tasks

- [x] **T01: Created generation_dispatch.py skeleton — server now starts without ImportError** `est:30m`
  Create backend/app/generation_dispatch.py exporting the two functions server.py calls: start_async_dispatch(db_path, job_id) and retry_generation_job(db_path, merchant_id, job_id, dispatch). start_async_dispatch spawns a threading.Thread targeting a _run_dispatch worker; retry_generation_job creates a new attempt and optionally dispatches. Goal is to unblock server startup and establish the module boundary. No real provider calls yet.
  - Files: `backend/app/generation_dispatch.py`
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -c 'from backend.app import generation_dispatch; print("ok")'

- [x] **T02: Created generation_providers package with OpenAI Sora 2 video adapter and adapter registry** `est:1h`
  Create backend/app/generation_providers/__init__.py and backend/app/generation_providers/openai_adapter.py implementing the OpenAI Sora 2 text-to-video adapter. Shared contract: submit(job_record, settings) -> attempt_id, poll(attempt_id) -> {status, output_url?, error?}, cancel(attempt_id). submit calls POST /v1/video/generations via direct HTTP with OPENAI_API_KEY from env. poll calls GET /v1/video/generations/{id}. Normalized ProviderError on failure. get_adapter(provider_key) factory in __init__.py.
  - Files: `backend/app/generation_providers/__init__.py`, `backend/app/generation_providers/openai_adapter.py`
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -c 'from backend.app.generation_providers import get_adapter; a = get_adapter("openai_video"); print(type(a).__name__)'

- [x] **T03: Created HeyGen avatar adapter and updated catalog seed from ccdance_stub to heygen:ready** `est:1h`
  Create backend/app/generation_providers/heygen_adapter.py implementing HeyGen v2 UGC avatar adapter. submit calls POST /v2/video/generate with avatar_id, script, voiceover from HEYGEN_API_KEY env. poll calls GET /v1/video_status.get?video_id={id}. Update store.py seed_generation_model_catalog: replace provider_key 'ccdance_stub' with 'heygen' and readiness_status 'preview' with 'ready' for the avatar model entry.
  - Files: `backend/app/generation_providers/heygen_adapter.py`, `backend/app/store.py`
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -c 'from backend.app.generation_providers import get_adapter; a = get_adapter("heygen"); print(type(a).__name__)'

- [x] **T04: Dispatch loop fully wired: submit→exponential-poll→settle/release with adapter registry** `est:1.5h`
  Implement the _run_dispatch worker in generation_dispatch.py. Load job from store, read model catalog for provider_key and credit_cost, call get_adapter(provider_key).submit(), poll at exponential backoff (2s→4s→8s→30s cap, max 60 attempts). On succeeded: settle_generation_credits + update job status. On failed/timeout: release_generation_credits + update job status to failed with normalized error. Log each state transition. retry_generation_job creates a new generation_attempt row and conditionally re-dispatches.
  - Files: `backend/app/generation_dispatch.py`
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -c 'from backend.app import generation_dispatch; import inspect; print(inspect.signature(generation_dispatch.retry_generation_job))'

- [x] **T05: 15 contract tests pass; full 168-test suite green** `est:1.5h`
  Write backend/tests/test_generation_dispatch.py. (1) Adapter contract: get_adapter raises for unknown provider_key; adapters instantiate without API keys at import time. (2) Job lifecycle: POST /api/v1/generation/jobs dispatch:false returns 201 status=queued with credit reservation; GET job returns it. (3) Credit correctness: mock adapter success path settles credits; failure path releases credits; balance correct after each. Use ApiCase pattern from test_fake_publish_lifecycle.py. Mock adapter via monkeypatching get_adapter.
  - Files: `backend/tests/test_generation_dispatch.py`
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -m pytest backend/tests/test_generation_dispatch.py -v 2>&1 | tail -20

## Files Likely Touched

- backend/app/generation_dispatch.py
- backend/app/generation_providers/__init__.py
- backend/app/generation_providers/openai_adapter.py
- backend/app/generation_providers/heygen_adapter.py
- backend/app/store.py
- backend/tests/test_generation_dispatch.py
