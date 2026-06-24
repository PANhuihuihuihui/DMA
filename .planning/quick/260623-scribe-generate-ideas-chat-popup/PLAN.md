---
quick_id: 260623-scribe-generate-ideas-chat-popup
status: in_progress
created: 2026-06-23
description: Add Scribe-style Generate ideas chat popup to creator workflow
---

# Scribe Generate Ideas Chat Popup

## Goal

Match the Scribe reference flow where `Generate ideas for me` opens a focused chat popup over the dimmed creator workflow shell before idea selection.

## Planned Changes

- Add a nested generate-ideas chat modal inside the creator workflow.
- Reuse the current backend creator idea generation endpoint.
- Let the chat send update the hidden goal context and then populate/select ideas.
- Keep the existing prompt step and `Continue` flow intact.

## Verification

- Capture prompt, chat popup, and idea selection screenshots.
- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
