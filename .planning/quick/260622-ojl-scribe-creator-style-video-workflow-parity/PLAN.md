---
quick_id: 260622-ojl
status: in_progress
created: 2026-06-22
description: Scribe creator-style video workflow parity
---

# Scribe Creator-Style Video Workflow Parity

## Goal

Make LocalPilot's Create New flow work like the referenced Predis creator-style video workflow, including the required backend state for the frontend.

Reference:
https://scribehow.com/o/WZELtEWDT3O4dqRkMjgDNg/viewer/Creating_AI-Generated_Creator_Style_Videos_on_Predis_ai__9hKf6X5GQrubPYTiaaEAMA?referrer=documents

## Scope

- Convert the Create New UGC path into a creator-style video wizard:
  - Prompt
  - Generate ideas
  - Goal
  - Style/tone
  - AI actor
  - Scene/template
  - Generate
  - Publish/schedule handoff
- Add backend-owned workflow records and deterministic demo generation.
- Surface generated creator-style videos in Content Library and Content Calendar.
- Keep owner approval required before real publishing.
- Verify with backend tests, frontend build, and Phase 3 screen smoke.

## Reference Workflow Notes

See `SCRIBE-WORKFLOW.md` for the Scribe extraction summary.

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `npm run build`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
