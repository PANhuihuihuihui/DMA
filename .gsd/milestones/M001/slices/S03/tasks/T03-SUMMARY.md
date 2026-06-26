---
id: T03
parent: S03
milestone: M001
key_files:
  - backend/tests/test_generation_dispatch.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T06:04:53.995Z
blocker_discovered: false
---

# T03: Added MockVideoSuccessAdapter, MockUgcVideoSuccessAdapter, and VideoPackageHandoffTest with 3 tests

**Added MockVideoSuccessAdapter, MockUgcVideoSuccessAdapter, and VideoPackageHandoffTest with 3 tests**

## What Happened

Read the existing test file to understand the MockSuccessAdapter pattern and CreditLedgerTest._patch_registry approach. Added two new mock adapter classes: MockVideoSuccessAdapter (poll returns kind=video) and MockUgcVideoSuccessAdapter (poll returns kind=avatar_video), following the async _dispatch_job adapter interface (submit returns provider_job_id string, poll returns result dict). Added VideoPackageHandoffTest with setUp using store.ensure_database and DEMO_MERCHANT_ID. Three tests use _create_video_job (wraps store.create_generation_job with dispatch=False) and _patch_and_dispatch (patches _PROVIDER_REGISTRY by string key, calls _dispatch_job, restores original). First run revealed test_dispatch_ugc_video_job_creates_ugc_creative was picking up a pre-seeded demo creative row instead of the newly created one. Fixed by resolving creativeId from serialize_generation_job (which reads it from the output metadata updated by materialize_video_package) and querying the specific row by ID. Used _dispatch_job (async path) not dispatch_generation_job (sync carousel path) because the plan-specified mock adapter shape (submit+poll) matches only the async path.

## Verification

python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short — 18 passed, 0 failed. All three new tests (test_dispatch_video_job_creates_generated_creative, test_dispatch_ugc_video_job_creates_ugc_creative, test_video_creative_has_video_media_asset) passed alongside the 15 pre-existing tests.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short` | 0 | 18 passed in 14.05s | 14229ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/tests/test_generation_dispatch.py`
