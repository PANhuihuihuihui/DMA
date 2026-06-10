---
phase: 01-backend-publishing-foundation
plan: 06
subsystem: frontend-publishing-retry
tags: [react, vite, retry, publish-timeline, redacted-diagnostics]

requires:
  - phase: 01-backend-publishing-foundation
    plan: 04
    provides: frontend fake publish client, publish job models, and timeline UI
  - phase: 01-backend-publishing-foundation
    plan: 05
    provides: backend retry endpoint, idempotency, append-only retry attempts, and diagnostic redaction
provides:
  - Retry API client method for backend publish jobs.
  - Retryable status constants and attempt metadata normalization for frontend publish jobs.
  - Attempt-grouped timeline rendering with trace IDs, timestamps, next actions, request digests, statuses, and redacted diagnostics.
  - `Retry publish` confirmation control rendered only for backend retryable job states.
  - `/app` retry wiring that refreshes workflow state and preserves immutable attempt history.
affects: [phase-01, phase-02, facebook-publishing, tiktok-publishing, status-timeline, support-diagnostics]

tech-stack:
  added: []
  patterns:
    - Plain relative `/api/v1` retry fetch method that sends only the backend publish job ID.
    - React retry control owns confirmation and pending/error state while `/app` owns refreshed workflow records.
    - Publish timeline groups backend events under immutable attempts without collapsing prior attempt rows.

key-files:
  created:
    - src/components/RetryPublishControl.jsx
  modified:
    - src/api/publishingClient.js
    - src/models/publishing.js
    - src/components/PublishTimeline.jsx
    - src/main.jsx
    - src/styles.css

key-decisions:
  - "Retry eligibility is determined from backend job status only: `failed` and `retry_needed`."
  - "Browser retry calls send only the publish job ID and cannot override draft payloads, provider targets, diagnostics, or idempotency data."
  - "Timeline diagnostics are rendered from backend-redacted attempt diagnostics and filtered again before display."

patterns-established:
  - "`RetryPublishControl` returns null unless the normalized backend publish job is retryable."
  - "`PublishTimeline` groups event rows by attempt number while preserving backend event order."
  - "`/app` stores retried publish jobs in React memory and refreshes backend workflow records after retry acceptance."

requirements-completed: [FOUND-02, FOUND-05, FOUND-06, SEC-03, STATUS-02]

duration: 7m 32s
completed: 2026-06-10
---

# Phase 01 Plan 06: Backend Publishing Foundation Summary

**React `/app` can retry backend retryable fake publish jobs and display immutable attempt-grouped timeline history with redacted diagnostics**

## Performance

- **Duration:** 7m 32s
- **Started:** 2026-06-10T19:10:01Z
- **Completed:** 2026-06-10T19:17:33Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added `retryPublishJob(jobId)` for `POST /api/v1/publish-jobs/{job_id}/retry`, with no client-supplied payload overrides.
- Added retryable backend status constants plus normalized attempt `nextAction` and `errorClass` fields.
- Updated `PublishTimeline` to group backend events by attempt number, keep prior attempt rows visible, and show trace IDs, timestamps, statuses, next actions, request digests, and redacted diagnostics.
- Added `RetryPublishControl` with `Retry publish` confirmation copy and pending/error state.
- Wired `/app` to show retry beside the selected platform timeline only when the normalized backend job is `failed` or `retry_needed`.
- Added timeline/retry CSS for stable desktop and mobile layout, status-specific failed/retry-needed tones, and wrapping long trace/digest values.

## Task Commits

1. **Task 1: Add retry client method and attempt-aware timeline models** - `fb22a04` (`feat`)
2. **Task 2: Add retry control and `/app` retry wiring** - `507ada8` (`feat`)

## Files Created/Modified

- `src/api/publishingClient.js` - Adds retry API method scoped to backend publish job IDs.
- `src/models/publishing.js` - Adds retryable status constants and attempt diagnostic metadata normalization.
- `src/components/PublishTimeline.jsx` - Renders attempt-grouped event history and redacted diagnostic rows.
- `src/components/RetryPublishControl.jsx` - Provides retry confirmation and bounded retry request state.
- `src/main.jsx` - Wires selected-platform retry into `/app` and refreshes workflow state after retry.
- `src/styles.css` - Adds attempt, diagnostic, retry, and responsive timeline fit styles.

## Decisions Made

- Retry UI uses backend job status as the source of truth and does not infer eligibility from client labels.
- Retry calls do not send alternate draft data, provider target data, diagnostic fixtures, token values, or idempotency overrides.
- Client-side diagnostic rendering applies a defensive display filter even though backend responses are already redacted.

## Verification

- `npm run test:approval` - passed.
- `npm run test:fake-publish` - passed; smoke output showed Facebook `published` and TikTok `retry_needed`.
- `npm run test:retry-redaction` - passed; smoke output showed retry attempts `[1, 2]` and final status `published`.
- `npm run build` - passed.
- `node --input-type=module ... normalizePublishJob smoke` - passed; preserved attempt `[1, 2]`, event order, and next action normalization.
- Acceptance scan confirmed `Retry publish` is guarded by `failed`/`retry_needed`, confirmation copy includes new attempt and idempotency language, and timeline CSS wraps trace/digest values.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Backend smoke suites each took about 36 seconds because they start local API servers, matching the prior Phase 1 test harness behavior.
- Verification generated Python `__pycache__` directories; those generated directories were removed and not staged.

## Known Stubs

None - scan found only defensive empty defaults and pre-existing form placeholder attributes.

## Auth Gates

None - no external service authentication, OAuth flow, provider credential, or package installation was required.

## Threat Flags

None - the retry endpoint client call, retry API response rendering, and diagnostics display are covered by the plan threat model.

## User Setup Required

None.

## Next Phase Readiness

- Later debug UI and production provider work can reuse the same retryable status guard, attempt grouping, trace display, next-action metadata, and redacted diagnostic rendering.
- Facebook/TikTok production phases inherit a UI path that retries only backend-approved retryable jobs and preserves prior attempt history.
- The current dirty `.planning/config.json` and unrelated `.vscode/` entries were not staged or committed.

## Self-Check: PASSED

- Created/modified files exist: `src/api/publishingClient.js`, `src/models/publishing.js`, `src/components/PublishTimeline.jsx`, `src/components/RetryPublishControl.jsx`, `src/main.jsx`, and `src/styles.css`.
- Task commits exist: `fb22a04` and `507ada8`.
- Required verification commands passed after implementation.
- No tracked file deletions were introduced by task commits.
- Unrelated `.planning/config.json` and `.vscode/` changes were not staged.

---
*Phase: 01-backend-publishing-foundation*
*Completed: 2026-06-10*
