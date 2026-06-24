---
quick_id: 260623-scribe-calendar-result-parity
status: in_progress
created: 2026-06-23
---

# Plan

Align the post-schedule Content Calendar result with the Scribe reference.

## Scope

- Route `Schedule Post` completion to Content Calendar instead of Content Library.
- Render monthly calendar cells with visual post thumbnail cards and platform/status markers.
- Keep existing calendar drawer behavior when a scheduled card is clicked.
- Update browser smoke coverage to verify the automatic calendar handoff and thumbnail cards.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
