---
quick_id: 260623-scribe-need-help-flyout
status: in_progress
created: 2026-06-23
---

# Plan

Align `Need help?` with the Scribe sidebar flyout behavior.

## Scope

- Make the sidebar `Need help` nav item open a compact sidebar flyout instead of navigating away from the current module.
- Keep the main workspace unchanged when the flyout opens.
- Add flyout actions for `Chat Support` and `Book a Demo`.
- Preserve the existing full Help support center for direct `/app?module=need-help` access.
- Update screen smoke to assert that `Need help` opens the flyout while Analytics remains on screen.

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
- `/bin/zsh -lc "PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens"`
