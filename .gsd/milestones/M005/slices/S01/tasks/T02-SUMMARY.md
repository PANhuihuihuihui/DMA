---
id: T02
parent: S01
milestone: M005
key_files:
  - backend/app/facebook_oauth.py
  - backend/app/facebook_auth_provider.py
  - backend/app/server.py
  - backend/tests/test_facebook_oauth.py
key_decisions:
  - Use `oauth_sessions.id` itself as the public Facebook OAuth `state` and `connectSession` token so start/callback/list/select can share one persisted lookup surface.
  - Keep `conn=None` fallback behavior in the Facebook OAuth helpers during the migration, but require real server routes to pass DB connections so the production flow no longer depends on process-local state.
  - Store `issued_at` and `token_expires_at` alongside persisted Facebook page tokens and log the expiry timestamp at selection time so downstream refresh-before-publish logic has concrete timing data.
duration: 
verification_result: passed
completed_at: 2026-06-26T22:54:35.355Z
blocker_discovered: false
---

# T02: Moved Facebook OAuth state/connect sessions into `oauth_sessions`, added `FacebookAuthProvider`, and persisted page-token expiry metadata during page selection.

**Moved Facebook OAuth state/connect sessions into `oauth_sessions`, added `FacebookAuthProvider`, and persisted page-token expiry metadata during page selection.**

## What Happened

Replaced Facebook OAuth’s process-local `_OAUTH_STATES` and `_CONNECT_SESSIONS` as the primary path with DB-backed `oauth_sessions` rows, while keeping `conn=None` in-memory fallback behavior as a transition safety net. `backend/app/facebook_oauth.py` now creates, consumes, and opportunistically cleans up persisted `state` and `connect` sessions, commits cross-request session writes, and carries `issuedAt`/`expiresAt` from the long-lived user-token exchange into the page-selection step. `select_page()` now persists `expires_at` and `issued_at` through `facebook_token_vault.put_page_token(...)` and logs the stored expiry timestamp for debugging. Added `backend/app/facebook_auth_provider.py` as the concrete `AuthProvider` implementation for Facebook, delegating build/exchange/profile/list behavior to the existing OAuth helpers and returning the current token for the planned S02 refresh/revoke stubs. Updated `backend/app/server.py` so `/api/v1/facebook/oauth/start` and `/api/v1/facebook/pages` pass a DB connection into the migrated helpers, ensuring the real request flow uses persisted sessions instead of silently falling back to process-local state. Expanded `backend/tests/test_facebook_oauth.py` to verify DB-backed state/connect sessions, connect-session consumption, expiry persistence, reset cleanup, and the new provider delegation surface.

## Failure Modes
- **Facebook Graph API**: `graph_get()` still wraps HTTP failures into `store.StoreError(status, message)`, so callback/profile/page-list failures bubble with the upstream status and message instead of producing partial state.
- **Missing or malformed OAuth payloads**: `complete_callback()` rejects missing `code`, missing user access tokens, and empty manageable-page lists; `select_page()` rejects missing page tokens and invalid page IDs from the connect session.
- **Expired or missing persisted sessions**: `store.get_oauth_session(..., consume=...)` enforces TTL, deletes expired rows on access, and the migrated OAuth helpers now call `cleanup_expired_oauth_sessions()` on the DB path so expired session cleanup is logged with a removed-row count.
- **Token-encryption configuration**: tests now exercise the encrypted DB path with a valid Fernet key so page-token expiry metadata is verified on the real persistence surface; the transitional in-memory fallback remains available only when no connection or no key is supplied.

## Load Profile
- The first 10x saturation point is the SQLite-backed transient-session table plus the one Graph `/me/accounts` fetch per completed callback, not Python memory growth, because OAuth state/connect sessions are now TTL-bounded rows instead of unbounded module-level dicts.
- Protection comes from `oauth_sessions` TTL enforcement plus opportunistic `cleanup_expired_oauth_sessions()` calls on start/callback/list/select, which prevents abandoned OAuth sessions from accumulating across restarts.
- The page-fetch path remains bounded to `limit=100`, so this task did not introduce any new unbounded per-request fan-out.

## Negative Tests
- `test_login_url_uses_code_flow_scopes_redirect_uri_and_db_state` verifies DB-backed state creation and the expected OAuth query contract.
- `test_callback_returns_db_connect_session_and_strips_page_tokens` verifies state consumption, persisted connect-session creation, and response sanitization so page access tokens do not leak back to the client.
- `test_select_page_persists_expiry_metadata_and_consumes_connect_session` verifies expiry metadata persistence, expiry logging, token retrieval on the encrypted DB path, and one-time connect-session consumption.
- `test_reset_for_tests_clears_db_oauth_sessions` verifies DB cleanup instead of leaving persisted OAuth rows behind.
- `test_facebook_auth_provider_delegates_existing_oauth_helpers` verifies the new provider abstraction delegates to the existing Facebook OAuth helper surface rather than forking separate logic.

## Verification

Ran `python3 -m pytest backend/tests/test_facebook_oauth.py -v` to verify the DB-backed OAuth flow, connect-session consumption, expiry persistence, reset cleanup, and provider delegation tests all pass. Ran `python3 -m py_compile backend/app/facebook_oauth.py backend/app/facebook_auth_provider.py backend/app/server.py` to confirm the edited runtime modules parse cleanly after the signature and import changes.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_facebook_oauth.py -v` | 0 | ✅ pass | 353ms |
| 2 | `python3 -m py_compile backend/app/facebook_oauth.py backend/app/facebook_auth_provider.py backend/app/server.py` | 0 | ✅ pass | 51ms |

## Deviations

Adjusted `connection_status()` to fall back to the first connected page when the transitional non-encrypted path does not mark an explicit `isActive` page, so the dev/fallback path stays behaviorally aligned with the DB-backed flow.

## Known Issues

`FacebookAuthProvider.refresh()` and `revoke()` are still intentionally narrow stubs that return the current token or derived endpoint metadata; full Graph refresh/revoke execution is deferred to S02 per the task plan.

## Files Created/Modified

- `backend/app/facebook_oauth.py`
- `backend/app/facebook_auth_provider.py`
- `backend/app/server.py`
- `backend/tests/test_facebook_oauth.py`
