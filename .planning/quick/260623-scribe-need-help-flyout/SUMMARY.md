---
quick_id: 260623-scribe-need-help-flyout
status: complete
completed: 2026-06-23
---

# Summary

## What Changed

- Changed sidebar `Need help` from full-page navigation into a compact Scribe-style flyout.
- Kept the current workspace visible when the flyout opens.
- Added `Chat Support` and `Book a Demo` flyout actions.
- Kept the existing full support center available through direct `/app?module=need-help` routing.
- Updated Phase 3 screen smoke to prove the flyout opens while Analytics remains visible.

## Reference Evidence

- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-50.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-51.jpg`

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
- `/bin/zsh -lc "PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens"`
