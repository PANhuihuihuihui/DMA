---
id: T02
parent: S01
milestone: M002
key_files:
  - src/components/PublishTimeline.jsx
  - src/main.jsx
key_decisions:
  - Use module-scope pure helpers (fallbackHintText, isAuthError) rather than inline ternaries to keep the JSX readable and the mapping testable
  - Target 'Brand & Social Accounts' as the onReconnect destination — confirmed via modules array and the connected-accounts module alias
  - Gate the Reconnect button on both isAuthError(errorClass) && onReconnect so the component is safe when used without the prop (e.g., non-Facebook timelines or tests)
duration: 
verification_result: passed
completed_at: 2026-06-26T06:36:07.303Z
blocker_discovered: false
---

# T02: Added manual-fallback-hint block with error-class-aware hint text and Reconnect CTA to PublishTimeline; wired onReconnect to Brand & Social Accounts navigation in both call sites

**Added manual-fallback-hint block with error-class-aware hint text and Reconnect CTA to PublishTimeline; wired onReconnect to Brand & Social Accounts navigation in both call sites**

## What Happened

PublishTimeline showed manual_fallback_required status but gave no actionable guidance. Added two pure-helper functions at module scope: `fallbackHintText(errorClass)` maps the four error-class branches (authentication, missing_permission, validation, rate_limit, default) to human-readable strings, and `isAuthError(errorClass)` guards the Reconnect CTA. Added `onReconnect` to the component's prop signature. After the lifecycle steps `<ol>`, a new `<div className="manual-fallback-hint">` conditionally renders when `currentStatus === 'manual_fallback_required'`: it displays the error-class hint paragraph and, when `isAuthError(latestAttempt?.errorClass) && onReconnect`, a `<button className="manual-fallback-reconnect">` that calls `onReconnect()`. Both PublishTimeline usages in main.jsx received `onReconnect={() => setActiveModule("Brand & Social Accounts")}` — the module name for the Facebook page connection flow confirmed via the modules array and the `connected-accounts` alias. The chunk-size warning in the build output is a pre-existing condition unrelated to this change.

## Verification

grep -q 'manual-fallback-hint' src/components/PublishTimeline.jsx (exit 0); grep -n onReconnect in PublishTimeline.jsx shows prop signature + button guard; grep -n onReconnect src/main.jsx shows both usages at lines 6850 and 7845 navigating to Brand & Social Accounts; vite build exits 0 (57 modules, built in 1.05s, 0 errors).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -n 'manual-fallback-hint' src/components/PublishTimeline.jsx` | 0 | pass — line 168: div className='manual-fallback-hint' | 5ms |
| 2 | `grep -n onReconnect src/components/PublishTimeline.jsx src/main.jsx` | 0 | pass — prop in signature (line 134), button guard (line 170-171), both main.jsx usages (lines 6850, 7845) | 5ms |
| 3 | `node_modules/.bin/vite build --outDir /tmp/localpilot-verify-t02` | 0 | pass — built in 1.05s, 0 errors | 1286ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/components/PublishTimeline.jsx`
- `src/main.jsx`
