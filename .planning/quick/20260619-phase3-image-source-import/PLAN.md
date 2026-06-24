---
quick_task: phase3-image-source-import
status: complete
created: 2026-06-19
---

# Quick Task: Phase 3 Image Source Import

## Goal

Move the AI Generator closer to Predis parity by allowing a local business image/product photo to be imported into the backend, analyzed into a content brief, and used as the seed for generated social posts.

## Predis Evidence

Predis publicly describes starting generation from text prompts, product links/product URLs, or images/product images, then producing creatives, copy, videos, and calendar-ready content.

## Scope

- Extend `POST /api/v1/phase3/content-sources` so it supports image source imports in addition to URLs.
- Persist uploaded image metadata and a demo-safe preview reference through backend-owned `content_sources`.
- Serialize image source previews through `GET /api/v1/phase3/workspace`.
- Update AI Generator UI with image upload, saved image source cards, and `Generate from source`.
- Extend backend tests and Playwright smoke coverage.
- Update Phase 3/GSD handoff artifacts.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
- Live local source-image import smoke if time permits
