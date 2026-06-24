---
quick_task: phase3-bulk-creative-variations
status: complete
created_at: 2026-06-19T03:05:00Z
phase: 03-predis-replica-plus-proof-loop
---

# Phase 3 Bulk Creative Variations

## Evidence

- Predis.ai public home page says it can create "Ad creatives and videos in bulk."
- It also says users can make "hundreds of variations in minutes" and test hooks, copy, and visuals.
- LocalPilot already has Idea Lab copy scoring, but not a bulk creative-variation run with visual directions.

## Goal

Add backend-owned bulk creative variations so a single generated creative can produce multiple hook/copy/visual direction cards for testing.

## Scope

- Add persistent bulk creative variation records.
- Add an API route to generate variations from an existing creative.
- Serialize variations through generated creative payloads.
- Add a Creative Editor panel and action for bulk variations.
- Add backend and Playwright smoke coverage.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run build`
