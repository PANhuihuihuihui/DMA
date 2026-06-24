---
quick_id: 260623-scribe-calendar-thumbnail-parity
status: complete
completed: 2026-06-23
---

# Summary

Moved the Content Calendar closer to the Scribe monthly calendar reference.

## Changes

- Updated the calendar title casing to `Content Calendar`.
- Changed the default calendar view to monthly.
- Reordered the view controls to `Today`, `Weekly`, `Monthly`.
- Moved status legend and timezone selector into a bottom calendar footer.
- Centered the month navigation above the grid.
- Tightened calendar post thumbnail sizing and kept media thumbnails in month cells.
- Updated browser smoke coverage to use the footer timezone selector and assert calendar reference copy.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Remaining Gap

The calendar shell and thumbnails now match the Scribe structure more closely, but exact pixel parity still requires fresh screenshot capture and real/generated media imagery.
