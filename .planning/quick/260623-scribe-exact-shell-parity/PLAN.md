---
quick_id: 260623-scribe-exact-shell-parity
status: in_progress
created: 2026-06-23
description: Push creator workflow UI closer to Scribe exact shell parity
---

# Scribe Exact Shell Parity

## Goal

Make the LocalPilot creator-style workflow look much closer to the supplied Scribe/Predis screenshots.

## Current Mismatch

- Current UI is a centered rounded card modal over a blurred app.
- Scribe reference is a full app shell with a left sidebar and a page-like wizard area.
- Current modal has an extra large LocalPilot workflow header that the reference does not have.
- Actor/template grids use placeholder cards instead of the reference's large visual tile rhythm.

## Planned Fix

- Keep popup behavior technically, but make it a near full-screen reference shell.
- Add a Scribe-like sidebar inside the popup.
- Move wizard content into a page-like main area.
- Remove the oversized modal header from the visual hierarchy.
- Tune dimensions, footer, stepper, and grids to match reference proportions.

## Verification

- Capture updated screenshots for prompt, style, actor, template, review, and generated states.
- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
