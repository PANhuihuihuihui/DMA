---
quick_id: 260623-creator-workflow-modal-and-ui-audit
status: complete
completed: 2026-06-23
description: Creator workflow modal and UI/button audit
---

# Summary

Fixed the creator-style video workflow and Need Help UI after audit.

## Delivered

- Moved creator-style video workflow into a popup modal.
- Kept the full workflow wired:
  - Generate ideas for me
  - Select idea
  - Select Motivational style
  - Select AI actor
  - Select scene/template
  - Generate
  - Show generated creative, media asset, UGC package, and calendar slot
  - Publish / Schedule Post handoff
- Replaced the inline UGC workflow with a launcher card.
- Fixed Create New behavior so it no longer silently generates a default Image when no format is selected.
- Updated UGC Inspirations `Recreate` to open the popup workflow.
- Redesigned Need Help as a support center with selectable topics and a local draft panel.
- Updated browser smoke coverage for popup workflow, artifact display, and Need Help support-center actions.

## Evidence

- `screenshots/creator-workflow-modal.png`
- `screenshots/need-help-support-center.png`

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `npm run build`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
