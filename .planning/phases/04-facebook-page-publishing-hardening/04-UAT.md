---
status: diagnosed
phase: 04-facebook-page-publishing-hardening
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md, 04-04-SUMMARY.md, 04-05-SUMMARY.md, 04-06-SUMMARY.md, 04-07-SUMMARY.md, 04-08-SUMMARY.md]
started: 2026-06-24T14:28:00Z
updated: 2026-06-24T14:35:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Server boots from scratch, health endpoint returns ok.
result: pass

### 2. Token Encryption Round-Trip
expected: All 19 token_crypto/vault tests pass.
result: pass

### 3. Full Backend Test Suite
expected: All 64 backend tests pass.
result: pass

### 4. Facebook Connection Status Endpoint
expected: Returns configured=false, scopes, connectedPages, activePage. No token leak.
result: pass

### 5. Facebook Page Selection Endpoints Exist
expected: select returns 400 (bad session), switch returns 404 (page not connected). Routes registered.
result: pass

### 6. App Review Evidence Document
expected: docs/facebook-app-review-evidence.md exists with scopes, Business Verification, screencast checklist.
result: pass

### 7. Encrypted Token Table Exists
expected: facebook_page_tokens table has ciphertext, credential_fingerprint, is_active columns.
result: pass

### 8. Graph API Version Unified to v25.0
expected: Both facebook_oauth.py and facebook_publisher.py use v25.0.
result: pass

### 9. Media Validation Rejects Invalid Input
expected: validate_facebook_media({}) returns {kind: text}. Function exists and is called pre-job.
result: pass

### 10. Frontend Client Functions Exist
expected: selectFacebookPage, switchFacebookPage, loadFacebookPages exported from publishingClient.js.
result: pass

### 11. CSS Health Badge Classes Exist
expected: fb-health-badge, fb-page-picker, fb-capability-gate classes in styles.css.
result: pass

### 12. Frontend JSX Wiring (Known Deferred)
expected: Page picker modal, health badges, gated publish button, failure-action buttons wired in main.jsx; app builds.
result: issue
reported: "JSX wiring in main.jsx was deferred due to a pre-existing rollup/code-signing build failure (@rollup/rollup-darwin-arm64 on Node v24.14). CSS classes and API client functions are in place but the main.jsx UI integration was not completed. The build issue is not caused by Phase 4."
severity: major

## Summary

total: 12
passed: 11
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Page picker modal, health badges, gated publish button, and failure-action buttons are wired in main.jsx and the app builds"
  status: failed
  reason: "JSX wiring deferred — pre-existing rollup build failure blocks safe verification of changes to the 357K-line main.jsx. CSS + client functions ready; JSX integration needs a working build."
  severity: major
  test: 12
  artifacts:
    - src/main.jsx
    - src/styles.css (fb-health-badge, fb-page-picker, fb-capability-gate already added)
    - src/api/publishingClient.js (loadFacebookPages, selectFacebookPage, switchFacebookPage already added)
  missing:
    - "Connect Facebook button in AppDemo connected-accounts area"
    - "Page picker modal reading from loadFacebookPages(connectSession)"
    - "Health badges rendering page_health states"
    - "Publish button disabled when canPublish=false with gate copy"
    - "Failure-action buttons (Reconnect/Retry/Get manual package)"
