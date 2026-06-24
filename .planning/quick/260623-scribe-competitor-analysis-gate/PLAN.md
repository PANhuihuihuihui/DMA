---
quick_id: 260623-scribe-competitor-analysis-gate
status: in_progress
created: 2026-06-23
---

# Plan

Align the first Competitor Analysis screen with the Scribe reference gate.

## Scope

- Make Competitor Analysis open to a sparse account-link requirement screen.
- Show reference copy structure: title, explanatory paragraph, Instagram Business/Creator account row, Facebook connection required badge, and a right-aligned `Link now` button.
- Wire `Link now` to the existing Brand & Social Accounts / Instagram add flow instead of a dead button.
- Keep LocalPilot backend competitor source analysis available in a secondary advanced panel below the gate.
- Update Phase 3 smoke coverage to assert the gate and the advanced source form.

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
- `/bin/zsh -lc "PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens"`
