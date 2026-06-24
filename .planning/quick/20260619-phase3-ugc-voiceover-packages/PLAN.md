---
quick_task: phase3-ugc-voiceover-packages
status: complete
created_at: 2026-06-19T03:35:00Z
phase: 03-predis-replica-plus-proof-loop
completed_at: 2026-06-19T02:17:23Z
---

# Phase 3 UGC Voiceover Packages

## Evidence

- Predis.ai public home page says it can create UGC videos and product videos from prompts, product links, or images.
- Predis.ai also lists video with voiceover and video with UGC avatar as credit-consuming content types.
- LocalPilot has short-video storyboard assets, but not a backend-owned UGC/avatar/voiceover package record.

## Goal

Add backend-owned UGC voiceover packages so a generated creative can produce a customer-demo video package with avatar, script, scenes, captions, and export specs.

## Scope

- Add persistent UGC voiceover package records for generated creatives.
- Add an API route to create a package from an existing creative.
- Serialize packages through generated creative payloads.
- Add Creative Editor UI to generate and display UGC voiceover packages.
- Add backend and Playwright smoke coverage.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run build`
- `npm test`
