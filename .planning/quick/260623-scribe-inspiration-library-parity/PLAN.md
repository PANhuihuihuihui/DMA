# Scribe Inspiration Library Parity

## Goal

Move `Ad Inspirations` closer to Scribe steps 1-8 by rebuilding it as a Predis-style inspiration library rather than a generic LocalPilot campaign inspiration list.

## Reference Evidence

- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-01.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-03.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-05.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-07.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-08.jpg`

## Visible Reference Structure

- Main page title: `Inspirations`.
- Sections:
  - `Trending collection`
  - `UGC Ads`
  - `Image Ads`
- Section chips: `All`, `< 8 sec`, `>= 8 sec`, `Beauty`, `Fashion`, `Health and Wellness`, `Home and Living`, `Food and Beverage`, `Consumer Electronic`.
- `View all →` action on sections.
- Overlay CTA: `View all trending collection` / `View all ugc ads`.
- Collection view with back button, title, search field, active chips, and masonry grid.

## Scope

- Use local placeholder imagery through existing LocalPilot assets; do not copy Predis images.
- Keep existing `Recreate` behavior wired to the creator workflow.
- Add a collection view state for `View all` actions and chip interactions.
- Update future smoke assertions, but do not run full Phase 3 smoke until final parity.

## Verification

- `git diff --check`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
