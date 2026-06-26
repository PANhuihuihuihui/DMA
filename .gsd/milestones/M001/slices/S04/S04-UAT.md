# S04: Pre-release Smoke and Credit Cost Validation — UAT

**Milestone:** M001
**Written:** 2026-06-26T03:46:47.049Z

## UAT Type

- UAT mode: runtime-executable
- Why this mode is sufficient: All verification is automated via Python test suite and smoke script; no browser interaction needed. Integration-level checks (catalog, API surface, insufficient-balance gate) run deterministically in isolated environments. Real provider checks (Sora 2, HeyGen) are SKIP in CI when API keys absent, confirming CI safety while supporting local developer testing with real credentials.

## Preconditions

- Python 3.9+ available with pytest installed
- Backend dependencies installed: `pip install -r backend/requirements.txt`
- No API keys required for CI run (OPENAI_API_KEY and HEYGEN_API_KEY omitted)
- For local real-provider testing: OPENAI_API_KEY and HEYGEN_API_KEY env vars set

## Smoke Test

Run `python3 backend/scripts/smoke_s04.py` and verify exit code 0 with smoke_s04_report.json containing: 3 PASS (catalog_costs, insufficient_balance, model_api_surface), 2 SKIP (sora2_real_gen, heygen_real_gen when API keys absent).

## Test Cases

### 1. Catalog Credit Costs

1. Run `python3 -m pytest backend/tests/test_smoke_catalog.py::CatalogCostTest -q`
2. Verify CatalogCostTest passes all 10 tests
3. **Expected:** Sora 2 credit_cost=180, HeyGen credit_cost=220, both seeded correctly, readiness_status='ready'

### 2. Model API Surface (creditCost Exposure)

1. Run `python3 -m pytest backend/tests/test_smoke_catalog.py::ModelApiSurfaceTest -q`
2. Verify ModelApiSurfaceTest passes both tests (openai_video and heygen models)
3. **Expected:** GET /api/v1/generation/models response includes creditCost fields matching catalog values (180 and 220)

### 3. Insufficient Balance Gating

1. Run `python3 -m pytest backend/tests/test_smoke_catalog.py::InsufficientBalanceTest -q`
2. Verify InsufficientBalanceTest passes (1 test)
3. **Expected:** create_generation_job raises StoreError(404 or 409) with credit-related detail for merchant with zero balance

### 4. Catalog Costs via Smoke Script

1. Run `python3 backend/scripts/smoke_s04.py` and capture smoke_s04_report.json
2. Verify CATALOG_COSTS check shows status=PASS with detail \"openai_video=180, heygen=220\"
3. **Expected:** Check passes, elapsed_ms recorded, exit code 0

### 5. Insufficient Balance via Smoke Script

1. Run `python3 backend/scripts/smoke_s04.py` and inspect smoke_s04_report.json
2. Verify INSUFFICIENT_BALANCE check shows status=PASS with detail \"Got expected StoreError status=404 or 409...\"
3. **Expected:** Check passes, confirms zero-balance merchant is gated

### 6. Model API Surface via Smoke Script

1. Run `python3 backend/scripts/smoke_s04.py` and inspect smoke_s04_report.json
2. Verify MODEL_API_SURFACE check shows status=PASS with detail \"openai_video creditCost=180, heygen creditCost=220\"
3. **Expected:** Check passes, confirms HTTP endpoint exposes creditCost fields

### 7. Provider Real-Generation Checks (Conditional)

1. When OPENAI_API_KEY is set: SORA2_REAL_GEN in smoke_s04_report.json shows status=PASS or FAIL (not SKIP)
2. When HEYGEN_API_KEY is set: HEYGEN_REAL_GEN in smoke_s04_report.json shows status=PASS or FAIL (not SKIP)
3. **Expected:** If keys present, real jobs dispatch and complete within 300s polling window; report records credit delta and final status

## Edge Cases

### Missing Catalog Rows

1. Run smoke script with manually corrupted DB (missing OPENAI_VIDEO_MODEL_ID row)
2. **Expected:** CATALOG_COSTS check fails with detail \"row missing for [model_id]\"

### API Endpoint Unavailable

1. Simulate server crash before MODEL_API_SURFACE check
2. **Expected:** Check fails with connection error detail

### Zero-Balance With Ledger Entries (Different from Missing Account)

1. Create merchant with credit_accounts row but ledger entries summing to zero
2. **Expected:** INSUFFICIENT_BALANCE check still raises error (covers both 404 and 409 paths)

## Failure Signals

- Exit code non-zero from `python3 backend/scripts/smoke_s04.py`
- Any \"FAIL\" status in smoke_s04_report.json
- Missing smoke_s04_report.json file after script runs
- pytest exit code non-zero for backend/tests/test_smoke_catalog.py
- Any test assertion failure in CatalogCostTest, ModelApiSurfaceTest, or InsufficientBalanceTest

## Not Proven By This UAT

- Real end-to-end merchant workflows (covered by M001 success criteria when API keys are present; S04 does not block on real provider runs for CI)
- Performance benchmarks or credit cost accuracy under concurrent job load (smoke runner is single-threaded)
- All edge cases in generation dispatch (S01 and S02 covered dispatch edge cases; S04 focuses on pre-release gates)
- UI credit visibility in frontend (part of S02 verification; S04 validates API surface only)

## Notes for Tester

- API keys are optional: CI runs with SKIP, local developer runs with real jobs if keys present
- Test isolation uses temporary databases per check; no shared state between runs
- HTTP server for MODEL_API_SURFACE check runs on OS-assigned port (port=0) to avoid conflicts
- Smoke report is machine-readable JSON; parse with `jq` for scripting or inspection
- Failure diagnostics include elapsed_ms per check for performance troubleshooting
