---
quick_task: phase3-layer-controls
status: in_progress
created: 2026-06-19
---

# Quick Task: Phase 3 Structured Layer Controls

## Goal

Move the Creative Editor closer to Predis parity by replacing one-note media edits with backend-owned structured layer controls for generated creative assets.

## Scope

- Add backend support for named layer-control updates on Phase 3 creative media assets.
- Preserve layer edit history and expose normalized controls in workspace serialization.
- Make rendered preview outputs reflect edited headline/CTA/brand-color controls where available.
- Add Creative Editor UI for applying visible layer-level edits.
- Extend backend and Playwright smoke tests.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
