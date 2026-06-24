---
quick_id: 260623-scribe-script-review-parity
status: complete
completed: 2026-06-23
---

# Summary

Rebuilt the creator workflow review step to match the Scribe reference's `Review your script` screen.

## Changes

- Renamed the review step title/subtitle to the script-review language.
- Replaced the generic summary card with a large script quote panel.
- Added the `Your script` tab, estimated duration pill, 8s/16s/24s rewrite controls, and script rewrite input.
- Made the rewrite input functional by appending the requested edit into the generation prompt.
- Updated the Phase 3 screen smoke to assert the new review UI and exercise the rewrite interaction before generation.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Remaining Gap

The workflow now follows the Scribe script-review structure, but exact visual parity still depends on continuing through the generated/editor/publish screens and replacing local placeholder media with licensed or generated assets.
