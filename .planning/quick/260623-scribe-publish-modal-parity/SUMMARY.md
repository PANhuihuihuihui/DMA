---
quick_id: 260623-scribe-publish-modal-parity
status: complete
completed: 2026-06-23
---

# Summary

Reshaped the publish modal toward the Scribe reference layout.

## Changes

- Replaced the old select-heavy publish body with Scribe-style `Ready to post` rows.
- Added Facebook and Facebook Reel row actions backed by the existing publish draft state.
- Added unsupported-media and account-link status cards with connector badges.
- Kept the owner-approval handoff and schedule confirmation path intact.
- Updated browser smoke coverage to use the row-based publish flow.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Remaining Gap

The publish modal now follows the Scribe hierarchy, but exact iconography and platform account behavior still need real connector assets/account state.
