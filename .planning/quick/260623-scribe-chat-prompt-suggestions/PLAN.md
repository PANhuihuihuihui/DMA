---
quick_id: 260623-scribe-chat-prompt-suggestions
status: in_progress
created: 2026-06-23
description: Add Scribe-style prompt suggestion cards inside the generate-ideas chat
---

# Scribe Chat Prompt Suggestions

## Goal

Match the Scribe generate-ideas popup after goal submission: the chat should show `Here are 2 prompts for you` with prompt cards and `Use This Prompt` actions.

## Planned Changes

- Keep the chat popup open after backend idea generation.
- Render two backend-derived prompt suggestions inside the chat.
- Add `Use This Prompt` actions that select the idea/prompt and continue the creator workflow.
- Update the screen smoke to test the prompt suggestion path.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
