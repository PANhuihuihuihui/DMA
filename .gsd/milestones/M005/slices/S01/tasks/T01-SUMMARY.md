---
id: T01
parent: S01
milestone: M005
key_files:
  - backend/app/auth_provider.py
  - backend/app/store.py
  - backend/tests/test_auth_provider.py
key_decisions:
  - Persist transient OAuth state in the new `oauth_sessions` table with TTL enforcement and explicit create/consume/cleanup logging instead of relying on process-local dicts.
  - Keep refresh retry behavior narrow: retry exactly once on `StoreError(401)` and require refresh payloads to expose a usable `access_token` or `token` field.
duration: 
verification_result: passed
completed_at: 2026-06-26T17:21:09.459Z
blocker_discovered: false
---

# T01: Added the AuthProvider base, credential refresh helpers, and DB-backed oauth_sessions persistence with logging and backend tests.

**Added the AuthProvider base, credential refresh helpers, and DB-backed oauth_sessions persistence with logging and backend tests.**

## What Happened

Implemented `backend/app/auth_provider.py` with the six-method `AuthProvider` ABC plus `get_valid_credential()` and `run_with_credential_refresh()` so downstream platform auth flows can share expiry checks, decryption, and one-time refresh retry behavior. Extended `backend/app/store.py` with an `oauth_sessions` table, migration-safe creation, TTL-backed create/get/consume/cleanup helpers, and structured info logs for session creation, consumption, and cleanup counts. Added `backend/tests/test_auth_provider.py` to cover the new abstraction, expiry handling, refresh retry, session consumption, expired-session rejection, and cleanup logging.

## Failure Modes
- Missing Facebook credential rows now fail fast with `StoreError(404)` from `get_valid_credential()`.
- Credentials that are inside the caller buffer window raise `StoreError(401)`; near-expiry-but-still-valid credentials emit a warning log before returning the plaintext token.
- Token decryption failures from `token_crypto.decrypt_secret()` are intentionally bubbled unchanged so callers see the underlying auth-secret problem instead of a silent fallback.
- `run_with_credential_refresh()` only retries on `StoreError(401)`. Any non-401 store error bubbles immediately. A refresh payload missing `access_token`/`token` now raises `StoreError(502)`, and a second operation failure is re-raised unchanged.
- `get_oauth_session()` returns `StoreError(400)` for missing or expired rows. Expired rows are deleted on access, and `cleanup_expired_oauth_sessions()` removes any remaining expired rows and logs the removed-row count.

## Load Profile
- The first 10x pressure point for this task is short-lived OAuth callback/session lookup churn in SQLite. Protection added here is a dedicated `(provider, session_type, id)` index plus TTL cleanup helpers so reads stay narrow and expired rows do not accumulate indefinitely.
- The runtime surface is still low-volume and handshake-oriented, so this task did not add caching or rate limiting; the intended protection is bounded row lifetime plus indexed point lookups.

## Negative Tests
- `backend/tests/test_auth_provider.py` covers: abstract-class instantiation rejection, valid credential return, near-expiry warning logging, within-buffer `401` expiry rejection, refresh-once success, second-error re-raise after retry, table creation, session consume semantics, missing-session `400`, expired-session `400`, and cleanup-count logging.

## Verification

Verified the new module imports cleanly, the focused auth/session test module passes, and existing Facebook OAuth/token-store tests still pass with the new schema/helpers present. The focused tests also exercised the slice observability contract by asserting the near-expiry warning log from `backend.app.auth_provider` and the create/consume/cleanup info logs from `backend.app.store`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python import smoke: from backend.app.auth_provider import AuthProvider, get_valid_credential, run_with_credential_refresh` | 0 | ✅ pass | 105ms |
| 2 | `python unittest: backend.tests.test_auth_provider.AuthProviderTest` | 0 | ✅ pass | 326ms |
| 3 | `python unittest: backend.tests.test_facebook_oauth + backend.tests.test_facebook_token_store` | 0 | ✅ pass | 407ms |

## Deviations

None.

## Known Issues

`backend/app/facebook_oauth.py` still uses the in-memory `_OAUTH_STATES` and `_CONNECT_SESSIONS` maps in this task; this unit only introduced the DB-backed session surface and auth abstraction that later tasks will wire into the live callback flow.

## Files Created/Modified

- `backend/app/auth_provider.py`
- `backend/app/store.py`
- `backend/tests/test_auth_provider.py`
