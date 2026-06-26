---
id: T01
parent: S01
milestone: M002
key_files:
  - src/main.jsx
key_decisions:
  - Normalize loadFacebookPages response with dual fallback (data?.pages then Array.isArray(data)) to handle both {pages:[]} and raw array shapes without knowing the exact backend contract
  - Use hidden={!pendingConnectSession} instead of conditional rendering to preserve demo section structure
  - Wire page card onClick conditionally (real flow vs demo) so existing demo behavior is undisturbed
  - Clear connectSession via navigate(..., {replace:true}) to keep React Router location state in sync
duration: 
verification_result: passed
completed_at: 2026-06-26T06:34:21.536Z
blocker_discovered: false
---

# T01: Wired connectSession URL param to inline Facebook Page picker — real OAuth redirects now trigger page listing and selection

**Wired connectSession URL param to inline Facebook Page picker — real OAuth redirects now trigger page listing and selection**

## What Happened

The backend split-OAuth flow (D11) was already complete: complete_callback redirected to the UI with a `connectSession` query param, and `/facebook/pages?connectSession=...` + `/facebook/pages/select` routes existed. The frontend URL-params useEffect only handled `facebookConnected=1` and ignored `connectSession`, so merchants were stuck after OAuth.

Changes made to `src/main.jsx`:

1. **Imports**: Added `loadFacebookPages` and `selectFacebookPage` to the import block from `./api/publishingClient.js`.

2. **State**: Added `connectSessionPages` (array) and `pendingConnectSession` (string) state variables alongside the existing `selectedFacebookPageId`.

3. **useEffect extension** (location.search effect): Added a `connectSession` branch — when the param is present, calls `loadFacebookPages(connectSession)`, stores pages in `connectSessionPages`, stores the session token in `pendingConnectSession`, and switches the Brand Accounts tab to "Social Platforms" so the picker is immediately visible. Errors surface as an app toast.

4. **`handleConnectSessionPageSelect` handler**: Async handler that calls `selectFacebookPage(pendingConnectSession, pageId)`, then `reloadFacebookConnection()` to update the connected pages display, clears `pendingConnectSession` and `connectSessionPages`, removes the `connectSession` param from the URL via `navigate(..., { replace: true })` (no reload), and shows a success toast. On error: shows a toast and clears `pendingConnectSession`.

5. **facebook-page-picker section**: Changed `hidden` (always hidden) to `hidden={!pendingConnectSession}` — the picker is only visible during a real OAuth session. Page cards now use `connectSessionPages` when `pendingConnectSession` is set (fallback to demo `pagePickerPages`). Card `onClick` uses `handleConnectSessionPageSelect` during the real flow and the existing `setSelectedFacebookPageId` for the demo mode. The existing "Save selected Page" demo button remains unchanged.

Build confirmed clean (vite production build, 0 errors, 57 modules transformed).

## Verification

grep -q 'connectSession' src/main.jsx (pass); vite production build exit 0 — 57 modules transformed, no errors.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -n connectSession src/main.jsx` | 0 | pass — 10 matching lines covering state, useEffect branch, handler, and JSX | 5ms |
| 2 | `node_modules/.bin/vite build --outDir /tmp/localpilot-verify-build` | 0 | pass — 57 modules transformed, built in 988ms, 0 errors | 1202ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/main.jsx`
