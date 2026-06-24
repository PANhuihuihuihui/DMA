---
quick_id: 260623-scribe-competitor-analysis-gate
status: complete
completed: 2026-06-23
---

# Summary

## What Changed

- Reworked the first Competitor Analysis state into the Scribe-style account-link gate.
- Added the title, explanatory copy, Instagram Business/Creator requirement row, Facebook connection required badge, and right-aligned `Link now` action.
- Wired `Link now` into the existing Social Platforms Instagram connection dialog.
- Preserved LocalPilot's backend competitor-source workflow in a secondary advanced panel below the gate.
- Updated Phase 3 screen smoke coverage to assert the gate and the Link-now dialog.

## Reference Evidence

- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-46.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-47.jpg`

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
- `/bin/zsh -lc "PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens"`
