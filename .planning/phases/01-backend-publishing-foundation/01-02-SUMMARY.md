---
phase: 01-backend-publishing-foundation
plan: 02
subsystem: frontend-api-approval
tags: [react, vite, publishing-api-client, approval-snapshot, localstorage-boundary]

requires:
  - phase: 01-backend-publishing-foundation
    plan: 01
    provides: backend `/api/v1/workflow` and `/api/v1/drafts/{draft_id}/approve` contracts
provides:
  - Browser publishing API client for backend workflow load and exact draft approval.
  - Frontend publishing normalizers for backend campaigns, drafts, media refs, connected-channel refs, token-boundary refs, and approval snapshots.
  - Guarded preference-only localStorage boundary.
  - React approval snapshot panel showing frozen backend approval payloads.
  - `/app` wiring from backend workflow records to selected platform review and approval UI.
affects: [phase-01, phase-03, facebook-publishing, tiktok-publishing, approval-workflow]

tech-stack:
  added: []
  patterns:
    - Plain fetch API client under `src/api/` with relative `/api/v1` URLs.
    - Frontend contract normalization under `src/models/`.
    - Preference-only browser storage helper under `src/storage/`.
    - Backend-returned approval snapshot rendered by a focused React component.

key-files:
  created:
    - src/api/publishingClient.js
    - src/models/publishing.js
    - src/storage/preferences.js
    - src/components/ApprovalSnapshot.jsx
  modified:
    - src/main.jsx
    - src/styles.css

key-decisions:
  - "Keep the current `/app` shell and module navigation, but derive campaign and platform draft state from `GET /api/v1/workflow`."
  - "Use the backend approval response and refreshed workflow approvals as the only source for frozen snapshot display."
  - "Keep browser localStorage constrained to language, demo session, active module, and selected UI indexes."

patterns-established:
  - "Approval UI sends `APPROVE_EXACT_VERSION`, draftVersionId, approver, and server media ref IDs to the backend."
  - "Frontend displays redacted `tokenBoundaryRef` metadata only; no credential-shaped fields are present under `src/`."
  - "Current dirty frontend visual/calendar edits were preserved as the working baseline for this plan."

requirements-completed: [FOUND-02, FOUND-06, SEC-01, SEC-02, SEC-04, SEC-06, APPR-04, APPR-05]

duration: 16m
completed: 2026-06-10
---

# Phase 01 Plan 02: Backend Publishing Foundation Summary

**React `/app` approval workflow now loads backend-owned Facebook/TikTok drafts and freezes exact draft-version approval snapshots from the API**

## Performance

- **Duration:** 16m
- **Started:** 2026-06-10T18:03:00Z
- **Completed:** 2026-06-10T18:18:28Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added a frontend publishing client for `GET /api/v1/workflow` and `POST /api/v1/drafts/{draft_id}/approve`.
- Added frontend normalizers mirroring backend workflow and approval snapshot contracts.
- Replaced `/app` publish-critical localStorage state with backend workflow-derived campaign, draft, media, connected-channel, token-boundary, and approval records.
- Added `ApprovalSnapshot` to show platform, draft version, approver, timestamp, idempotency suffix, target ref, caption/body, CTA, media refs, provider payload summary, disclosure/settings ref, and token boundary ref.
- Added approval snapshot and loading/error styles using the existing CSS token system.

## Task Commits

1. **Task 1: Add frontend API, models, and preference boundary** - `c685c3a` (`feat`)
2. **Task 2: Wire `/app` approval UI and frozen snapshot display** - `b9e75dc` (`feat`)

## Files Created/Modified

- `src/api/publishingClient.js` - Relative `/api/v1` workflow and exact-version approval fetch client with JSON error handling.
- `src/models/publishing.js` - Normalizes backend workflow, draft version, media ref, connected-channel ref, token-boundary ref, and approval snapshot payloads.
- `src/storage/preferences.js` - Allows only language, demo session, active module, and selected UI index preference keys.
- `src/components/ApprovalSnapshot.jsx` - Renders backend-returned immutable approval snapshots.
- `src/main.jsx` - Loads backend workflow records, maps backend drafts into the existing workspace UI, approves exact draft versions, and removes publish-critical localStorage usage.
- `src/styles.css` - Adds `.approval-snapshot-*`, `.workflow-state-panel`, and pending-state styles while preserving existing visual edits in the dirty baseline.

## Decisions Made

- Backend workflow records are the source of truth for `/app`; local React state only holds loading/error/UI selection state.
- The approval button label is `Approve exact draft` in the workbench, calendar, and approval queue surfaces.
- Approval snapshots are not rebuilt from mutable UI fields; they are rendered from backend approvals after approval and workflow refresh.
- Existing uncommitted frontend changes in `src/main.jsx` and `src/styles.css` were treated as the working baseline because this plan had to modify those same files.

## Verification

- `npm run test:approval` - passed after Task 1, after Task 2, and after final verification.
- `npm run build` - passed after Task 1, after Task 2, and after final verification.
- `rg -n "localpilot-demo-input|localpilot-demo-plans|localpilot-export-package|access_token|refresh_token|authorization|cookie|client_secret|api_key|oauth_payload|provider_raw|secretRef" src || true` - returned no matches after final verification.
- Full-stack local smoke through Vite proxy:
  - `GET http://127.0.0.1:5173/api/v1/workflow` returned Facebook and TikTok drafts with version 1, one media ref each, and token-boundary refs.
  - `POST http://127.0.0.1:5173/api/v1/drafts/draft_facebook_lunch/approve` returned an approved snapshot with media refs, token-boundary ref, and idempotency suffix `093e5d15`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Removed non-preference browser persistence outside the new storage boundary**
- **Found during:** Task 2
- **Issue:** The marketing pilot form still wrote `localpilot-pilot-request` directly to localStorage after the plan introduced a preference-only browser storage boundary.
- **Fix:** Removed that browser write and kept the prototype toast behavior.
- **Files modified:** `src/main.jsx`
- **Verification:** Final source scan found no direct publish-critical storage keys or credential-shaped terms under `src/`.
- **Committed in:** `b9e75dc`

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** The fix tightened the browser storage boundary without adding product scope.

## Issues Encountered

- Browser-plugin verification via Node REPL could not run because `playwright` is not installed in this repo/runtime. Package installation is outside this plan and prohibited by the supply-chain rule, so verification used build checks plus direct full-stack HTTP smoke through the existing Vite proxy.
- The first Vite-proxy smoke request raced backend startup and timed out before the backend printed ready. Re-running after health passed succeeded.

## Dirty Baseline Note

`src/main.jsx` and `src/styles.css` contained uncommitted frontend edits before this plan started. Task 2 built on those current files to avoid overwriting user work, so commit `b9e75dc` includes both the Plan 01-02 wiring and the preserved frontend baseline changes. Unrelated `.vscode/`, `.planning/config.json`, and pre-existing `.planning/STATE.md` changes were not staged.

## Known Stubs

None - stub scan found only defensive empty defaults and existing form placeholder attributes.

## Auth Gates

None - no external service authentication or provider credentials were required.

## Threat Flags

None - the browser-to-workflow API, API-response-to-React-state, and localStorage boundaries are covered by the plan threat model.

## User Setup Required

None.

## Next Phase Readiness

- Later Phase 1 plans can add fake publish jobs/timelines on top of the same frontend workflow and snapshot boundaries.
- Phase 3 can use `src/models/publishing.js` as the frontend contract layer for editable backend draft records.
- Facebook/TikTok phases inherit a UI that displays redacted token-boundary refs without exposing provider credentials.

## Self-Check: PASSED

- Created files exist: `src/api/publishingClient.js`, `src/models/publishing.js`, `src/storage/preferences.js`, `src/components/ApprovalSnapshot.jsx`.
- Modified files exist: `src/main.jsx`, `src/styles.css`.
- Task commits exist: `c685c3a`, `b9e75dc`.
- Final verification commands passed: `npm run test:approval`, `npm run build`, source safety scan, and full-stack HTTP smoke.
- No tracked file deletions were introduced by task commits.

---
*Phase: 01-backend-publishing-foundation*
*Completed: 2026-06-10*
