---
quick_id: 260622-ojl
status: complete
completed: 2026-06-23
description: Scribe creator-style video workflow parity
---

# Summary

Implemented the referenced Predis creator-style video workflow as a backend-owned LocalPilot flow.

## Delivered

- Reviewed the Scribe workflow and extracted the core path:
  - Inspirations
  - Create New
  - creator-style video with AI-generated actors
  - describe prompt
  - generate ideas
  - choose style
  - choose actor
  - choose scene/template
  - generate
  - publish/schedule
- Added backend `creator_style_workflows` state with deterministic seeded options.
- Added API endpoints:
  - `POST /api/v1/phase3/creator-style-video-workflows`
  - `POST /api/v1/phase3/creator-style-video-workflows/:id/generate`
- Generation now creates linked backend artifacts:
  - generated creative
  - media storyboard asset
  - UGC voiceover package
  - calendar slot
  - proof link
  - approval review link
- Reworked the Create New UGC card into a creator-style video wizard.
- Updated Inspirations so UGC Recreate loads the creator-style wizard instead of making a generic batch.
- Updated Phase 3 screen smoke to click through the new wizard.

## Evidence

- Current wizard screenshot:
  - `screenshots/current/creator-style-wizard.png`
- Generated state screenshot:
  - `screenshots/current/creator-style-generated.png`

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `npm run build`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
