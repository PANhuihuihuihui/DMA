---
quick_id: 260623-scribe-exact-shell-parity
status: complete
completed: 2026-06-23
---

# Summary

Moved the creator workflow closer to the supplied Scribe/Predis reference screenshots.

## Changes

- Changed the workflow from a rounded card floating over a gray backdrop into a full-screen reference-style app shell.
- Added a left navigation rail inside the workflow with reference-like create, auto-posting, module, trial, and account blocks.
- Reworked the first step to match the Scribe prompt flow: visible idea textarea plus `Generate ideas for me`, with backend goal state preserved internally.
- Replaced abstract actor placeholders with large visual tile cards using local reference assets.
- Tuned stepper, title, wizard content offset, footer, prompt textarea, filter tabs, actor grid, and template grid spacing.
- Updated Phase 3 screen smoke expectations to assert the new Scribe-style workflow copy.

## Evidence

- Refined screenshots:
  - `.planning/quick/260623-scribe-exact-shell-parity/screenshots/refined2/prompt.png`
  - `.planning/quick/260623-scribe-exact-shell-parity/screenshots/refined2/actor.png`
  - `.planning/quick/260623-scribe-exact-shell-parity/screenshots/refined/generated.png`
- Reference anchors:
  - `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-12.jpg`
  - `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-22.jpg`

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- Focused Playwright smoke passed through the creator workflow actor step with no React warnings/errors.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Remaining Gaps

- The shell and workflow proportions are now much closer, but the app still uses LocalPilot branding and local demo assets rather than Predis proprietary branding/avatar media.
- Exact pixel parity would require either licensed/reference-equivalent avatar assets or an approved synthetic avatar asset set.
