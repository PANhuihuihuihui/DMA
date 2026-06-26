# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

## Validated

### R002 — Untitled
- Status: validated
- Validation: validated
- Notes: Verified by test_facebook_oauth.py (4 tests): full OAuth→connectSession→select_page flow with token non-leakage. S01 wired frontend connectSession picker; S02 provided contract-level verification.

### R003 — Untitled
- Status: validated
- Validation: validated
- Notes: Verified by test_facebook_token_store.py (19 tests): Fernet encrypt/decrypt round-trip, ciphertext opacity, production fails-closed, SQLite vault storage. Implementation in token_crypto.py + facebook_token_vault.py.

### R004 — Untitled
- Status: validated
- Validation: validated
- Notes: Verified by test_media_validation.py (12 tests): single-image enforcement, multi-image rejection, private host blocking, extension/size/content-type validation. Implementation in facebook_publisher.py validate_facebook_media().

### R005 — Untitled
- Status: validated
- Validation: validated
- Notes: Verified by test_error_classification.py (16 tests): all 7 error classes mapped correctly (authentication, missing_permission, page_capability, validation, rate_limit, platform_transient, unknown) with retryable vs manual_fallback routing. Implementation in facebook_publisher.py classify_error_class().

### R006 — Untitled
- Status: validated
- Validation: validated
- Notes: Verified by test_evidence_export.py (4 tests): redacted evidence bundle with required fields (job, appReview, exportedAt, route), admin endpoint with role-based access control. Implementation in store.py build_publish_job_evidence() + server.py admin endpoint.

## Deferred

## Out of Scope

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R002 |  | validated | none | none | validated |
| R003 |  | validated | none | none | validated |
| R004 |  | validated | none | none | validated |
| R005 |  | validated | none | none | validated |
| R006 |  | validated | none | none | validated |

## Coverage Summary

- Active requirements: 0
- Mapped to slices: 0
- Validated: 5 (R002, R003, R004, R005, R006)
- Unmapped active requirements: 0
