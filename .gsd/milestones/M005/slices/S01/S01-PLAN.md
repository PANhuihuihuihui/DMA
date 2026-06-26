# S01: AuthProvider Abstraction and Session Persistence

**Goal:** Facebook OAuth works end-to-end using DB-backed sessions and a new AuthProvider base class. Token expiry is tracked and logged. In-memory _OAUTH_STATES and _CONNECT_SESSIONS dicts are replaced by oauth_sessions table with TTL enforcement. get_valid_credential and run_with_credential_refresh helpers enable downstream slices to add refresh-before-publish.
**Demo:** Facebook OAuth still works end-to-end but now uses DB sessions and the new base class. Token expiry is tracked and logged.

## Must-Haves

- 1. AuthProvider ABC exists with abstract methods: build_auth_url, exchange_code, refresh, revoke, get_profile, list_selectable_accounts
- 2. oauth_sessions table persists state and connect sessions with automatic TTL expiry
- 3. FacebookAuthProvider implements all AuthProvider abstract methods
- 4. get_valid_credential checks token_expires_at with 60s buffer, returns plaintext token when valid, raises when expired
- 5. run_with_credential_refresh wraps an operation, catches authentication failures, calls provider.refresh, retries once
- 6. All existing facebook_oauth.py tests pass without modification (backward-compatible refactor)
- 7. In-memory _OAUTH_STATES and _CONNECT_SESSIONS dicts are no longer used for session persistence
- 8. Token expiry timestamp is populated when storing page tokens from Graph API response

## Proof Level

- This slice proves: contract + integration — tests exercise ABC contract, DB session lifecycle, credential expiry logic, and full OAuth callback flow against SQLite + mocks. No live Graph API calls needed.

## Integration Closure

Upstream surfaces consumed: backend/app/store.py (DB schema, facebook_page_tokens CRUD), backend/app/facebook_token_vault.py (token storage), backend/app/token_crypto.py (encryption), backend/app/contracts.py (utc_now, new_id).
New wiring introduced: backend/app/auth_provider.py (ABC + helpers), backend/app/facebook_auth_provider.py (concrete implementation), oauth_sessions table in store.py schema.
What remains before milestone is truly usable end-to-end: S02 wires refresh-before-publish into actual Facebook publish flow. S03-S05 add Instagram/TikTok/Xiaohongshu providers. S06 adds E2E test suite.

## Verification

- Token expiry warnings logged when get_valid_credential finds a token within 300s of expiry. Session creation and consumption events logged for debugging. Expired session cleanup logged with count of removed rows.

## Tasks

- [x] **T01: Added the AuthProvider base, credential refresh helpers, and DB-backed oauth_sessions persistence with logging and backend tests.** `est:1h`
  Why: The codebase needs a shared abstract interface for platform auth providers (modeled on AiToEarn's AuthProvider pattern) and DB-backed OAuth sessions to replace the in-memory _OAUTH_STATES/_CONNECT_SESSIONS dicts that lose state on server restart.
  - Files: `backend/app/auth_provider.py`, `backend/app/store.py`
  - Verify: python -c "from backend.app.auth_provider import AuthProvider, get_valid_credential, run_with_credential_refresh"

- [x] **T02: Moved Facebook OAuth state/connect sessions into `oauth_sessions`, added `FacebookAuthProvider`, and persisted page-token expiry metadata during page selection.** `est:1h30m`
  Why: The existing facebook_oauth.py uses module-level dicts (_OAUTH_STATES, _CONNECT_SESSIONS) that lose all OAuth state on server restart. This task implements the concrete FacebookAuthProvider and migrates session storage to the oauth_sessions table while preserving the existing API surface for backward compatibility.
  - Files: `backend/app/facebook_auth_provider.py`, `backend/app/facebook_oauth.py`, `backend/app/server.py`, `backend/app/facebook_token_vault.py`
  - Verify: python -m pytest backend/tests/test_facebook_oauth.py -v

- [ ] **T03: Contract tests for AuthProvider, DB sessions, and credential refresh helpers** `est:1h`
  Why: The AuthProvider abstraction, DB session lifecycle, and credential refresh helpers need thorough test coverage to ensure the contract is enforced and downstream slices (S02-S05) can rely on these primitives.
  - Files: `backend/tests/test_auth_provider.py`
  - Verify: python -m pytest backend/tests/test_auth_provider.py -v

## Files Likely Touched

- backend/app/auth_provider.py
- backend/app/store.py
- backend/app/facebook_auth_provider.py
- backend/app/facebook_oauth.py
- backend/app/server.py
- backend/app/facebook_token_vault.py
- backend/tests/test_auth_provider.py
