# Scribe Analytics Dashboard Parity

## Goal

Move the Analytics module closer to Scribe steps 47-48 by replacing the top LocalPilot-specific hero/card layout with the visible Predis-style analytics dashboard.

## Reference Evidence

- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-47.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-48.jpg`

## Visible Reference Structure

- Top social tabs: `Instagram`, `Aurora Heating & Cooling`, `LinkedIn`.
- Metric cards:
  - `New posts` with `2` and `21 May - 21 Jun`.
  - `Followers` with `0` and `21 May - 21 Jun`.
  - `Engagement` with `0` and `21 May - 21 Jun`.
- Chart cards:
  - `Your Posting Activity`
  - `Your Posts' Engagement`
  - `Your Followers' Growth`
- In step 48, the existing posting consistency block appears above the account tabs.

## Scope

- Render the reference analytics dashboard first in the viewport.
- Keep LocalPilot proof-loop controls below the reference analytics dashboard.
- Update future full-smoke assertions, but do not run full Phase 3 smoke until final parity.

## Verification

- `git diff --check`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
