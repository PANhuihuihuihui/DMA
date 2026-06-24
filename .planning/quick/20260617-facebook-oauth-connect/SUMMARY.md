---
quick_task: facebook-oauth-connect
status: complete
completed: 2026-06-17
phase: 03-facebook-customer-demo-loop
---

# Summary

Replaced the customer-facing Graph API Explorer token paste path with a clickable Facebook OAuth connect flow.

## Completed

- Added Facebook OAuth start/callback support using server-side `code` flow.
- Requested `pages_show_list`, `pages_read_engagement`, and `pages_manage_posts`.
- Read `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, redirect URI, and return URL from backend environment.
- Added state validation for the OAuth callback.
- Added an in-memory local demo Page token vault so Page tokens do not enter browser localStorage, committed files, API responses, or SQLite publish diagnostics.
- Updated live Facebook publishing to use the connected Page token from the backend vault.
- Updated UI from token paste to `Connect Facebook`, Page selection, and `Publish live`.
- Added tests for OAuth URL generation, callback connection, invalid state rejection, token redaction, and publish-with-connected-Page-token.

## Verification

- `python3 -m unittest backend.tests.test_facebook_oauth -v`
- `python3 -m unittest backend.tests.test_facebook_publisher -v`
- `npm run test:storage-boundary`
- `npm run build`
- `npm test`

## Runtime Setup

Set these before `npm run dev:full`:

```bash
export FACEBOOK_APP_ID="..."
export FACEBOOK_APP_SECRET="..."
export FACEBOOK_REDIRECT_URI="http://127.0.0.1:8787/api/v1/facebook/oauth/callback"
export FACEBOOK_OAUTH_RETURN_URL="http://127.0.0.1:5173/app?facebookConnected=1"
export FACEBOOK_DEMO_PAGE_ID="1243605852158721"
```

The same redirect URI must be allowlisted in Meta App Dashboard under Facebook Login settings.
