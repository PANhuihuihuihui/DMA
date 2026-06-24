---
quick_id: 260623-scribe-publish-modal-parity
status: in_progress
created: 2026-06-23
---

# Plan

Align the publish modal with the Scribe reference after opening a generated library asset.

## Scope

- Replace the form-like publish modal body with Scribe-style ready-to-post rows.
- Show unsupported-media and account-not-linked cards at the bottom.
- Preserve owner-approval/compatibility gating and the existing schedule handoff.
- Update smoke coverage to use the row-based modal instead of select controls.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
