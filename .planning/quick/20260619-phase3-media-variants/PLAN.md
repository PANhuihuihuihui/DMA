---
quick_task: phase3-media-variants
status: in_progress
created: 2026-06-19
---

# Quick Task: Phase 3 Media Variants And Layer Edits

## Goal

Move the Creative Editor closer to Predis parity by making media layer edits and resize variants backend-owned records, not static preview labels.

## Scope

- Add backend operations for media asset layer edits and resize variants.
- Add API routes and frontend client functions.
- Add Creative Editor controls for saving layer edits and creating resize variants.
- Extend backend tests and Playwright screen smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
