---
quick_id: 260623-scribe-script-review-parity
status: in_progress
created: 2026-06-23
---

# Plan

Align the creator workflow review step with the Scribe reference screen.

## Scope

- Replace the generic review summary with a script-review surface.
- Add the large script card, duration badge, rewrite duration controls, and rewrite prompt input.
- Keep the existing backend generation handoff intact.
- Update smoke coverage so the script-review UI is asserted before generation.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
