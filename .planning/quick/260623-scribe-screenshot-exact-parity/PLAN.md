---
quick_id: 260623-scribe-screenshot-exact-parity
status: in_progress
created: 2026-06-23
description: Scribe screenshot exact parity for creator-style workflow
---

# Scribe Screenshot Exact Parity

## Goal

Download the reference screenshots from the Scribe workflow and use them as the visible target for the LocalPilot creator-style video workflow.

## Reference URL

https://scribehow.com/o/WZELtEWDT3O4dqRkMjgDNg/viewer/Creating_AI-Generated_Creator_Style_Videos_on_Predis_ai__9hKf6X5GQrubPYTiaaEAMA?referrer=documents

## Scope

- Capture the Scribe workflow screenshots locally.
- Build a reference contact sheet and workflow notes.
- Compare the reference wizard screens against the current LocalPilot modal.
- Adjust UI structure and behavior to match the visible workflow as closely as possible:
  - Create New creator-style video popup
  - Generate ideas prompt step
  - Idea selection
  - Motivational style selection
  - AI actor selection
  - Scene/template selection
  - Generate
  - Generated output with publish/schedule handoff
- Keep LocalPilot legal/product boundaries:
  - do not copy proprietary Predis media assets into product UI
  - do not claim a real rendered video provider unless implemented
  - keep owner approval and account connection gating

## Verification

- Screenshot evidence in `reference/` and `screenshots/`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `npm run build`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
