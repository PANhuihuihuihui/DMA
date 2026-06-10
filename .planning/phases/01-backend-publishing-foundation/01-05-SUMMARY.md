---
phase: 01-backend-publishing-foundation
plan: 05
subsystem: backend-publishing-retry-security
tags: [python-stdlib, sqlite, fake-publisher, retry, idempotency, redaction]

requires:
  - phase: 01-backend-publishing-foundation
    plan: 03
    provides: fake publish jobs, attempts, events, trace IDs, and retry-needed TikTok lifecycle
provides:
  - `POST /api/v1/publish-jobs/{job_id}/retry` for retryable fake publish jobs.
  - Append-only retry attempts and events with new attempt numbers and trace IDs.
  - SQLite `publish_outcomes` idempotency guard for successful fake external outcomes.
  - Deep diagnostic redaction that removes forbidden diagnostic key names before persistence and response serialization.
  - Backend and full-stack smoke coverage for retry, redaction, and duplicate outcome prevention.
affects: [phase-01, phase-02, facebook-publishing, tiktok-publishing, support-diagnostics]

tech-stack:
  added: []
  patterns:
    - Retry endpoint reuses stored approval snapshots and never accepts alternate provider targets.
    - Successful fake outcomes are keyed by approved draft version idempotency key plus connected channel.
    - Diagnostic redaction renames forbidden keys and redacts nested values before SQLite writes and API responses.

key-files:
  created:
    - backend/tests/test_retry_redaction_idempotency.py
    - scripts/smoke-retry-redaction.mjs
  modified:
    - backend/app/server.py
    - backend/app/store.py
    - backend/app/contracts.py
    - backend/app/fake_publisher.py
    - package.json

key-decisions:
  - "Retry is allowed only from `failed` or `retry_needed`; `published`, `queued`, and `publishing` jobs return safe 409 conflicts."
  - "TikTok fake retry deterministically succeeds on attempt 2 so STATUS-02 can prove retry without duplicate outcome records."
  - "Forbidden diagnostic keys are renamed to neutral redacted field names instead of preserving sensitive key names with redacted values."

patterns-established:
  - "Publish retry appends `queued`, `publishing`, and terminal events for the new attempt while preserving prior attempt and event row IDs."
  - "Successful publish outcomes are recorded separately from attempts and protected by a unique idempotency key/channel constraint."
  - "Smoke scripts assert browser-facing payloads and command output do not contain injected secret fixture values."

requirements-completed: [FOUND-04, FOUND-05, SEC-03, SEC-06, STATUS-02]

duration: 10m 16s
completed: 2026-06-10
---

# Phase 01 Plan 05: Backend Publishing Foundation Summary

**Retry-safe fake publishing now records immutable second attempts, blocks duplicate successful outcomes, and redacts nested provider diagnostics before storage or API output**

## Performance

- **Duration:** 10m 16s
- **Started:** 2026-06-10T18:45:56Z
- **Completed:** 2026-06-10T18:56:12Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added retry/redaction/idempotency backend tests and a full-stack Node smoke script.
- Added `POST /api/v1/publish-jobs/{job_id}/retry` for retryable fake publish jobs.
- Added append-only retry events and attempt 2 records with fresh trace IDs.
- Added `publish_outcomes` with an idempotency guard so one approved draft version/channel can produce only one successful fake external outcome.
- Expanded diagnostics redaction so forbidden nested diagnostic keys are renamed and values are redacted before SQLite persistence and API serialization.

## Task Commits

1. **Task 1: Add failing retry, idempotency, and redaction tests** - `015be5b` (`test`)
2. **Task 2: Implement idempotent retry and diagnostic redaction** - `d384c41` (`feat`)

## Files Created/Modified

- `backend/tests/test_retry_redaction_idempotency.py` - Contract tests for retry attempt immutability, published retry conflict, idempotency outcomes, and redaction.
- `scripts/smoke-retry-redaction.mjs` - Starts the backend, publishes a TikTok fake job, retries it, and checks browser-facing payload/output safety.
- `backend/app/server.py` - Adds retry routing and explicit SQLite connection closing in route handlers.
- `backend/app/store.py` - Adds `publish_outcomes`, event summary sanitization, and successful outcome idempotency writes.
- `backend/app/contracts.py` - Renames forbidden diagnostic keys during redaction instead of preserving sensitive key names.
- `backend/app/fake_publisher.py` - Adds fake retry behavior and records successful outcomes for initial and retry publishes.
- `package.json` - Adds `test:retry-redaction`.

## Decisions Made

- Retry reuses the original approval snapshot and idempotency key; clients cannot send alternate provider targets or draft payloads.
- Fake TikTok retry succeeds on attempt 2 to prove successful retry behavior after the deterministic attempt 1 `retry_needed` path.
- The retry endpoint accepts an optional fake-only diagnostics fixture for redaction testing, but all provider target data still comes from the stored approval snapshot.
- Redaction removes sensitive key names from serialized diagnostics, not just their values, because support/debug payloads must not expose credential-shaped fields.

## Verification

- `python3 -m unittest backend.tests.test_retry_redaction_idempotency -v` - failed in RED before implementation with HTTP 404 for the missing retry endpoint and 404 instead of the expected safe 409 published conflict.
- `npm run test:retry-redaction` - failed in RED for the same missing retry endpoint.
- `python3 -m unittest backend.tests.test_publish_approval backend.tests.test_token_boundary backend.tests.test_fake_publish_lifecycle backend.tests.test_retry_redaction_idempotency -v` - passed, 11 tests.
- `npm run test:retry-redaction` - passed; smoke output showed TikTok retry reaching `published` with attempts `[1, 2]` and event statuses `approved`, `queued`, `publishing`, `failed`, `retry_needed`, `queued`, `publishing`, `published`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected retry outcome test expectation**
- **Found during:** Task 2 verification
- **Issue:** The RED test initially expected the successful outcome row to be tied to attempt 1, but attempt 1 is the deterministic TikTok failure and attempt 2 is the retry success.
- **Fix:** Updated the assertion to require the single successful outcome record to reference attempt 2.
- **Files modified:** `backend/tests/test_retry_redaction_idempotency.py`
- **Verification:** Full backend suite and `npm run test:retry-redaction` passed.
- **Committed in:** `d384c41`

**2. [Rule 1 - Bug] Closed route-handler SQLite connections explicitly**
- **Found during:** Task 2 verification
- **Issue:** The expanded API test suite surfaced ResourceWarnings from route-handler SQLite connections that were committed/rolled back by context manager exit but not explicitly closed.
- **Fix:** Wrapped route-handler connections with `contextlib.closing`.
- **Files modified:** `backend/app/server.py`
- **Verification:** Full backend suite reran without the ResourceWarning output and passed.
- **Committed in:** `d384c41`

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes tightened correctness and verification fidelity without expanding beyond the retry/redaction backend scope.

## Issues Encountered

- The Python API tests take about 36-39 seconds because each test starts and shuts down a threaded local backend server. This is existing test harness cost, not a functional blocker.

## Known Stubs

| File | Line | Reason |
|------|------|--------|
| `backend/app/store.py` | 436 | Existing seeded TikTok provider summary uses `upload_to_inbox_placeholder`; live TikTok upload/direct-post behavior remains intentionally deferred beyond Phase 1 fake publishing. |

## Auth Gates

None - no external service authentication, OAuth flow, provider credential, or package installation was required.

## Threat Flags

None - the retry endpoint, idempotency outcome record, diagnostics redaction, and supply-chain constraints are covered by the plan threat model.

## User Setup Required

None.

## Next Phase Readiness

- Later debug/support surfaces can rely on attempts, events, trace IDs, redacted diagnostics, next actions, and idempotent outcome records.
- Phase 2 engine-spike work can preserve the same retry/idempotency contract when evaluating Postiz-style or native provider adapters.
- Facebook/TikTok production phases inherit a guardrail that prevents retry from duplicating a successful approved draft/channel outcome.

## Self-Check: PASSED

- Created files exist: `backend/tests/test_retry_redaction_idempotency.py` and `scripts/smoke-retry-redaction.mjs`.
- Modified files exist: backend route/store/contracts/fake publisher files and `package.json`.
- Task commits exist: `015be5b`, `d384c41`.
- Final verification commands passed after all task commits.
- No tracked file deletions were introduced by task commits.
- Unrelated `.planning/STATE.md`, `.planning/config.json`, and `.vscode/` changes were not staged.

---
*Phase: 01-backend-publishing-foundation*
*Completed: 2026-06-10*
