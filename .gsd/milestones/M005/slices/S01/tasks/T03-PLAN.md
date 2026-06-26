---
estimated_steps: 28
estimated_files: 1
skills_used: []
---

# T03: Contract tests for AuthProvider, DB sessions, and credential refresh helpers

Why: The AuthProvider abstraction, DB session lifecycle, and credential refresh helpers need thorough test coverage to ensure the contract is enforced and downstream slices (S02-S05) can rely on these primitives.

Do:
1. Create backend/tests/test_auth_provider.py with unittest.TestCase classes:

   TestAuthProviderABC:
   - test_cannot_instantiate_abc: verify AuthProvider() raises TypeError
   - test_facebook_provider_is_auth_provider: verify isinstance(FacebookAuthProvider(), AuthProvider)

   TestOAuthSessionDB:
   - setUp: create temp DB via store.ensure_database, get conn
   - test_create_and_fetch_session: create_oauth_session, then get_oauth_session returns matching payload
   - test_consume_session_removes_row: get_oauth_session with consume=True, second fetch raises StoreError(400)
   - test_expired_session_raises: create session with ttl_seconds=0, sleep briefly, fetch raises StoreError(400)
   - test_invalid_session_id_raises: fetch nonexistent ID raises StoreError(400)
   - test_cleanup_removes_expired: create expired + valid sessions, cleanup returns count of removed expired only

   TestGetValidCredential:
   - setUp: create temp DB, seed merchant/channel, store a page token with known expiry
   - test_valid_token_returns_plaintext: store token with expiry 1 hour from now, get_valid_credential returns it
   - test_expired_token_raises_401: store token with expiry in the past, get_valid_credential raises StoreError(401)
   - test_near_expiry_within_buffer_raises: store token expiring in 30s (within 60s buffer), raises StoreError(401)
   - test_no_expiry_set_returns_token: store token with expires_at=None, returns token (assumes valid)

   TestRunWithCredentialRefresh:
   - test_success_without_refresh: operation succeeds first try, refresh not called
   - test_retries_on_auth_failure: operation raises StoreError(401), refresh called, operation retried with new token
   - test_raises_on_second_failure: operation fails twice, second error propagated
   - test_non_auth_error_not_retried: operation raises StoreError(500), not retried, error propagated immediately

2. Ensure all tests use the standard pattern: tempfile DB, store.ensure_database, setUp/tearDown cleanup.
3. Use unittest.mock.patch for Graph API calls and token_crypto where needed.
4. Set LOCALPILOT_TOKEN_KEY env var in tests that need encryption.

Done when: All tests in test_auth_provider.py pass. Combined with T02 verification that existing facebook_oauth tests still pass, this confirms full backward compatibility.

## Inputs

- `backend/app/auth_provider.py`
- `backend/app/facebook_auth_provider.py`
- `backend/app/store.py`
- `backend/app/facebook_token_vault.py`
- `backend/app/token_crypto.py`

## Expected Output

- `backend/tests/test_auth_provider.py`

## Verification

python -m pytest backend/tests/test_auth_provider.py -v
