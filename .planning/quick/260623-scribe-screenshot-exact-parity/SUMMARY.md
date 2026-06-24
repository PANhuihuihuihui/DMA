---
quick_id: 260623-scribe-screenshot-exact-parity
status: complete
completed: 2026-06-23
---

# Summary

Captured the supplied Scribe workflow screenshots and rebuilt the LocalPilot creator-style video flow to follow that visible workflow pattern more closely.

## Reference capture

- Downloaded the Scribe page HTML to `/tmp/localpilot-scribe-workflow.html`.
- Extracted 56 unique step screenshots into `reference/steps/`.
- Generated `reference/steps.md`, `reference/steps.json`, `reference/contact-sheet.html`, and `reference/contact-sheet.png`.

## UI changes

- Converted the UGC creator flow from a multi-panel all-at-once modal into a step-by-step popup wizard:
  - prompt / Generate ideas for me
  - idea selection
  - script style with Motivational option and aspect ratio
  - AI actor selection grid
  - scene/template selection grid
  - review and confirm
  - generated creative preview with publish/schedule actions
- Reshaped the generated output into a two-column preview layout with media preview, caption, input prompt, backend artifact IDs/status, and Publish / Schedule Post handoff.
- Kept the product boundary clear: LocalPilot uses demo-safe generated placeholders and backend storyboard artifacts instead of copying Predis media or claiming a real video renderer.

## Backend changes

- Expanded creator-style options to match the reference-visible style labels:
  - Storytelling
  - Promotional
  - Motivational
  - Exploratory
- Expanded AI actor and template fixtures so the frontend can render a real selectable grid.
- Passed creator aspect ratio into generated media assets.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Evidence

- Reference contact sheet: `reference/contact-sheet.png`
- Current UI screenshots:
  - `screenshots/localpilot-create-new.png`
  - `screenshots/localpilot-wizard-prompt.png`
  - `screenshots/localpilot-wizard-ideas.png`
  - `screenshots/localpilot-wizard-style.png`
  - `screenshots/localpilot-wizard-actor.png`
  - `screenshots/localpilot-wizard-template.png`
  - `screenshots/localpilot-wizard-review.png`
  - `screenshots/localpilot-wizard-generated.png`

## Running service

- Web: `http://127.0.0.1:4173/app?module=create-new`
- API: `http://127.0.0.1:8787`
