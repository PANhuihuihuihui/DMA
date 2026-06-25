# Phase 7: Google Login And Auth - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 replaces the prototype fake login with real Google sign-in. A user signs in with Google; the backend verifies the Google ID token, resolves or creates the user + merchant, and issues a LocalPilot session delivered as a secure cookie. It is the auth foundation for milestone v2.0 (onboarding, generation).

In scope: GAUTH-01, GAUTH-02.

Out of scope this phase: OAuth authorization-code flow and Google API scopes/refresh tokens (deferred until a real Google API integration is needed), team/multi-user-per-merchant roles, and website-crawl onboarding (Phase 8).
</domain>

<decisions>
## Implementation Decisions

### Google Sign-In Flow
- **D-01:** Use Google Identity Services (GIS) **ID-token / One Tap login only** for v1. The frontend GIS button/One Tap returns a credential (ID token) which the backend verifies. No OAuth authorization-code flow, no client secret, no refresh token, no Google API scopes this phase. (GAUTH-01)
- **D-02:** Verify the ID token server-side with `google-auth` `verify_oauth2_token` against `GOOGLE_CLIENT_ID`: validate signature, `aud` == our client ID, `iss` ∈ {`accounts.google.com`, `https://accounts.google.com`}, and `exp`. Reject anything else. Cache Google certs where practical. Never trust client-sent user IDs.

### Identity & Tenancy
- **D-03:** First Google sign-in is **self-serve**: create a new merchant + user and store the Google `sub` as the stable identity key. If the verified Google email matches an existing user, link the `sub` to that user instead of creating a duplicate (one user = one merchant, per Phase 5 D-19).
- **D-04:** Store the Google `sub` (and verified email) on the user. `sub` is the durable lookup key; email is secondary/link-only and may change over time.

### Session Issuance & Transport
- **D-05:** On successful verification, issue a LocalPilot session via the existing `sessions` table (`sessions.create_session`) and deliver it as an **httpOnly + Secure + SameSite cookie** set by the backend. The session token is never exposed to JavaScript or stored in localStorage.
- **D-06:** Extend request handling so the server resolves the session from the **Cookie header** in addition to the existing `X-LocalPilot-Session` header / `session` query param (kept for backward compatibility and tests). Logout clears the cookie and expires the session (`sessions.expire_session`).

### Dev/Demo & Fake Login
- **D-07:** Keep a **dev-only login path behind an env flag** (e.g. `LOCALPILOT_DEV_LOGIN`) that issues a demo session without Google; the real Google flow activates when `GOOGLE_CLIENT_ID` is configured. The token verifier is mocked in tests.
- **D-08:** Replace the existing fake login in `src/main.jsx` with the Google sign-in entry point, keeping the dev bypass behind the flag for local/demo use.

### the agent's Discretion
- Exact backend endpoint shapes (e.g. `POST /api/v1/auth/google` accepting the credential, `POST /api/v1/auth/logout`, optional `GET /api/v1/auth/session`).
- Cookie name and attributes (Secure auto-relaxed for localhost http), SameSite value (Lax vs Strict), and session TTL.
- Whether to add `google_sub` / `email_verified` columns to the existing `users` table (likely simplest under one-user-one-merchant) vs a separate identities table — use the established `migrate_database` column pattern.
- GIS frontend specifics (One Tap vs rendered button), and how the public `GOOGLE_CLIENT_ID` is injected into the frontend (env/build).
- Google certificate caching strategy for `google-auth`.
</decisions>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md` — security constraints: OAuth secrets/tokens never in browser/localStorage or committed files; owner-controlled, official-API posture.
- `.planning/REQUIREMENTS.md` — GAUTH-01, GAUTH-02.
- `.planning/ROADMAP.md` §"Phase 7: Google Login And Auth" — goal and success criteria.
- `.planning/research/SUMMARY.md` §3 (Google login) — `verify_oauth2_token`, `sub` as key, aud/iss/exp checks; links: [Google backend auth](https://developers.google.com/identity/sign-in/web/backend-auth), [best practices](https://developers.google.com/identity/siwg/best-practices).
- `backend/app/sessions.py` — `create_session`, `resolve_session`, `expire_session`, `SessionError`.
- `backend/app/store.py` — `users` / `merchants` tables, `DEMO_USER_ID` / `DEMO_MERCHANT_ID`, `seed_demo_data`, `ensure_demo_session`, `migrate_database` (column-add pattern).
- `backend/app/server.py` — `JsonHandler.route_request`, `resolve_merchant_id`, `send_json`/`send_redirect`/`read_json`, manual route matching.
- `backend/app/contracts.py` — `serialize_session`, `utc_now`, `new_id`, `redact`.
- `src/main.jsx` — existing fake login modal to replace.
- `src/api/publishingClient.js` — client API patterns; add auth calls.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sessions.py` already implements the full session lifecycle (create/resolve/expire) against the `sessions` table — the auth endpoint issues a session through it.
- `contracts.serialize_session` already redacts the session shape for safe serialization.
- `JsonHandler.resolve_merchant_id` already resolves a session token (header/query) to a merchant — extend it to also read the Cookie header.
- `migrate_database` provides the additive column pattern for new `users` columns (`google_sub`, `email_verified`).

### Established Patterns
- Routes are registered manually in `route_request` with small `match_*` helpers; errors via `store.StoreError(status, message)`.
- Secret boundary + redaction conventions (`redact`, `safe_diagnostics`) must hold — no tokens/secrets in responses.
- Demo seeding (`ensure_demo_session`, `DEMO_USER_ID`) supports the dev-login path.

### Integration Points
- **New:** the server must set `Set-Cookie` on the login response and read the `Cookie` header on subsequent requests (`http.server` `BaseHTTPRequestHandler`). This is the main new request-handling capability.
- **Frontend:** replace the fake login in `src/main.jsx` with a GIS sign-in entry; add `googleLogin`/`logout`/`session` calls to `src/api/publishingClient.js`.
</code_context>

<specifics>
## Specific Ideas

- httpOnly + Secure + SameSite cookie is the security-correct transport; the session token must never live in JS/localStorage (PROJECT.md).
- ID-token-only login minimizes the secret surface — no Google refresh token or client secret is stored anywhere this phase.
- `sub` is the durable identity key; email is for first-login account linking only and may change.
- The dev bypass must be clearly gated by an env flag so it can never be enabled in production by default.
</specifics>

<deferred>
## Deferred Ideas

- OAuth 2.0 authorization-code flow + Google API scopes / refresh tokens (e.g. Drive, Google Business Profile) — when a real Google API integration is needed.
- Multi-user-per-merchant and team roles/permissions (Agency backlog: AGENCY-01/02).
- Advanced account-protection (Cross-Account Protection / RISC, App Check).
- Other social logins (Facebook/Apple) — not requested.
</deferred>

---

*Phase: 7-Google Login And Auth*
*Context gathered: 2026-06-24*
