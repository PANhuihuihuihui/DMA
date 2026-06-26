---
id: S01
parent: M001
milestone: M001
provides:
  - generation_dispatch module with start_async_dispatch and retry_generation_job
  - OpenAI Sora 2 provider adapter (openai:video)
  - HeyGen UGC avatar provider adapter (heygen:avatar_video)
  - HeyGen model in catalog at readiness=ready
  - Contract tests: adapter factory, job lifecycle, credit ledger
requires:
  []
affects:
  []
key_files:
  - backend/app/generation_dispatch.py
  - backend/app/generation_providers/__init__.py
  - backend/app/generation_providers/openai_adapter.py
  - backend/app/generation_providers/heygen_adapter.py
  - backend/app/store.py
  - backend/tests/test_generation_dispatch.py
key_decisions: []
patterns_established:
  - Adapter registry keyed by '{provider_key}:{capability}' composite — avoids collisions when one vendor covers multiple content types
  - credit settle/release always commits independently — never rely on outer transaction to flush ledger entries
  - dispatch_generation_job() synchronous path for legacy carousel adapter interface; start_async_dispatch() for the video/avatar async path
observability_surfaces:
  - none
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-06-26T00:34:28.899Z
blocker_discovered: false
---

# S01: Dispatch Engine and Provider Adapters

**Backend server starts cleanly; async dispatch engine, Sora 2 + HeyGen adapters, and 15 contract tests all pass**

## What Happened

S01 delivered the entire generation dispatch layer that was blocking server startup. Five tasks completed:

T01 created generation_dispatch.py with the full async dispatch skeleton: threading.Thread worker, exponential backoff poll loop (2s→30s cap, 900s wall-clock timeout), credit settle on success, credit release on failure, and start_async_dispatch / retry_generation_job exported to match server.py's exact call sites.

T02 created the generation_providers package with ADAPTER_REGISTRY keyed by "{provider_key}:{capability}" composites (provider_key alone is not unique — "openai" covers both image and video models). OpenAIVideoAdapter submits to POST /v1/video/generations and polls GET /v1/video/generations/{id}, normalizing OpenAI status strings to the dispatch engine's running/succeeded/failed shape. The dispatch module imports ADAPTER_REGISTRY at module load time so adapters register automatically.

T03 created HeyGenAvatarAdapter targeting POST /v2/video/generate + GET /v1/video_status.get, updated store.py's seed_generation_model_catalog to change the CCDANCE_AVATAR_MODEL_ID entry from provider_key="ccdance_stub"/readiness_status="preview" to provider_key="heygen"/readiness_status="ready". The seed uses UPDATE ON CONFLICT so existing databases pick up the change on next startup.

T04 verified the full dispatch loop was correct and fixed a missing conn.commit() after release_generation_credits in _release_on_failure, which was causing credit release writes to be lost.

T05 wrote 15 contract tests covering adapter registry instantiation, HTTP job lifecycle (submit/reserve/get), and credit ledger correctness (success settles, failure releases, unregistered provider fails cleanly). During testing, discovered test_phase3_workspace.py had been written anticipating a dispatch_generation_job() synchronous function for the Phase 11 carousel path — implemented this as a separate function using the legacy adapter interface that Phase 11 tests expect.

## Verification

python3 -m pytest backend/tests/ -q → 168 passed (15 new + 153 pre-existing). Server imports cleanly. Both adapters instantiate from registry. HeyGen model is ready in catalog.

## Requirements Advanced

None.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

- `backend/app/generation_dispatch.py` — New: async dispatch engine with submit-poll-settle/release loop, exponential backoff, credit management, and legacy carousel dispatch_generation_job
- `backend/app/generation_providers/__init__.py` — New: adapter registry package with get_adapter() factory
- `backend/app/generation_providers/openai_adapter.py` — New: Sora 2 text-to-video adapter (POST /v1/video/generations)
- `backend/app/generation_providers/heygen_adapter.py` — New: HeyGen UGC avatar adapter (POST /v2/video/generate)
- `backend/app/store.py` — Updated CCDANCE_AVATAR_MODEL_ID seed: provider_key ccdance_stub→heygen, readiness_status preview→ready
- `backend/tests/test_generation_dispatch.py` — New: 15 contract tests for adapter registry, job lifecycle, and credit ledger
