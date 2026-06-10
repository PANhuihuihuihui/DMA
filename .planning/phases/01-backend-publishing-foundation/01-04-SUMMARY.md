---
phase: 01-backend-publishing-foundation
plan: 04
subsystem: frontend-publishing-timeline
tags: [react, vite, publishing-api-client, fake-publish, lifecycle-timeline, approval-snapshot]

requires:
  - phase: 01-backend-publishing-foundation
    plan: 03
    provides: fake publish jobs, attempts, events, trace IDs, and redacted diagnostics
provides:
  - Browser fake publish queue and publish job lookup client methods.
  - Frontend lifecycle constants and publish job, attempt, event, trace, status, diagnostic, and media ref normalizers.
  - `PublishTimeline` component rendering fixed generic lifecycle states and backend event rows.
  - `/app` queue action from approved backend snapshots with returned jobs kept in React memory only.
affects: [phase-01, phase-02, facebook-publishing, tiktok-publishing, status-timeline]

tech-stack:
  added: []
  patterns:
    - Plain relative `/api/v1` fetch methods for fake publishing actions.
    - Frontend lifecycle normalization mirroring backend job, attempt, and event serializers.
    - React-only in-memory publish job state for timeline display without browser persistence.

key-files:
  created:
    - src/components/PublishTimeline.jsx
  modified:
    - src/api/publishingClient.js
    - src/models/publishing.js
    - src/main.jsx
    - src/styles.css

key-decisions:
  - "Queue fake publish submits only the backend approval ID and never sends provider targets, credentials, or alternate payload fields."
  - "Publish job/event records returned by the backend are displayed from normalized React state and are not written to localStorage."
  - "The timeline renders every generic lifecycle state for each platform before and after approval, using empty-state copy until a backend job exists."

patterns-established:
  - "`src/models/publishing.js` now owns `LIFECYCLE_STATES` and `normalizePublishJob` for frontend lifecycle consumers."
  - "`PublishTimeline` renders backend event rows with timestamp, source actor, attempt number, status, and summary."
  - "`/app` can consume returned publish job detail records even before `/workflow` includes job collections."

requirements-completed: [FOUND-02, FOUND-03, FOUND-06, SEC-04, APPR-06, STATUS-01]

duration: 12m
completed: 2026-06-10
---

# Phase 01 Plan 04: Backend Publishing Foundation Summary

**React `/app` can queue backend fake publish jobs from approved snapshots and show per-platform lifecycle timelines without storing job history in localStorage**

## Performance

- **Duration:** 12m
- **Started:** 2026-06-10T18:32:00Z
- **Completed:** 2026-06-10T18:43:43Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `queueFakePublish(approvalId)` and `loadPublishJob(jobId)` client methods using relative `/api/v1` endpoints and existing JSON error handling.
- Added frontend lifecycle constants and normalizers for publish jobs, attempts, events, trace IDs, request digests, redacted diagnostics, current status, and approval snapshot media refs.
- Added `PublishTimeline` with all generic lifecycle states and fixed event rows for timestamp, actor/source, attempt number, status, and summary.
- Wired `/app` to show `Queue fake publish` only after a backend approval snapshot exists and no in-memory job is loaded for that approval.
- Kept fake publish job, attempt, event, diagnostic, and provider-like data out of browser localStorage; returned job details live only in React state.

## Task Commits

1. **Task 1: Add frontend fake publish client and lifecycle models** - `8331d62` (`feat`)
2. **Task 2: Add `Queue fake publish` and visible per-platform timeline UI** - `19516af` (`feat`)

## Files Created/Modified

- `src/api/publishingClient.js` - Adds fake publish queue and job lookup API methods.
- `src/models/publishing.js` - Adds lifecycle constants plus publish job, attempt, event, diagnostic, and status normalizers.
- `src/components/PublishTimeline.jsx` - Renders per-platform backend-backed fake publish timeline states and event rows.
- `src/main.jsx` - Wires approval IDs, in-memory returned jobs, queue action, workflow refresh, and timeline rendering into `/app`.
- `src/styles.css` - Adds `.publish-timeline-*` styles for fixed stepper, status chips, event rows, and empty states.

## Decisions Made

- Used backend approval IDs as the only queue input to preserve the Plan 03 server-owned fake publisher boundary.
- Loaded the returned publish job detail after queueing so the timeline can use backend attempt/event records immediately, without waiting for `/workflow` to include jobs.
- Rendered timeline empty states for every platform before approval so lifecycle visibility is present throughout the review flow.

## Verification

- `npm run test:approval` - passed after Task 1 and after Task 2.
- `npm run test:fake-publish` - passed after Task 1 and after Task 2.
- `npm run build` - passed after Task 1 and after Task 2.
- Local full-stack smoke via `npm run dev:full -- --port 5173` and Vite proxy:
  - `/app` served the React document through Vite.
  - `GET /api/v1/workflow` returned seeded Facebook/TikTok backend drafts.
  - `POST /api/v1/drafts/{draft_id}/approve` approved the Facebook draft.
  - `POST /api/v1/approvals/{approval_id}/publish` returned `ctaCopy: "Queue fake publish"`.
  - `GET /api/v1/publish-jobs/{job_id}` returned `published` with event statuses `approved`, `queued`, `publishing`, and `published`, actor sources, and attempt numbers.
- Source scan over plan files confirmed required lifecycle states, exact CTA copy, exact empty-state copy, and no new `localStorage` or credential-shaped strings in plan-owned source changes.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The Browser plugin did not expose a callable browser-control tool in this session; only Node REPL/Figma tools were available after tool discovery. Verification used the required automated commands plus full-stack HTTP smoke through the running Vite proxy.
- The first local API smoke raced backend readiness and received an empty response. Health checks then passed on both `127.0.0.1:8787` and the Vite proxy, and the guarded smoke rerun passed.
- Verification and dev-server runs generated Python cache directories and `.localpilot-dev/`; these generated outputs were removed and not staged.

## Known Stubs

None - `No publish jobs yet` is the required empty state copy, and the remaining placeholder text found by scan is existing form placeholder UI.

## Auth Gates

None - no external service authentication, OAuth flow, provider credential, or package installation was required.

## Threat Flags

None - the browser-to-publish endpoint, API-response-to-timeline UI, and localStorage boundary are covered by the plan threat model.

## User Setup Required

None.

## Next Phase Readiness

- Later retry and diagnostics plans can reuse `LIFECYCLE_STATES`, `normalizePublishJob`, and `PublishTimeline`.
- The frontend can display backend jobs immediately after queueing while remaining compatible with a future `/workflow` response that includes `publishJobs`.
- The hidden debug/admin surface can render the same normalized attempts, trace IDs, diagnostics, and events without duplicating lifecycle parsing.

## Self-Check: PASSED

- Summary file exists: `.planning/phases/01-backend-publishing-foundation/01-04-SUMMARY.md`.
- Created/modified plan files exist: `src/api/publishingClient.js`, `src/models/publishing.js`, `src/components/PublishTimeline.jsx`, `src/main.jsx`, and `src/styles.css`.
- Task commits exist: `8331d62`, `19516af`.
- No tracked file deletions were introduced by task commits.
- Generated verification outputs were removed; unrelated `.planning/STATE.md`, `.planning/config.json`, and `.vscode/` were not staged.

---
*Phase: 01-backend-publishing-foundation*
*Completed: 2026-06-10*
