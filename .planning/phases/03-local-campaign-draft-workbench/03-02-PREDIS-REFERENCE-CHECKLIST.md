---
phase: 03-local-campaign-draft-workbench
plan: 03-02
title: Predis Logged-In Reference Checklist
status: implemented-with-environment-gate
created: 2026-06-22
---

# 03-02 Predis Reference Checklist

This checklist translates the logged-in reference screenshots into LocalPilot implementation scope. The target is workflow parity and sales-demo credibility, not Predis impersonation. Do not copy Predis trademarks, logos, exact template artwork, or private implementation details.

## Scope Classification

| Reference moment | LocalPilot treatment | Status |
|---|---|---|
| Left-nav logged-in shell with persistent create action, trial/account card, and help entry | Ship now | Implemented |
| Inspirations landing with UGC Ads, Image Ads, category chips, and Recreate actions | Ship now | Implemented |
| Content Library grid with All/Image/Video/Carousel tabs and filters | Ship now | Implemented |
| Publish post modal with platform and post-type compatibility gating | Ship now | Implemented |
| Unsupported media warnings and missing-account route to account setup | Ship now | Implemented |
| Scheduled confirmation and auto-posting upsell | Ship now, reframed as owner-approved weekly autoplan | Implemented |
| Content Calendar with Weekly/Monthly toggle, Today, timezone, and status legend | Ship now | Implemented |
| Scheduled-post detail drawer with locked near-publish copy, Discard, and Reschedule | Ship now | Implemented |
| Brand & Social Accounts tabs for Social Platforms, Brand Details, Style, Integrations, and Exports | Ship now | Implemented |
| Facebook OAuth consent and Page picker | Ship now, official OAuth boundary only | Implemented as demo Page picker around existing OAuth-safe path |
| Analytics posting streak, consistency grid, and empty states | Ship now | Implemented |
| Help widget with support, FAQ, service status, and demo booking affordances | Demo placeholder | Implemented as local-only non-sending drawer |
| Create New chooser with Image, UGC, Short Ad Video, Carousel, Faceless Video, Product Photo Shoot | Ship now | Implemented |
| Image/UGC source methods: write idea, store or CSV, product URL, image upload | Ship now | Implemented |
| Carousel style and aspect-ratio setup before generation | Ship now | Implemented |
| Brand details website/social/hashtag fields | Ship now | Implemented with backend persistence |
| Brand style typography, light/dark logo refs, and color controls | Ship now | Implemented with backend persistence |
| E-commerce and product integrations | Demo placeholder | Implemented as non-credential placeholders |
| Content cooking progress overlay | Ship now | Implemented as deterministic UI state |
| Production Shopify/Wix/Squarespace/WooCommerce/Odoo integrations | Defer | Deferred until credential and API boundaries are deliberately planned |
| Production autonomous auto-posting | Must not ship | Replaced with explicit owner-approved autoplan language |
| Token or cookie posting flows | Must not ship | Preserved no-token browser boundary |

## Verification Mapping

| Gate | Coverage |
|---|---|
| `npm run test:phase3` | Backend workspace records, brand metadata persistence, no-secret brand payload boundary |
| `python3 -m unittest discover backend/tests -v` | Full backend regression suite, including Facebook OAuth/publisher, Phase 3, token boundary, retry/idempotency |
| `npm run test:storage-boundary` | Browser storage must not contain OAuth tokens, provider secrets, credentials, or publish-critical state |
| `npm run test:facebook-oauth` | Facebook OAuth route contract and no-token status responses |
| `scripts/smoke-phase3-screens.mjs` | New logged-in nav, Create New, Inspirations, Content Library, publish modal, Calendar, Brand & Social Accounts, Analytics, Help |
| `npm run build` | Production Vite bundle and Sites package preparation |

## Current Gate State

- Passing: backend Phase 3 tests, full backend unittest discovery, storage-boundary test, Facebook OAuth test, JSX parse check, and esbuild bundle check.
- Blocked in this local environment: Vite dev/build and Playwright screen smoke cannot start because Rollup's native `@rollup/rollup-darwin-arm64` binary fails macOS code-signature validation under the current Node 24 runtime.
- Required before marking fully verified: fix the local Node/Rollup runtime issue, then rerun `npm run build` and `npm run test:phase3-screens`.

## Guardrails Confirmed

- Facebook remains first for official direct publishing.
- TikTok remains assisted/deferred for direct production posting.
- Credentials, refresh tokens, app secrets, and OAuth tokens are not stored in browser localStorage.
- Publish and autoplan copy requires explicit owner approval before any real send.
- Proof language stays lower-bound and evidence-based, not exact ROI.
