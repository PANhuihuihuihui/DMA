---
quick_id: 260623-scribe-prompt-avatar-fidelity
status: complete
completed: 2026-06-23
---

# Summary

Tightened the remaining high-visibility Scribe parity deltas in the creator workflow prompt and actor steps.

## Changes

- Changed prompt textarea rendering to normal input weight so it reads like typed user text rather than bold heading copy.
- Added a CSS-drawn wand icon to `Generate ideas for me`, matching the reference button rhythm without relying on emoji rendering.
- Added dedicated creator avatar preview image/crop data so actor tiles use people-heavy local assets instead of product/interior images.
- Kept the backend goal/form state intact while preserving the Scribe-like visible prompt step.

## Evidence

- `.planning/quick/260623-scribe-prompt-avatar-fidelity/screenshots/prompt-final.png`
- `.planning/quick/260623-scribe-prompt-avatar-fidelity/screenshots/actor-people-only.png`

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Remaining Gap

The workflow is closer to the Scribe reference, but exact avatar parity still requires licensed or generated avatar portrait assets. The current version uses available LocalPilot demo imagery cropped into portrait cards.
