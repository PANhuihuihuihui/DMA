---
quick_task: phase3-public-review-route
status: in_progress
created: 2026-06-19
---

# Quick Task: Phase 3 Public Review Route

## Goal

Turn the seeded approval review links into working app links so a client/owner can open a no-login review page, inspect the generated creative, and submit approval notes or change requests inside LocalPilot.

## Predis Evidence

Predis publicly describes approval parity as sharing a link to a post, with the approval and feedback process taking place inside the app.

## Scope

- Change demo review URLs from placeholder external URLs to local `/review/:token` routes.
- Add backend API to fetch a review package by token.
- Add backend API to submit review feedback by token.
- Add React `/review/:token` page with creative preview, review link state, feedback history, and owner actions.
- Extend backend tests and Playwright smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
- Targeted live local review-route smoke
