---
quick_task: phase3-performance-analytics
status: in_progress
created: 2026-06-19
---

# Quick Task: Phase 3 Performance Analytics Dashboard

## Goal

Move the Proof Loop closer to Predis parity by adding backend-owned performance analytics snapshots and insights, while preserving LocalPilot's lower-bound evidence guardrail.

## Scope

- Add backend persistence for Phase 3 performance snapshots and analytics insights.
- Seed deterministic platform/creative performance records for the Aurora HVAC demo.
- Serialize analytics records through the Phase 3 workspace.
- Add a visible analytics dashboard panel with performance totals, channel breakdowns, top creative, and confidence notes.
- Extend backend tests and Playwright smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
