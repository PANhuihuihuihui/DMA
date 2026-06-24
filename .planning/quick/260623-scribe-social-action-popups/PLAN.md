---
quick_id: 260623-scribe-social-action-popups
status: in_progress
created: 2026-06-23
---

# Plan

Make Brand & Social Accounts row actions behave like the later Scribe workflow frames.

## Scope

- Add centered dark-backdrop social account dialogs for FAQ and Add actions.
- Match the visible Scribe modal structure: platform icon, title, close button, divider, rounded accordion/action rows.
- Wire FAQ buttons for Instagram/TikTok and other platforms to platform-specific FAQ lists.
- Wire Add buttons for Instagram and demo-only providers to a connection-choice dialog, while preserving Facebook OAuth behavior.
- Wire Watch Videos to an in-app tutorial dialog instead of an inert button.
- Update screen smoke coverage to click and verify FAQ/Add modal states.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
