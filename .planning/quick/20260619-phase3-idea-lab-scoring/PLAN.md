---
quick_task: phase3-idea-lab-scoring
status: complete
created: 2026-06-19
---

# Quick Task: Phase 3 Idea Lab Scoring

## Goal

Move the Creative Editor closer to Predis parity by generating multiple scored messaging variations for a creative, showing AI scoring/rationale, and letting the user apply the winning variant back to the backend-owned creative.

## Predis Evidence

Predis publicly describes generating multiple variations for testing, an Idea Labs feature that suggests varied messaging, and AI scoring that helps fine-tune creatives against objectives.

## Scope

- Add backend persistence for creative idea variants and AI scoring.
- Add `POST /api/v1/phase3/creatives/:id/idea-variants` to generate deterministic variants.
- Add `POST /api/v1/phase3/idea-variants/:id/apply` to apply one variant to the creative.
- Serialize variants through generated creatives in `GET /api/v1/phase3/workspace`.
- Add Creative Editor UI for Idea Lab generation, score cards, rationale, and apply action.
- Extend backend tests and Playwright smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
