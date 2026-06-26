---
estimated_steps: 12
estimated_files: 1
skills_used: []
---

# T01: Created backend/tests/test_smoke_catalog.py with 13 passing tests covering catalog credit costs, API surface, and insufficient-balance gating.

Why: The milestone requires proof that credit cost is visible before launch and insufficient balance is blocked with a clear 409 error. Existing tests drain credits iteratively rather than asserting exact catalog values or the precise error message. We need direct assertions on the seeded credit_cost values (180 for Sora 2, 220 for HeyGen) and on the HTTP error contract.

Do:
1. Create backend/tests/test_smoke_catalog.py.
2. Add CatalogCostTest (unittest.TestCase) using store.ensure_database on a tempfile DB + store.connect:
   - Assert Sora 2 row (OPENAI_VIDEO_MODEL_ID) has credit_cost=180, readiness_status='ready', capability='video', model_key='sora-2', provider_key='openai'.
   - Assert HeyGen row (CCDANCE_AVATAR_MODEL_ID) has credit_cost=220, readiness_status='ready', capability='avatar_video', model_key='heygen-avatar', provider_key='heygen'.
3. Add ModelApiSurfaceTest (extends ApiCase pattern from test_generation_dispatch.py — create_app on port 0):
   - GET /api/v1/generation/models returns a list where the Sora 2 entry has creditCost=180 and the HeyGen entry has creditCost=220.
4. Add InsufficientBalanceTest (unittest.TestCase, store-layer only):
   - Create a temp DB, call store.create_generation_job with a fresh merchant_id (not DEMO_MERCHANT_ID, no ledger entries → zero balance).
   - Assert store.StoreError is raised with status=409 and message matching 'Insufficient generation credits.'.

Done when: python3 -m pytest backend/tests/test_smoke_catalog.py -q --tb=short exits 0 with all tests passing.

## Inputs

- `backend/app/store.py`
- `backend/app/server.py`
- `backend/tests/test_generation_dispatch.py`

## Expected Output

- `backend/tests/test_smoke_catalog.py`

## Verification

python3 -m pytest backend/tests/test_smoke_catalog.py -q --tb=short
