---
estimated_steps: 30
estimated_files: 2
skills_used: []
---

# T01: Added the AuthProvider base, credential refresh helpers, and DB-backed oauth_sessions persistence with logging and backend tests.

Why: The codebase needs a shared abstract interface for platform auth providers (modeled on AiToEarn's AuthProvider pattern) and DB-backed OAuth sessions to replace the in-memory _OAUTH_STATES/_CONNECT_SESSIONS dicts that lose state on server restart.

Do:
1. Create backend/app/auth_provider.py with:
   - AuthProvider ABC (from abc import ABC, abstractmethod) with 6 abstract methods:
     - build_auth_url(config) -> str
     - exchange_code(conn, code, config) -> dict (returns token payload)
     - refresh(conn, credential_row, config) -> dict (returns refreshed token payload)
     - revoke(conn, credential_row, config) -> None
     - get_profile(token, config) -> dict (returns user profile)
     - list_selectable_accounts(token, config) -> list[dict]
   - Standalone function get_valid_credential(conn, page_id, merchant_id, buffer_seconds=60):
     - Reads facebook_page_token_row, decrypts via token_crypto
     - Checks token_expires_at against current time + buffer
     - Returns plaintext token if valid, raises StoreError(401) if expired
     - Logs warning if token expires within 300s
   - Standalone function run_with_credential_refresh(conn, provider, credential_row, config, operation):
     - Calls operation(token) with current token
     - On StoreError with status 401, calls provider.refresh() to get new token
     - Retries operation once with refreshed token
     - If retry also fails, raises the second error
2. Add oauth_sessions table to store.py initialize_database:
   - Columns: id (text PK), provider (text), session_type (text: 'state' or 'connect'), payload_json (text), created_at (text), expires_at (text)
   - Index on (provider, session_type, id)
3. Add store.py helper functions:
   - create_oauth_session(conn, provider, session_type, payload, ttl_seconds) -> session_id
   - get_oauth_session(conn, session_id, session_type, consume=False) -> dict or raises StoreError(400)
   - cleanup_expired_oauth_sessions(conn) -> int (count removed)
   Session fetch must check expires_at against current time and raise StoreError(400) if expired.
   When consume=True, delete the row after fetching.

Done when: auth_provider.py module imports cleanly, AuthProvider cannot be instantiated directly, oauth_sessions table is created by initialize_database, store helper functions exist.

## Inputs

- `backend/app/store.py`
- `backend/app/facebook_oauth.py`
- `backend/app/token_crypto.py`
- `backend/app/facebook_token_vault.py`
- `backend/app/contracts.py`

## Expected Output

- `backend/app/auth_provider.py`

## Verification

python -c "from backend.app.auth_provider import AuthProvider, get_valid_credential, run_with_credential_refresh"
