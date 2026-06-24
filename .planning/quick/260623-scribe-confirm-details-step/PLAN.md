---
quick_id: 260623-scribe-confirm-details-step
status: in_progress
created: 2026-06-23
---

# Plan

Add the missing Scribe-style `Review and confirm your details` step after script review and before final generation.

## Scope

- Insert a separate confirm step into the creator workflow.
- Render the compact summary card with post type, aspect ratio, and estimated credit usage.
- Keep generation on the confirm step, not the script-review step.
- Update browser smoke coverage to verify both script-review and confirm-details screens.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
