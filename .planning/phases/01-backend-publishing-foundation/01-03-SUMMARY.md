---
phase: 01-backend-publishing-foundation
plan: 03
subsystem: backend-publishing-lifecycle
tags: [python-stdlib, sqlite, fake-publisher, publish-jobs, lifecycle-events, redacted-diagnostics]

requires:
  - phase: 01-backend-publishing-foundation
    plan: 02
    provides: backend approval snapshots consumed by `/app`
provides:
  - Deterministic fake publishing lifecycle from approved snapshots only.
  - `POST /api/v1/approvals/{approval_id}/publish` and `GET /api/v1/publish-jobs/{job_id}` API routes.
  - Publish job, immutable attempt, request digest, trace ID, retry classification, redacted diagnostics, and append-only lifecycle event persistence.
  - Backend and smoke coverage for Facebook fake success and TikTok fake retry-needed failure.
affects: [phase-01, phase-02, facebook-publishing, tiktok-publishing, status-timeline]

tech-stack:
  added: []
  patterns:
    - Python stdlib fake publisher service with synchronous deterministic outcomes.
    - SQLite append-only event records and immutable attempt serialization.
    - Redacted diagnostics and digest generation through backend contract helpers.

key-files:
  created:
    - backend/app/fake_publisher.py
    - backend/tests/test_fake_publish_lifecycle.py
    - scripts/smoke-fake-publish.mjs
  modified:
    - backend/app/server.py
    - backend/app/store.py
    - backend/app/contracts.py
    - package.json

key-decisions:
  - "Fake publish jobs require an existing approved snapshot and reject missing approvals with bounded 400 errors."
  - "Facebook deterministically reaches `published`; TikTok deterministically records `failed` then `retry_needed` to prove retry-facing lifecycle states without live provider calls."
  - "Attempt diagnostics stay fake, redacted, and local; Phase 1 still contains no Meta, TikTok, Postiz, OAuth, scraping, cookie posting, or browser automation path."

patterns-established:
  - "Publish events serialize timestamp, source actor, attempt number, lifecycle status, and summary for timeline UI use."
  - "Publish attempts serialize attempt number, trace ID, request digest, normalized status, started/finished timestamps, retry classification, and redacted diagnostics."
  - "Task 01-03 uses RED then GREEN commits for the fake publish lifecycle contract."

requirements-completed: [FOUND-03, FOUND-04, SEC-04, SEC-06, APPR-06, STATUS-01]

duration: 6m 38s
completed: 2026-06-10
---

# Phase 01 Plan 03: Backend Publishing Foundation Summary

**Approved backend snapshots can now queue deterministic fake Facebook and TikTok publish jobs with attempts, traceable events, and redacted diagnostics**

## Performance

- **Duration:** 6m 38s
- **Started:** 2026-06-10T18:24:58Z
- **Completed:** 2026-06-10T18:31:36Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added fake publish lifecycle tests and a full-stack smoke script covering approval-required publishing, CTA copy, safe responses, Facebook success, and TikTok retry-needed failure.
- Added `backend/app/fake_publisher.py` with deterministic local-only outcomes.
- Added publish job, attempt, event, trace ID, request digest, retry classification, and redacted diagnostic serializers.
- Added `POST /api/v1/approvals/{approval_id}/publish` and `GET /api/v1/publish-jobs/{job_id}` routes.
- Added `npm run test:fake-publish` without changing dependency lists.

## Task Commits

1. **Task 1: Add failing backend fake publish lifecycle tests** - `825252a` (`test`)
2. **Task 2: Implement fake publisher jobs, attempts, and append-only events** - `4e1ee83` (`feat`)

## Files Created/Modified

- `backend/app/fake_publisher.py` - Queues approved fake publish jobs and runs deterministic Facebook/TikTok fake attempts.
- `backend/app/server.py` - Routes approval publish and publish job detail requests.
- `backend/app/store.py` - Persists and serializes jobs, attempts, events, retry classification, traces, digests, and diagnostics.
- `backend/app/contracts.py` - Adds request digest, trace ID, and safe diagnostics helpers.
- `backend/tests/test_fake_publish_lifecycle.py` - Verifies approval-required fake lifecycle, event shape, attempt shape, CTA copy, and response safety.
- `scripts/smoke-fake-publish.mjs` - Starts the backend, approves Facebook/TikTok drafts, queues fake publish jobs, and checks terminal states.
- `package.json` - Adds `test:fake-publish`.

## Decisions Made

- Used one synchronous local fake publish path in Phase 1 to keep lifecycle behavior deterministic and bounded.
- Returned `400 Approval not found.` for missing approval publish requests rather than leaking route or storage details.
- Added SQLite column migrations for the new publish job fields so existing local dev databases can open without manual reset.

## Verification

- `python3 -m unittest backend.tests.test_fake_publish_lifecycle -v` - failed in RED before implementation with HTTP 404 for the missing publish endpoint, as expected.
- `npm run test:fake-publish` - failed in RED before implementation with HTTP 404 for the missing publish endpoint, as expected.
- `python3 -m unittest backend.tests.test_publish_approval backend.tests.test_token_boundary backend.tests.test_fake_publish_lifecycle -v` - passed, 9 tests.
- `npm run test:fake-publish` - passed; smoke output showed Facebook `published` and TikTok `retry_needed`.
- Implementation-only scan found no provider SDK imports, provider environment reads, Postiz calls, browser automation strings, or network calls in `backend/app`.
- Invalid publish request to `/api/v1/approvals/not_an_approval/publish` returned `400 Approval not found.`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Task 1 files were already present as untracked plan-scope files when execution started. They matched the plan contract, were verified in RED, and were committed as the Task 1 test commit.

## Known Stubs

| File | Line | Reason |
|------|------|--------|
| `backend/app/store.py` | 397 | Seeded TikTok provider summary still uses `upload_to_inbox_placeholder`; live TikTok upload/direct-post behavior remains intentionally deferred beyond Phase 1 fake publishing. |

## Auth Gates

None - no external service authentication, OAuth flow, provider credential, or package installation was required.

## Threat Flags

None - the new publish endpoint, fake publisher, store writes, and response serializers are covered by the plan threat model.

## User Setup Required

None.

## Next Phase Readiness

- Later Phase 1 plans can render the persisted job timeline and support diagnostics using the event and attempt response shapes from this plan.
- Phase 2 can evaluate a Postiz-style or native provider adapter behind the same workflow records without changing approval snapshot semantics.
- Facebook and TikTok production phases inherit approval-required publishing, redacted diagnostics, and lifecycle status contracts.

## Self-Check: PASSED

- Created/modified files exist: `backend/app/fake_publisher.py`, backend route/store/contracts files, fake lifecycle tests, smoke script, and `package.json`.
- Task commits exist: `825252a`, `4e1ee83`.
- Final verification commands passed after all task commits.
- No tracked file deletions were introduced by task commits.
- Unrelated `.planning/config.json`, orchestrator `.planning/STATE.md` changes, and `.vscode/` were not staged.

---
*Phase: 01-backend-publishing-foundation*
*Completed: 2026-06-10*
