---
quick_id: 260623-scribe-subtitle-style-picker
status: complete
completed: 2026-06-23
---

# Summary

Converted the creator workflow template step into a Scribe-style subtitle picker.

## Changes

- Renamed the visible step from `Select scene/template` to `Pick Subtitle style`.
- Updated the subtitle to match the reference: `Choose how subtitles will show in the UGC Video.`
- Replaced metadata-heavy template cards with large grey subtitle preview cards.
- Added outlined/highlighted caption text variations to mimic the Scribe subtitle-style tiles.
- Updated creator workflow copy and review summary from `Scene/template` to `Subtitle style`.
- Updated the Phase 3 screen smoke expectation for the new review copy.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Remaining Gap

The subtitle style grid is much closer structurally, but it still uses CSS-generated preview text rather than exact extracted Scribe bitmap previews.
