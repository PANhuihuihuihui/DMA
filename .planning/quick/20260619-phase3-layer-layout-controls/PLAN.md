---
quick_task: phase3-layer-layout-controls
status: complete
created_at: 2026-06-19T02:35:00Z
phase: 03-predis-replica-plus-proof-loop
---

# Phase 3 Layer Layout Controls

## Evidence

- Predis.ai public copy says generated creatives can be edited and exported.
- Predis.ai home page also says it gives users "complete control over all layers and elements of the ad creative."
- LocalPilot already has structured layer controls; this slice adds layout/reorder movement so the editor feels closer to a real creative tool.

## Goal

Add backend-owned drag/drop-style creative layer layout controls for generated media assets.

## Scope

- Persist layer layout metadata in each media asset.
- Add an API route to update a selected layer's placement/order/size.
- Add UI controls in Creative Editor for moving a layer up/down and changing placement.
- Serialize refreshed media assets through the existing workspace.
- Add backend and Playwright smoke coverage.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run build`
