---
quick_task: phase3-ai-assistant-replies
status: complete
created: 2026-06-19
---

# Quick Task: Phase 3 AI Assistant Replies

## Goal

Move the AI Generator closer to Predis parity by making the in-app AI Assistant backend-owned: users can ask for post ideas or a content calendar outline, see saved assistant replies, and create posts from a reply with one click.

## Predis Evidence

Predis publicly describes an in-built AI chat where users ask the social media AI Assistant for post ideas or a content calendar outline, then use AI replies as input to create posts with a click.

## Scope

- Add backend persistence for AI Assistant replies.
- Add `POST /api/v1/phase3/ai-assistant/replies` to generate deterministic assistant replies.
- Add `POST /api/v1/phase3/ai-assistant/replies/:id/content-batch` to create posts from a saved reply.
- Serialize assistant replies through `GET /api/v1/phase3/workspace`.
- Update AI Generator UI with assistant prompt, saved replies, and `Create posts from reply`.
- Extend backend tests and Playwright smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
