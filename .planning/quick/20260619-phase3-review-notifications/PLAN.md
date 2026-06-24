---
quick_task: phase3-review-notifications
status: in_progress
created: 2026-06-19
---

# Quick Task: Phase 3 Review-Link Notifications

## Goal

Move the Phase 3 approval flow closer to Predis parity by adding a backend-owned notification/outbox layer for shared review links, so the demo can show that a review link was sent to a client/owner and can be tracked from the Approval Queue.

## Predis Evidence

Predis publicly describes approval parity as sharing a link to the post and keeping approval/feedback inside the app.

## Scope

- Add backend persistence for review-link notification records.
- Seed deterministic Aurora HVAC review notification history.
- Add API to send/create a review notification for a generated creative or review link.
- Serialize notification records through the Phase 3 workspace and nested review link data.
- Update Approval Queue UI to show notification status and a `Send review link` action.
- Extend backend tests and Playwright smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
- Targeted live local notification smoke
