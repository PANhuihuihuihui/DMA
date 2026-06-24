---
quick_id: 260623-scribe-calendar-thumbnail-parity
status: in_progress
created: 2026-06-23
---

# Plan

Move the Content Calendar closer to the Scribe monthly calendar reference.

## Scope

- Render scheduled posts as compact media thumbnails inside month cells.
- Add Scribe-style status/time rows and Facebook badge under each thumbnail.
- Adjust the calendar toolbar/legend/timezone placement toward the reference.
- Keep the existing detail drawer and smoke coverage intact.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
