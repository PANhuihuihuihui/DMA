---
quick_id: 260623-creator-workflow-modal-and-ui-audit
status: in_progress
created: 2026-06-23
description: Creator workflow modal and UI/button audit
---

# Creator Workflow Modal And UI/Button Audit

## Goal

Fix the creator-style video flow so it opens in a popup wizard and audit the affected Create New / Need Help buttons so the UI feels shippable instead of half-wired.

## Scope

- Move the creator-style video workflow into a modal window.
- Make the wizard steps explicit:
  - Generate ideas for me
  - Select idea
  - Select Motivational style
  - Select AI actor
  - Select scene/template
  - Generate
  - Generated creative + media asset + UGC package + calendar slot
  - Publish / Schedule Post handoff
- Keep backend-owned workflow artifacts from the previous slice.
- Fix Create New buttons that only toast or feel non-functional.
- Redesign Need Help into a stable support/help center layout.
- Update smoke coverage for modal workflow and Need Help actions.

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `npm run build`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
