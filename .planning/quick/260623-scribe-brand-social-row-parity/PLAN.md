---
quick_id: 260623-scribe-brand-social-row-parity
status: in_progress
created: 2026-06-23
---

# Plan

Align the Brand & Social Accounts social-platform tab with the Scribe reference.

## Scope

- Replace grid cards with Scribe-style horizontal provider rows.
- Show Add, FAQ, and Watch Videos actions per platform.
- Keep the connected Facebook page visible as an expanded account card with Unlink.
- Preserve existing Facebook connection behavior.
- Update browser smoke coverage for the row-based social account screen.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
