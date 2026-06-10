---
phase: 01-backend-publishing-foundation
plan: 08
subsystem: frontend-debug-diagnostics
tags: [react, vite, routes, debug-ui, support-diagnostics, redaction]

requires:
  - phase: 01-backend-publishing-foundation
    plan: 06
    provides: frontend approval, fake publish timeline, and retry behavior
  - phase: 01-backend-publishing-foundation
    plan: 07
    provides: read-only backend debug publish jobs endpoint
provides:
  - Hidden `/app/debug` direct-URL operator diagnostics route.
  - Separated React route tree preserving `/`, `/app`, and fallback navigation.
  - Debug API client method for `GET /api/v1/debug/publish-jobs`.
  - Safe workflow helpers for status labels, attempt counts, trace IDs, idempotency suffixes, and redacted debug summaries.
  - Responsive debug jobs table, details panel, and redacted diagnostics styles.
affects: [phase-01, support-diagnostics, facebook-publishing, tiktok-publishing, operator-workflows]

tech-stack:
  added: []
  patterns:
    - Route tree extracted under `src/routes/` while keeping large page components in `src/main.jsx`.
    - Hidden operator route consumes backend debug records through a plain relative API client.
    - Debug rendering uses frontend defensive summarizers before displaying diagnostics.

key-files:
  created:
    - src/routes/AppRoutes.jsx
    - src/routes/DebugRoute.jsx
    - src/publishing/workflow.js
  modified:
    - src/api/publishingClient.js
    - src/main.jsx
    - src/styles.css

key-decisions:
  - "Keep `/app/debug` as a direct URL route outside the merchant sidebar module registry."
  - "Extract only the route tree and debug workflow helpers, leaving existing marketing and `/app` component behavior intact."
  - "Render only redacted backend diagnostics and frontend-summarized values in the operator details panel."

patterns-established:
  - "`src/routes/AppRoutes.jsx` owns route definitions for `/`, `/app`, `/app/debug`, and fallback navigation."
  - "`src/publishing/workflow.js` centralizes support-safe workflow/debug derivations for future operator surfaces."
  - "`DebugRoute` keeps debug payloads in React state only and does not write diagnostics to localStorage."

requirements-completed: [FOUND-02, FOUND-06, SEC-03, SEC-06, APPR-06, STATUS-01, STATUS-02]

duration: 9m 53s
completed: 2026-06-10
---

# Phase 01 Plan 08: Backend Publishing Foundation Summary

**Hidden React operator diagnostics route for backend publish jobs with route extraction, safe debug summaries, trace copying, attempts, events, and redacted diagnostics**

## Performance

- **Duration:** 9m 53s
- **Started:** 2026-06-10T19:21:11Z
- **Completed:** 2026-06-10T19:31:04Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Extracted the React route tree into `src/routes/AppRoutes.jsx` while preserving `/`, `/app`, language provider behavior, translation layer behavior, and fallback navigation.
- Added `loadDebugPublishJobs()` for `GET /api/v1/debug/publish-jobs`.
- Added `src/publishing/workflow.js` helpers for status labels, current state, attempt counts, idempotency suffixes, trace IDs, safe diagnostics, and debug job summaries.
- Added hidden `/app/debug` with an operations table and details panel for merchant, platform, job status, attempt count, latest trace ID, error class, updated timestamp, next action, approval snapshot summary, attempts, events, media refs, approver, draft version, and redacted diagnostics.
- Added responsive `.debug-jobs-*` and `.redacted-diagnostics-*` styles with desktop table semantics and mobile row-card fallback.

## Task Commits

1. **Task 1: Extract route tree and add debug API client/helper boundary** - `1c7f518` (`feat`)
2. **Task 2: Build hidden `/app/debug` diagnostics UI** - `9c684dd` (`feat`)

## Files Created/Modified

- `src/api/publishingClient.js` - Adds `loadDebugPublishJobs()` for the backend debug endpoint.
- `src/routes/AppRoutes.jsx` - Owns `/`, `/app`, hidden `/app/debug`, and fallback route definitions.
- `src/routes/DebugRoute.jsx` - Renders the hidden operator diagnostics route from backend debug rows.
- `src/publishing/workflow.js` - Provides support-safe workflow/debug summary helpers.
- `src/main.jsx` - Exports `LandingPage` and `AppDemo`, imports the separated route tree, and preserves merchant module navigation.
- `src/styles.css` - Adds debug table, details, diagnostics, status, and responsive row-card styles.

## Decisions Made

- Kept the debug route hidden by routing it directly and not adding it to `modules`, `moduleDetails`, or the sidebar navigation.
- Kept debug data out of localStorage; the route loads diagnostics into component state only.
- Used the backend debug endpoint as the source of truth and applied a frontend defensive display filter for diagnostics before rendering.

## Verification

- `npm run test:debug` - passed after Task 1 and after Task 2; backend debug contract tests passed and Node smoke showed Facebook `published`, TikTok `published` after retry, attempts `{facebook: 1, tiktok: 2}`, and trace IDs only.
- `npm run build` - passed after Task 1 and after Task 2 with the extracted route tree and hidden debug route bundled.
- `rg -n "access_token|refresh_token|authorization|cookie|client_secret|api_key|oauth_payload|provider_raw|secretRef|credentialFingerprint" src/routes/DebugRoute.jsx src/publishing/workflow.js src/api/publishingClient.js src/routes/AppRoutes.jsx src/styles.css || true` - returned no matches.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

None - stub scan found only pre-existing form placeholder attributes in `src/main.jsx`, not debug/workflow stubs.

## Auth Gates

None - no external service authentication, OAuth flow, provider credential, or package installation was required.

## Threat Flags

None - the hidden route, debug endpoint consumption, token-boundary display, and redacted diagnostics rendering are covered by the plan threat model.

## User Setup Required

None.

## Next Phase Readiness

- Future operator/support work can extend `DebugRoute` and `src/publishing/workflow.js` without touching merchant navigation.
- Later Facebook/TikTok provider work can keep the same redacted diagnostics display while swapping fake provider diagnostics for official API diagnostics after backend redaction.
- The extracted route tree gives later frontend plans a stable place to add route-level surfaces without expanding `src/main.jsx`.

## Self-Check: PASSED

- Created/modified files exist: `src/api/publishingClient.js`, `src/routes/AppRoutes.jsx`, `src/routes/DebugRoute.jsx`, `src/publishing/workflow.js`, `src/main.jsx`, `src/styles.css`, and this summary.
- Task commits exist: `1c7f518` and `9c684dd`.
- Required verification commands passed after implementation: `npm run test:debug` and `npm run build`.
- No tracked file deletions were introduced by task commits.
- Unrelated `.planning/config.json` and `.vscode/` changes were not staged.

---
*Phase: 01-backend-publishing-foundation*
*Completed: 2026-06-10*
