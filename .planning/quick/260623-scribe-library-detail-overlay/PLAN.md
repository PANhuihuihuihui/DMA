---
quick_id: 260623-scribe-library-detail-overlay
status: in_progress
created: 2026-06-23
---

# Plan

Add the missing Scribe-style Content Library asset detail overlay.

## Scope

- Open a large preview/caption overlay from generated video cards.
- Show portrait media preview on the left and caption/input prompt/details on the right.
- Include Publish, Edit, Download, rating, overflow, and close actions.
- Route Publish from the detail overlay into the existing publish workflow.
- Update browser smoke coverage to exercise the detail overlay before publishing.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
