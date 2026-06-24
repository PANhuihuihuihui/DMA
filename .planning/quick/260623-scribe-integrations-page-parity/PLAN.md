# Scribe Integrations Page Parity

## Goal

Replace the generic LocalPilot integrations placeholder grid with the Scribe-visible ecommerce integrations page from steps 55-56.

## Reference Evidence

- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-55.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-56.jpg`

## Visible Reference Structure

- Heading: `Integrations`
- Subtitle: `Connect your online store and link your products.`
- Trust cards:
  - `Used by over 20,000+`
  - `Rated 4.8`
  - `Verified by Shopify, WooCommerce and SquareSpace`
- Connector cards:
  - `Shopify`
  - `Wix`
  - `Squarespace`
  - `WooComm...`
- `or` separator.
- `Other E-Commerce Platforms` section.
- `Download Sample` link.
- Upload dropzone: `Click to upload or drag and drop`.

## Scope

- Use text/icon approximations only; do not copy external brand assets.
- Wire `Connect`, `Download Sample`, and upload dropzone to demo-safe local toasts or existing export behavior.
- Update future smoke assertions, but do not run full Phase 3 smoke until final parity.

## Verification

- `git diff --check`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
