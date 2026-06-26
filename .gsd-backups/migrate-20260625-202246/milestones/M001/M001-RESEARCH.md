# M001: Text-to-Video and UGC Avatar Generation — Research

**Date:** 2026-06-26
**Status:** Complete

## Summary

Phase 13 laid substantial groundwork: `store.py` contains the full DB schema (generation_model_catalog, generation_jobs, generation_attempts, generation_outputs, credit_accounts, credit_ledger), seed data for Sora 2 (`genmodel_openai_video_primary`, 180 credits, `readiness_status: "ready"`) and CCDance avatar (`genmodel_ccdance_avatar_preview`, 220 credits, `readiness_status: "preview"`), and all CRUD store functions (`create_generation_job`, `list_generation_models`, `serialize_generation_job`, etc.). `server.py` has all HTTP routes (GET /api/v1/generation/models, GET /credits, GET /jobs, POST /jobs, GET /jobs/:id, POST /jobs/:id/retry). `src/main.jsx` has "Short Ad Video" and "UGC Ads" module cards and already imports from `./api/generationClient.js` and `./models/generation.js`.

**The critical gap:** `backend/app/generation_dispatch.py` is imported at server startup but does not exist — the server currently fails to start. No `backend/app/generation_providers/` directory exists. `src/api/generationClient.js` and `src/models/generation.js` are imported by main.jsx but do not exist — the frontend fails to build. These three pieces are the entire unbuild surface for M001.

The provider selection question is partially answered: Sora 2 via OpenAI API is the correct text-to-video choice (catalog entry exists, `readiness_status: ready`). The UGC avatar provider is the open risk — CCDance is a stub with no real implementation path; the milestone context flags volcengine/dashscope (from AiToEarn reference) and commercial alternatives (HeyGen, D-ID, Synthesia). A pragmatic resolution: implement the CCDance adapter against a real provider that supports avatar video (HeyGen is the most accessible; volcengine requires Chinese cloud account; Synthesia is enterprise). The decision should be made before slice planning.

## Recommendation

**Build `generation_dispatch.py` first** — it's the hard blocker for server startup and all downstream work. The dispatch engine should follow the AiToEarn submit-poll-callback pattern: accept a job_id, load the model catalog entry, instantiate the correct provider adapter, submit the job, poll at configured intervals, settle credits on completion or release on failure. Make it idempotent (job already in terminal state → no-op).

**Provider strategy:** Sora 2 for text-to-video (OpenAI Responses API, video generation endpoint). For UGC avatar, replace the CCDance stub with HeyGen API (v2) — it supports avatar selection by ID, script-based video generation, and voiceover in one call; their async job pattern matches the existing lifecycle model exactly. This preserves the "one adapter per capability" pattern without blocking on unavailable/obscure providers.

**Frontend:** `generationClient.js` and `models/generation.js` are small, well-scoped modules — write them after the backend dispatch is proven.

## Implementation Landscape

### Key Files

- `backend/app/store.py` — DO NOT CHANGE schema or store functions. Generation tables, catalog seed (Sora 2 + CCDance), credit CRUD, and `create_generation_job` are all complete. Add `ccdance_stub` → `heygen` rename in catalog seed when provider is resolved.
- `backend/app/server.py:26` — imports `generation_dispatch`; `server.py:179` calls `generation_dispatch.start_async_dispatch(self.db_path, job_id)`; `:193` calls `generation_dispatch.retry_generation_job(...)`. These are the two functions the dispatch module must export.
- `backend/app/generation_dispatch.py` — MUST CREATE. The async dispatch engine. Pattern: spawn a background thread per job (matching Phase 11's carousel dispatch pattern if it exists, otherwise use `threading.Thread`). Must export `start_async_dispatch(db_path, job_id)` and `retry_generation_job(db_path, merchant_id, job_id, dispatch=True)`.
- `backend/app/generation_providers/` — MUST CREATE directory with `__init__.py`, `openai_adapter.py` (Sora 2), `heygen_adapter.py` (or chosen avatar provider).
- `src/api/generationClient.js` — MUST CREATE. Mirrors `publishingClient.js` pattern. Functions: `listGenerationModels()`, `getGenerationCredits()`, `submitGenerationJob(payload)`, `getGenerationJob(jobId)`, `retryGenerationJob(jobId)`, `listGenerationJobs()`.
- `src/models/generation.js` — MUST CREATE. Normalizer/serializer for generation job records, matching `src/models/publishing.js` pattern.
- `src/main.jsx:61,67` — imports already wired; the UI module cards exist. Needs: job submit handler, status polling loop, Creative Editor handoff when job reaches `succeeded` state.

### Build Order

1. **`generation_dispatch.py` + provider adapters** — server cannot start without the dispatch module. Prove submit→poll→succeed/fail for Sora 2 first (it's `readiness_status: ready`); CCDance/HeyGen adapter can follow. This unblocks contract tests.
2. **Contract tests** — adapter contract, job lifecycle state transitions, credit reserve/settle/release. Must pass before frontend work.
3. **`src/api/generationClient.js` + `src/models/generation.js`** — frontend modules. Once backend is proven, these are straightforward.
4. **Frontend wiring in `main.jsx`** — submit flow, polling, Creative Editor handoff, approval continuity.
5. **Real provider smoke** — Sora 2 end-to-end with real credits, then avatar provider.

### Verification Approach

```bash
# Backend: server starts without ImportError
cd backend && python -m pytest tests/ -x -q

# Generation job submit + dispatch returns job_id with status=queued
curl -X POST http://localhost:8080/api/v1/generation/jobs \
  -H "Cookie: session=..." \
  -d '{"modelCatalogId":"genmodel_openai_video_primary","prompt":"...", "dispatch":false}'

# Poll job status
curl http://localhost:8080/api/v1/generation/jobs/<id>

# Credits reserved/released correctly
curl http://localhost:8080/api/v1/generation/credits
```

## Constraints

- `generation_dispatch.py` must export exactly `start_async_dispatch(db_path, job_id)` and `retry_generation_job(db_path, merchant_id, job_id, dispatch)` — server.py calls these at lines 179 and 193.
- Provider secrets (OpenAI API key, HeyGen API key) must be server-side only; never passed to the frontend.
- All generation is async — no synchronous blocking provider calls in the request path. Use threading or asyncio worker matching existing server architecture (server.py appears to be a stdlib HTTPServer — threading.Thread is the safe choice).
- Credits must be reserved at job creation and either settled (success) or released (failure); `create_generation_job` in store.py already handles the reservation — the dispatch module must call the settle/release functions.
- CCDance catalog entry uses `provider_key: "ccdance_stub"` — when switching to HeyGen, update the catalog seed in `store.py:seed_generation_model_catalog` to use `provider_key: "heygen"`. The `CCDANCE_AVATAR_MODEL_ID` constant can remain but its provider_key changes.

## Common Pitfalls

- **Missing `generation_dispatch.py` causes server startup failure** — this is currently the case; the first task must create it even as a minimal skeleton so tests can run.
- **Credit double-reservation** — `create_generation_job` in store.py already reserves credits (line 6356+); the dispatch module must NOT reserve again, only settle or release.
- **Status polling in the frontend** — video jobs take minutes. Use exponential backoff with a max interval (e.g. 2s → 4s → 8s → 30s cap) rather than fixed polling to avoid hammering the backend.
- **Avatar provider latency** — HeyGen async jobs typically complete in 2–5 minutes; the frontend must handle `running` state gracefully with a progress indicator.
- **CCDance catalog entry `readiness_status: "preview"`** — this is served to the frontend by `list_generation_models`. If switching to HeyGen, update to `"ready"` in the seed.

## Open Risks

- **Provider availability** — Sora 2 (OpenAI video generation) requires API access that may not yet be generally available; verify the `POST /v1/video/generations` endpoint is accessible before committing to the slice plan. If not available, fallback to a provider with known access (RunwayML, Kling, Luma Labs).
- **HeyGen / avatar provider selection** — if HeyGen is not chosen, the dispatch module needs a different adapter. The catalog seed `provider_key` is the coupling point. This decision gates S01.
- **Voiceover composition** — the CCDance catalog entry has `voiceover` as a settings field; if HeyGen handles voiceover natively (it does), the field maps cleanly. If a separate TTS step is needed (MiniMax TTS), the dispatch module must orchestrate two sequential provider calls before settling credits — which adds complexity and a new failure mode.

## Sources

- `backend/app/store.py` (lines 117–170, 1273–1415) — generation schema and catalog seed
- `backend/app/server.py` (lines 26, 115–197) — HTTP routes and dispatch interface contract
- `src/main.jsx` (lines 61, 67, 1331, 1438) — frontend import surface and module card definitions
