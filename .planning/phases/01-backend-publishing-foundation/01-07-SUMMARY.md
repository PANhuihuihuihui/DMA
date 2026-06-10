---
phase: 01-backend-publishing-foundation
plan: 07
subsystem: backend-debug-diagnostics
tags: [python-stdlib, sqlite, debug-api, support-diagnostics, redaction]

requires:
  - phase: 01-backend-publishing-foundation
    plan: 05
    provides: retry attempts, trace IDs, append-only events, redacted diagnostics, and idempotent publish outcomes
provides:
  - Read-only `GET /api/v1/debug/publish-jobs` support diagnostics endpoint.
  - Support-safe debug rows with merchant, platform, job status, attempt count, latest trace ID, error class, updated timestamp, next action, approver, draft version, media refs, attempts, events, and approval snapshot summary.
  - Redacted token-boundary and provider-diagnostics serializers for debug payloads.
  - Backend and full-stack smoke coverage for debug diagnostics and secret-value redaction.
affects: [phase-01, phase-06, support-diagnostics, facebook-publishing, tiktok-publishing]

tech-stack:
  added: []
  patterns:
    - Debug endpoint reads existing SQLite workflow records only and introduces no mutation route.
    - Debug serializers derive support rows from approval snapshots, publish attempts, and append-only events.
    - Token boundary refs are re-shaped for debug output so secret refs and credential fingerprints are never exposed.

key-files:
  created:
    - backend/tests/test_debug_redaction.py
    - scripts/smoke-debug-route.mjs
  modified:
    - backend/app/server.py
    - backend/app/store.py
    - backend/app/contracts.py
    - package.json

key-decisions:
  - "Expose debug publishing diagnostics as `GET /api/v1/debug/publish-jobs` with read-only support rows instead of adding admin mutation or permission behavior."
  - "Use approval snapshots as the source for approver, draft version, media refs, and token-boundary refs, but summarize them so debug payloads avoid token internals."
  - "Report latest trace ID, error class, and next action from the latest serialized attempt diagnostics while preserving all attempt and event history."

patterns-established:
  - "Debug rows include both table-friendly fields and detailed sections for approval snapshot summary, attempts, append-only events, and redacted diagnostics."
  - "Full-stack debug smoke creates published Facebook and retry-published TikTok jobs, then fails if support payloads or stdout leak forbidden diagnostic fields or injected secret values."
  - "Contract tests assert debug tokenBoundaryRef has `visibility: redacted` and omits server-only boundary internals."

requirements-completed: [FOUND-02, SEC-03, SEC-06, APPR-06, STATUS-01, STATUS-02]

duration: 10m 35s
completed: 2026-06-10
---

# Phase 01 Plan 07: Backend Publishing Foundation Summary

**Read-only backend debug diagnostics now expose support-safe publish job rows with redacted attempts, events, trace IDs, next actions, approval snapshots, and token-boundary refs**

## Performance

- **Duration:** 10m 35s
- **Started:** 2026-06-10T18:56:30Z
- **Completed:** 2026-06-10T19:07:05Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added backend debug contract tests for published, retry-needed, and retry-published fake jobs.
- Added `scripts/smoke-debug-route.mjs`, which starts the backend, creates Facebook/TikTok publish jobs, retries TikTok with injected secret-like diagnostics, and checks debug payload safety.
- Added `GET /api/v1/debug/publish-jobs`.
- Added support-safe debug serialization for merchant, platform, job status, attempt count, latest trace ID, error class, updated timestamp, next action, approver, draft version, media refs, token-boundary ref, approval snapshot summary, attempts, events, and redacted diagnostics.
- Added `npm run test:debug`.

## Task Commits

1. **Task 1: Add failing debug endpoint smoke and redaction tests** - `03aa161` (`test`)
2. **Task 2: Implement read-only redacted debug API** - `76ef46f` (`feat`)

## Files Created/Modified

- `backend/tests/test_debug_redaction.py` - Contract tests for debug row shape, approval/audit fields, attempts/events, token-boundary redaction, and provider diagnostic redaction.
- `scripts/smoke-debug-route.mjs` - Full-stack debug smoke test with published Facebook, retry-published TikTok, and secret-leak assertions.
- `backend/app/server.py` - Adds read-only `GET /api/v1/debug/publish-jobs`.
- `backend/app/store.py` - Adds debug publish job query and support-row serializer.
- `backend/app/contracts.py` - Adds redacted token-boundary ref and approval snapshot summary helpers.
- `package.json` - Adds `test:debug`.

## Decisions Made

- The debug endpoint is intentionally read-only and adds no approval, publish, retry, role, or permission behavior.
- Debug payloads summarize approval snapshots for support use while preserving enough audit context: approver, exact draft version, idempotency suffix, media refs, connected channel ref, timestamps, and safe provider/disclosure summaries.
- Latest table fields come from the latest attempt, while all attempts and append-only events remain available in the detailed row.

## Verification

- `python3 -m unittest backend.tests.test_debug_redaction -v` - failed in RED before implementation with HTTP 404 for the missing debug endpoint.
- `npm run test:debug` - failed in RED before implementation with HTTP 404 for the missing debug endpoint.
- `python3 -m unittest backend.tests.test_debug_redaction -v` - passed, 2 tests.
- `npm run test:debug` - passed; smoke output showed Facebook `published`, TikTok `published` after retry, attempts `{facebook: 1, tiktok: 2}`, and trace IDs only.
- `python3 -m unittest backend.tests.test_publish_approval backend.tests.test_token_boundary backend.tests.test_fake_publish_lifecycle backend.tests.test_retry_redaction_idempotency backend.tests.test_debug_redaction -v` - passed, 13 tests.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Python API tests still take about 36-40 seconds because each test starts and shuts down local backend server instances. This is existing harness cost and did not block verification.

## Known Stubs

| File | Line | Reason |
|------|------|--------|
| `backend/app/store.py` | 438 | Existing seeded TikTok provider summary uses `upload_to_inbox_placeholder`; live TikTok upload/direct-post behavior remains intentionally deferred beyond Phase 1 fake publishing. |

## Auth Gates

None - no external service authentication, OAuth flow, provider credential, or package installation was required.

## Threat Flags

None - the debug endpoint, token-boundary debug serialization, diagnostics redaction, read-only behavior, and supply-chain constraints are covered by the plan threat model.

## User Setup Required

None.

## Next Phase Readiness

- Phase 1 debug UI work can consume `GET /api/v1/debug/publish-jobs` directly for operator diagnostics.
- Later Facebook/TikTok provider implementations can preserve the same support fields while swapping fake diagnostics for official provider diagnostics after redaction.
- Phase 6 pilot support workflows can build on these rows without needing token access.

## Self-Check: PASSED

- Created files exist: `backend/tests/test_debug_redaction.py` and `scripts/smoke-debug-route.mjs`.
- Modified files exist: backend route/store/contracts files and `package.json`.
- Task commits exist: `03aa161` and `76ef46f`.
- Required verification commands passed after task commits.
- Broader backend regression suite passed with 13 tests.
- No tracked file deletions were introduced by task commits.
- Unrelated `.planning/config.json` and `.vscode/` changes were not staged.

---
*Phase: 01-backend-publishing-foundation*
*Completed: 2026-06-10*
