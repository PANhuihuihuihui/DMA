---
id: T05
parent: S01
milestone: M001
key_files:
  - backend/tests/test_generation_dispatch.py
  - backend/app/generation_dispatch.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T06:03:35.518Z
blocker_discovered: false
---

# T05: 15 contract tests pass; full 168-test suite green

**15 contract tests pass; full 168-test suite green**

## What Happened

Created backend/tests/test_generation_dispatch.py with 15 tests across three classes: (1) AdapterRegistryContractTest — verifies all registry keys instantiate, get_adapter raises for unknown keys, and adapters instantiate without API env vars; (2) JobLifecycleTest — verifies POST /api/v1/generation/jobs returns 201/queued, reserves credits correctly, GET returns the job, HeyGen model is ready, unknown model returns error, insufficient credits returns 409; (3) CreditLedgerTest — verifies success path settles credits (balance stays at balance-reserved), failure path releases credits (balance restored to initial), and unregistered provider_key fails cleanly with credit release. Fixed a missing conn.commit() after release_generation_credits in _release_on_failure. Also discovered and implemented dispatch_generation_job() for the legacy carousel synchronous adapter interface used by test_phase3_workspace.py — that test had been planned anticipating this function but was failing before S01.

## Verification

Verification evidence recorded: `python3 -m pytest backend/tests/test_generation_dispatch.py -v 2>&1 | tail -5` exited 0 (15 passed); `python3 -m pytest backend/tests/ -q 2>&1 | tail -3` exited 0 (168 passed in full suite).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_generation_dispatch.py -v 2>&1 | tail -5` | 0 | 15 passed | 7840ms |
| 2 | `python3 -m pytest backend/tests/ -q 2>&1 | tail -3` | 0 | 168 passed in full suite | 26550ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/tests/test_generation_dispatch.py`
- `backend/app/generation_dispatch.py`
