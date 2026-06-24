---
quick_task: facebook-demo-publish-loop
status: complete
completed: 2026-06-17
phase: 03-facebook-customer-demo-loop
---

# Summary

Implemented the first backend/UI wiring for the Facebook customer demo publish loop.

## Completed

- Added `backend/app/facebook_publisher.py` for official Graph API Page publishing.
- Added `POST /api/v1/approvals/:approvalId/publish-facebook`.
- Preserved exact-version approval, publish jobs, attempts, events, outcomes, idempotency, and redacted diagnostics.
- Added frontend API support through `publishFacebookPost`.
- Added Facebook-only live publish controls for approved drafts in the app UI.
- Updated seeded backend demo records to Aurora Heating & Cooling with the verified Facebook Page ID.
- Kept the Graph API user token request-scoped: it is accepted by the backend request, exchanged for a Page token, used for the provider call, and not persisted or returned.
- Added backend tests for successful live publish, missing `pages_manage_posts`, and non-Facebook approval rejection.

## Verification

- `python3 -m unittest backend.tests.test_facebook_publisher -v`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`
- `curl http://127.0.0.1:8787/api/v1/health`
- `curl -I http://127.0.0.1:5173/`

## Notes

- Browser visual verification was attempted, but the in-app browser was unavailable in this session.
- Local dev servers are running through `npm run dev:full` at `http://127.0.0.1:5173/` and `http://127.0.0.1:8787/`.
