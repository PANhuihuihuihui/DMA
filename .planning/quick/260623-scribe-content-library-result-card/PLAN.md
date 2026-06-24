---
quick_id: 260623-scribe-content-library-result-card
status: in_progress
created: 2026-06-23
---

# Plan

Make the post-generation Content Library view closer to the Scribe result screen.

## Scope

- Stop masking the first library card with a forced cooking overlay after generation.
- Add a real video-card treatment with play affordance and edit pencil.
- Keep cooking state available only while backend creation is actually pending.
- Update browser smoke coverage to ensure the first generated card is not permanently masked.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
