---
quick_id: 260623-scribe-social-action-popups
status: complete
completed: 2026-06-23
---

# Summary

## What Changed

- Added Scribe-style centered social account dialogs with dark page backdrop.
- Wired Social Platforms `FAQ` buttons to platform-specific FAQ modals.
- Wired Instagram and other non-Facebook `Add` buttons to connection-choice modals.
- Preserved Facebook `Add` behavior through the existing secure OAuth handler.
- Wired `Watch Videos` buttons to visible setup-video dialogs instead of inert controls.
- Updated Phase 3 screen smoke to click and assert Instagram FAQ, Instagram Add, Instagram Videos, and TikTok FAQ modal states.

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
- `/bin/zsh -lc "PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens"`

## Notes

- Default Codex.app Node is signed with hardened runtime and rejects Rollup's native addon on this machine. Build verification passes when PATH is pinned to Homebrew Node first.
- The screenshot capture command that required escalated Chromium permissions was aborted, so this slice used local Scribe frame inspection plus Playwright smoke assertions as evidence.
