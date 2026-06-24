---
quick_task: phase3-approval-feedback-loop
status: in_progress
created: 2026-06-19
---

# Quick Task: Phase 3 Approval Feedback Loop

## Goal

Move Phase 3 closer to Predis parity by adding a backend-owned approval feedback loop for generated posts: shareable review links, owner/client comments, change requests, and approval notes.

## Predis Evidence

Predis publicly describes a complete approval/feedback loop where users share a link to a post and the approval process happens inside the app.

## Scope

- Add backend persistence for approval review links and approval feedback comments.
- Seed deterministic Aurora HVAC review links/comments for the demo.
- Serialize approval feedback through `GET /api/v1/phase3/workspace`.
- Add an API route for appending approval feedback.
- Add Approval Queue UI showing review link, recent feedback, and quick actions for approval notes or requested changes.
- Extend backend and Playwright smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- Targeted live API smoke
