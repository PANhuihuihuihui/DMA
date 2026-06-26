# S04: Pre-release Smoke and Credit Cost Validation

**Goal:** Validate pre-release readiness: catalog credit costs match expected provider billing, the insufficient-balance gate returns a clear 409, model credit cost is visible in the API, and real provider smoke (Sora 2 + HeyGen) completes end-to-end when API keys are present. Produce a machine-readable diagnostics report as the milestone deliverable.
**Demo:** One real Sora 2 generation and one real HeyGen generation each complete end-to-end with correct credit delta recorded. Credit cost is visible in the model selector before launch. A job submitted with insufficient balance is blocked at the API with a clear error. Smoke diagnostics file captured.

## Must-Haves

- python3 -m pytest backend/tests/test_smoke_catalog.py -q --tb=short exits 0 (catalog costs, model API surface, and insufficient-balance gate all pass). python3 backend/scripts/smoke_s04.py exits 0 and writes backend/scripts/smoke_s04_report.json with CATALOG_COSTS, INSUFFICIENT_BALANCE, and MODEL_API_SURFACE as PASS; real provider checks are PASS when keys are present and SKIP otherwise.

## Proof Level

- This slice proves: operational — integration-level without keys; real-provider dispatch with Sora 2 and HeyGen when OPENAI_API_KEY / HEYGEN_API_KEY are set

## Integration Closure

Upstream surfaces consumed: store.py (create_generation_job, get_generation_credit_summary, seed_generation_model_catalog, OPENAI_VIDEO_MODEL_ID, CCDANCE_AVATAR_MODEL_ID, DEMO_MERCHANT_ID), generation_dispatch.py (start_async_dispatch, _dispatch_job), openai_adapter.py, heygen_adapter.py. New wiring introduced: test_smoke_catalog.py (CI-safe assertions), smoke_s04.py (orchestration script). What remains before the milestone is truly usable end-to-end: nothing — this slice closes M001.

## Verification

- Runtime signals: backend/scripts/smoke_s04_report.json contains per-check PASS/SKIP/FAIL with detail and elapsed time. Inspection surface: cat backend/scripts/smoke_s04_report.json gives a structured readiness verdict. Failure visibility: each check result includes a reason field and, for provider checks, the raw failure_reason and credit delta.

## Tasks

- [x] **T01: Created backend/tests/test_smoke_catalog.py with 13 passing tests covering catalog credit costs, API surface, and insufficient-balance gating.** `est:45m`
  Why: The milestone requires proof that credit cost is visible before launch and insufficient balance is blocked with a clear 409 error. Existing tests drain credits iteratively rather than asserting exact catalog values or the precise error message. We need direct assertions on the seeded credit_cost values (180 for Sora 2, 220 for HeyGen) and on the HTTP error contract.
  - Files: `backend/tests/test_smoke_catalog.py`
  - Verify: python3 -m pytest backend/tests/test_smoke_catalog.py -q --tb=short

- [x] **T02: Created backend/scripts/smoke_s04.py with 5 checks (3 PASS, 2 SKIP); smoke_s04_report.json written successfully.** `est:1h`
  Why: The milestone deliverable requires a 'smoke diagnostics file captured' artifact and evidence that the full pipeline runs end-to-end. The smoke script is the single runnable entry point: it validates all pre-release gates and writes backend/scripts/smoke_s04_report.json. When real API keys are absent (expected in CI), provider checks are SKIP and the script exits 0. When OPENAI_API_KEY or HEYGEN_API_KEY are present, it dispatches real generation jobs and records credit deltas.
  - Files: `backend/scripts/smoke_s04.py`
  - Verify: python3 backend/scripts/smoke_s04.py && test -f backend/scripts/smoke_s04_report.json

## Files Likely Touched

- backend/tests/test_smoke_catalog.py
- backend/scripts/smoke_s04.py
