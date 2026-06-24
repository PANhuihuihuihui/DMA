# Scribe Social Platforms Parity Summary

## Changes

- Rebuilt the Brand & Social Accounts Social Platforms tab as a Scribe-style account table.
- Added provider rows for Instagram, Facebook, Linkedin, Google Business Profile, TikTok, Pinterest, Twitter, and Youtube.
- Added row actions for Watch Videos, FAQ, Add, plus the expanded Facebook connected-page card with Unlink.
- Hid the legacy Facebook Page picker from the visible reference workspace while preserving the demo-only OAuth/page code path.
- Updated the Phase 3 screen smoke to assert the new Scribe-style social account surface.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`

## Runtime Note

- Backend health passed on `http://127.0.0.1:8787/api/v1/health`.
- Vite is listening on `http://127.0.0.1:4173/` according to `lsof`; sandboxed curl to that port is blocked by local network permissions, not by the app process.
