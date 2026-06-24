---
quick_task: phase3-source-url-import
status: complete
created: 2026-06-19
---

# Quick Task: Phase 3 Source URL Import

## Goal

Move the AI Generator closer to Predis parity by allowing a local business source URL to be imported into the backend, analyzed into a content brief, and used as the seed for generated social posts.

## Predis Evidence

Predis publicly describes starting content generation from text prompts, product URLs/product links, or images, then producing launch-ready creatives and copy.

## Scope

- Add backend persistence for imported content/source URLs.
- Seed deterministic Aurora HVAC source URL data.
- Add `POST /api/v1/phase3/content-sources`.
- Serialize imported source records through `GET /api/v1/phase3/workspace`.
- Update AI Generator UI with source URL import, saved sources, and `Generate from source`.
- Extend backend tests and Playwright smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
- Targeted live local source-import smoke
