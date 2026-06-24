---
quick_task: phase3-media-storyboard
status: in_progress
created: 2026-06-19
---

# Quick Task: Phase 3 Media Storyboard Assets

## Goal

Move LocalPilot closer to Predis-style media generation by adding backend-owned media/storyboard assets to generated Phase 3 creatives and surfacing them in the Creative Editor.

## Scope

- Add persisted media asset records for generated creatives.
- Seed/backfill media assets for existing Phase 3 demo creatives.
- Surface media/storyboard assets in the Creative Editor.
- Extend Phase 3 backend and browser smoke tests.
- Update GSD handoff/state artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
