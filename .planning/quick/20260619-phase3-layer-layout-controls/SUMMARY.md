---
quick_task: phase3-layer-layout-controls
status: complete
completed_at: 2026-06-19T02:48:00Z
phase: 03-predis-replica-plus-proof-loop
---

# Phase 3 Layer Layout Controls Summary

## What Changed

- Added backend-owned layer layout metadata to creative media asset layer controls.
- Added `POST /api/v1/phase3/media-assets/:id/layer-layout` to move/reposition a selected layer.
- Added store function `update_creative_media_layer_layout`.
- Creative Editor now shows layer order and percentage-based position metadata.
- Creative Editor now exposes a `Move layer` action alongside `Apply layer edit`.
- Added backend and browser-smoke coverage for layer layout moves.

## Predis Evidence

- Fresh public Predis copy says generated creatives are editable and that Predis gives users complete control over all layers and elements.
- This slice adapts that claim into a backend-owned local demo editor without introducing browser automation or paid-ad campaign booking.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run build`

## Notes

- This is drag/drop-style movement through deterministic controls, not yet freeform pointer dragging.
- Layer layout edits are persisted as media asset metadata and returned through the normal Phase 3 workspace.
