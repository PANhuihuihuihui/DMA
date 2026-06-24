---
quick_id: 260623-scribe-subtitle-style-picker
status: in_progress
created: 2026-06-23
description: Convert creator workflow template step into Scribe-style subtitle picker
---

# Scribe Subtitle Style Picker

## Goal

Move the post-avatar workflow step closer to the Scribe reference, which shows `Pick Subtitle style` with a two-column scrollable grid of grey subtitle preview cards.

## Planned Changes

- Rename the visible step from `Select scene/template` to `Pick Subtitle style`.
- Replace metadata-heavy template cards with large subtitle preview cards.
- Preserve `templateId` as the backend selection field so generation still works.
- Tune CSS to match the reference card rhythm, typography, and scroll area.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
