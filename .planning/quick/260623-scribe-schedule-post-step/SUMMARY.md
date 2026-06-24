---
quick_id: 260623-scribe-schedule-post-step
status: complete
completed: 2026-06-23
---

# Summary

Added the missing Scribe-style `Schedule post` step after the publish destination selection.

## Changes

- Extended publish draft state with a `platform` / `schedule` step and schedule fields.
- Changed publish `Continue` to advance into the schedule step instead of immediately confirming.
- Added the calendar, time picker, AI suggested time checkbox, approval checkbox, Back, and Schedule Post controls.
- Kept owner-approval scheduling behavior and returned to Content Library after scheduling.
- Updated browser smoke coverage to verify the schedule step and complete with `Schedule Post`.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Remaining Gap

The scheduling sequence now matches the Scribe flow structurally, but exact pixel parity still requires visual screenshot QA and real platform account state.
