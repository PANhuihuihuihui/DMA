---
quick_id: 260623-scribe-prompt-avatar-fidelity
status: in_progress
created: 2026-06-23
description: Tighten Scribe parity for prompt typography and avatar tile fidelity
---

# Scribe Prompt And Avatar Fidelity

## Goal

Move the creator workflow closer to the Scribe reference after the full-shell parity pass.

## Target Deltas

- Prompt textarea text should look like normal typed input, not bold heading text.
- `Generate ideas for me` should include a wand-style leading icon like the reference.
- Actor tiles should read more like portrait/avatar cards and less like mixed business/product photos.
- Keep the existing backend creator workflow behavior intact.

## Verification

- Recapture prompt and actor screenshots.
- `npm run build`
- Focused Playwright creator workflow smoke.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
