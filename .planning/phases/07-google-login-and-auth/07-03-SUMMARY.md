---
phase: 07-google-login-and-auth
plan: 03
subsystem: auth
tags: [google-auth, dev-login, react, python]
requires:
  - phase: 07-01
    provides: Google auth backend endpoints, cookie session flow, and `google_auth.dev_login_enabled()`
  - phase: 07-02
    provides: Google sign-in modal and frontend auth client wiring
provides:
  - Backend auth capability endpoint exposing runtime dev-login availability
  - Frontend login gating aligned to backend dev-login runtime behavior
affects: [login-ui, google-auth, demo-auth]
tech-stack:
  added: []
  patterns:
    - Backend capability discovery through the existing unauthenticated JSON client
    - Login fallback visibility delegated to backend runtime gates
key-files:
  created:
    - .planning/phases/07-google-login-and-auth/07-03-SUMMARY.md
  modified:
    - backend/app/server.py
    - backend/tests/test_google_auth.py
    - src/api/publishingClient.js
    - src/main.jsx
key-decisions:
  - "Expose `devLoginEnabled` from `/api/v1/auth` and derive it directly from `google_auth.dev_login_enabled()`."
  - "Fetch auth capability only for the no-client-ID login path so Google sign-in behavior stays unchanged when configured."
patterns-established:
  - "UI login fallbacks are advertised only from backend runtime capability checks."
  - "Small unauthenticated capability endpoints can reuse `requestJson()` without adding a separate client path."
requirements-completed: [GAUTH-01, GAUTH-02]
duration: 15min
completed: 2026-06-25
---

# Phase 07 Plan 03: Google Login Dev-Gate Closure Summary

**Backend auth capability discovery now controls whether the login modal advertises dev login, so the UI only offers the fallback when the backend would actually accept it.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-06-25T17:11:28Z
- **Completed:** 2026-06-25T17:26:28Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added an unauthenticated backend auth capability endpoint that exposes `devLoginEnabled` from `google_auth.dev_login_enabled()`.
- Added focused backend tests for enabled and disabled capability responses.
- Updated the login modal to fetch backend auth capability before showing the dev-login fallback, while leaving the Google sign-in path unchanged when `VITE_GOOGLE_CLIENT_ID` is configured.

## Task Commits

Each task was committed atomically:

1. **Task 1: Expose backend auth capabilities for the login UI** - `df5e718` (fix)
2. **Task 2: Make the login modal respect backend dev-login gating** - `07bb996` (fix)

## Files Created/Modified
- `backend/app/server.py` - Adds `GET /api/v1/auth` with backend-owned `devLoginEnabled` capability.
- `backend/tests/test_google_auth.py` - Verifies enabled and disabled auth-capability responses.
- `src/api/publishingClient.js` - Adds `loadAuthCapabilities()` on the existing unauthenticated JSON client boundary.
- `src/main.jsx` - Gates the dev-login UI on backend capability loading instead of missing Vite client ID alone.

## Decisions Made
- Reused `google_auth.dev_login_enabled()` as the single backend source of truth instead of duplicating gating logic in the new endpoint.
- Scoped the frontend capability fetch to the no-client-ID modal path so configured Google sign-in remains exactly as before.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `src/main.jsx` already had unrelated local edits in the worktree. The auth-gating hunks were staged and committed selectively so those unrelated changes stayed out of the plan commits.

## Verification

- `python3 -m unittest backend.tests.test_google_auth -v` - passed, 19 tests
- `npm run build` - passed
- `rg -n '"/api/v1/auth"|devLoginEnabled|loadAuthCapabilities|Checking sign-in options|Google sign-in is not configured in this environment|backend dev login is enabled' backend/app/server.py backend/tests/test_google_auth.py src/api/publishingClient.js src/main.jsx` - confirmed capability endpoint, tests, client helper, and UI gating strings are present

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The frontend no longer shows `Dev Login` just because `VITE_GOOGLE_CLIENT_ID` is missing; it waits for backend capability and only advertises the fallback when `/api/v1/auth` returns `devLoginEnabled: true`.
- The Google sign-in path is unchanged when a browser Google client ID is configured.
- Residual risk: this plan did not add browser-level UI automation, so the final assurance on the modal state is source-verified and build-backed rather than exercised end to end in a running browser.

## Self-Check: PASSED

- Summary file exists on disk.
- Task commits `df5e718` and `07bb996` exist in git history.
