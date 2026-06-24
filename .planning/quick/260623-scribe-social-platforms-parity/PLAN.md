---
quick_id: 260623-scribe-social-platforms-parity
status: in_progress
created: 2026-06-23
---

# Plan

Move the Brand & Social Accounts social-platform list closer to the Scribe reference.

## Scope

- Replace abstract placeholder social rows with explicit platform rows.
- Show logo-like icons, provider name, account type, Watch Videos, FAQ, and Add actions.
- Expand the Facebook row with a connected-page card and unlink action.
- Keep secure OAuth/Page picker behavior available through the existing handlers.
- Update smoke coverage to assert the Scribe-style row copy.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
