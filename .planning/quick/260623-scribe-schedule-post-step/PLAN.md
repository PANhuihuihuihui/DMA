---
quick_id: 260623-scribe-schedule-post-step
status: in_progress
created: 2026-06-23
---

# Plan

Add the missing Scribe-style `Schedule post` step after selecting a publish destination.

## Scope

- Change publish modal `Continue` to advance to a schedule step.
- Render the calendar/time picker, AI suggested time checkbox, approval checkbox, Back, and Schedule Post controls.
- Keep the existing owner-approval handoff and confirmation behavior after scheduling.
- Update browser smoke coverage to verify the schedule step before the modal closes.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
