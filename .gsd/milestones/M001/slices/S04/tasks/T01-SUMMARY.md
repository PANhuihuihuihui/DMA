---
id: T01
parent: S04
milestone: M001
key_files:
  - backend/tests/test_smoke_catalog.py
key_decisions:
  - Used a zero monthly_credits credit account (no ledger entries) to simulate a merchant with zero balance, rather than draining credits iteratively
  - Inserted a merchants row before credit_accounts to satisfy the FK constraint for the fresh merchant in InsufficientBalanceTest
duration: 
verification_result: passed
completed_at: 2026-06-26T03:43:52.687Z
blocker_discovered: false
---

# T01: Created backend/tests/test_smoke_catalog.py with 13 passing tests covering catalog credit costs, API surface, and insufficient-balance gating.

**Created backend/tests/test_smoke_catalog.py with 13 passing tests covering catalog credit costs, API surface, and insufficient-balance gating.**

## What Happened

Examined store.py to confirm seeded values (Sora 2: credit_cost=180, model_key='sora-2', provider_key='openai', capability='video', readiness_status='ready'; HeyGen: credit_cost=220, model_key='heygen-avatar', provider_key='heygen', capability='avatar_video', readiness_status='ready'). Studied test_generation_dispatch.py for the ApiCase pattern (create_app on port 0, serve_forever in daemon thread). Created backend/tests/test_smoke_catalog.py with three test classes: CatalogCostTest (10 tests hitting the SQLite store directly via ensure_database + connect), ModelApiSurfaceTest (2 tests calling GET /api/v1/generation/models over HTTP and asserting creditCost values), and InsufficientBalanceTest (1 test inserting a bare merchant + zero-credit account then asserting StoreError(409, 'Insufficient generation credits.') is raised). Initial run failed with FK constraint — fixed by inserting the merchant row into the merchants table before the credit_accounts row. Final run: 13 passed in 1.32s.

## Verification

python3 -m pytest backend/tests/test_smoke_catalog.py -q --tb=short

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_smoke_catalog.py -q --tb=short` | 0 | 13 passed in 1.32s | 1320ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/tests/test_smoke_catalog.py`
