---
quick_id: 260623-scribe-confirm-details-step
status: complete
completed: 2026-06-23
---

# Summary

Inserted the missing Scribe-style `Review and confirm your details` step between script review and final generation.

## Changes

- Added a separate `confirm` workflow step after `Review your script`.
- Moved the final `Generate` action from script review to the confirm step.
- Added the compact summary card with post type, aspect ratio, and estimated credit usage.
- Updated browser smoke coverage to verify script review, continue to confirm details, then generate.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Remaining Gap

The step order now matches the Scribe workflow more closely, but pixel-level spacing and proprietary icon treatment still require screenshot QA and licensed/generated assets.
