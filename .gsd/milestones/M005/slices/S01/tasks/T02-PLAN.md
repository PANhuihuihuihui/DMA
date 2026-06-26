---
estimated_steps: 24
estimated_files: 4
skills_used: []
---

# T02: FacebookAuthProvider and migrate OAuth sessions from in-memory to DB

Why: The existing facebook_oauth.py uses module-level dicts (_OAUTH_STATES, _CONNECT_SESSIONS) that lose all OAuth state on server restart. This task implements the concrete FacebookAuthProvider and migrates session storage to the oauth_sessions table while preserving the existing API surface for backward compatibility.

Do:
1. Create backend/app/facebook_auth_provider.py implementing AuthProvider:
   - build_auth_url(config): delegates to existing URL construction logic from facebook_oauth.build_login_url
   - exchange_code(conn, code, config): delegates to exchange_code_for_user_token + exchange_for_long_lived_user_token logic
   - refresh(conn, credential_row, config): calls Graph API fb_exchange_token endpoint to refresh a page token (will be fully wired in S02, stub for now that returns the existing token)
   - revoke(conn, credential_row, config): calls Graph API revoke endpoint (stub for now)
   - get_profile(token, config): calls /me endpoint to get user profile
   - list_selectable_accounts(token, config): delegates to existing fetch_pages logic
2. Refactor facebook_oauth.py:
   - build_login_url: replace _OAUTH_STATES[state] = {...} with store.create_oauth_session(conn, 'facebook', 'state', payload, STATE_TTL_SECONDS). This means build_login_url now needs a conn parameter — add it with default None for backward compat during transition. When conn is None, fall back to in-memory dict (safety net).
   - pop_valid_state: replace _OAUTH_STATES.pop(state) with store.get_oauth_session(conn, state, 'state', consume=True). Add conn parameter.
   - complete_callback: replace _CONNECT_SESSIONS[session_id] = {...} with store.create_oauth_session(conn, 'facebook', 'connect', payload, CONNECT_SESSION_TTL_SECONDS).
   - list_pages_for_session: replace _CONNECT_SESSIONS lookup with store.get_oauth_session(conn, session_id, 'connect', consume=False). Add conn parameter.
   - select_page: replace _pop_or_peek_session with store.get_oauth_session(conn, session_id, 'connect', consume=True).
   - _pop_or_peek_session: can be removed once all callers use DB sessions.
   - reset_for_tests: clear both in-memory dicts AND call cleanup for DB sessions.
3. Populate token_expires_at when storing page tokens:
   - In complete_callback, extract expires_in from the long-lived token exchange response
   - Calculate token_expires_at = utc_now() + expires_in seconds
   - Pass expires_at and issued_at to facebook_token_vault.put_page_token
   - Log the expiry timestamp: print(f'Facebook page token stored, expires at {expires_at}')
4. Update server.py if needed to pass conn to any refactored functions that now need it.

Done when: Facebook OAuth callback flow works end-to-end with DB sessions. _OAUTH_STATES and _CONNECT_SESSIONS are no longer the primary storage path. token_expires_at is populated on token storage.

## Inputs

- `backend/app/auth_provider.py`
- `backend/app/facebook_oauth.py`
- `backend/app/store.py`
- `backend/app/facebook_token_vault.py`
- `backend/app/server.py`
- `backend/app/contracts.py`
- `backend/app/token_crypto.py`

## Expected Output

- `backend/app/facebook_auth_provider.py`

## Verification

python -m pytest backend/tests/test_facebook_oauth.py -v
