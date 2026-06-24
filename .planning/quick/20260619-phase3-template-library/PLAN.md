---
quick_task: phase3-template-library
status: in_progress
created: 2026-06-19
---

# Quick Task: Phase 3 Template Import And Asset Library

## Goal

Move the Creative Editor closer to Predis parity by adding backend-owned template import and premium asset library records that can be applied to generated creatives.

## Scope

- Add Phase 3 backend tables for creative templates, imported templates, and premium/local asset library items.
- Seed deterministic demo templates and assets for Aurora Heating & Cooling.
- Add an import/apply endpoint for Canva/Adobe/Figma-style templates.
- Serialize templates, imported templates, and asset library items in the Phase 3 workspace.
- Add a Creative Editor panel for template import and asset library selection.
- Extend backend and Playwright smoke tests.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
