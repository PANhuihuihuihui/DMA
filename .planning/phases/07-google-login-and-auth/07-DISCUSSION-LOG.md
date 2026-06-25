# Phase 7 Discussion Log — Google Login And Auth

**Date:** 2026-06-24
**Mode:** discuss (default)

Human-reference audit log. Canonical decisions live in `07-CONTEXT.md`.

## Area 1 — Sign-in flow
- **Options:** ID-token/One Tap only (recommended) / full OAuth code flow / both.
- **Decision:** ID-token / One Tap login only for v1; no client secret, no Google API scopes. → D-01, D-02.

## Area 2 — Identity & tenancy (first sign-in)
- **Options:** self-serve create + email-link (recommended) / always create new / pre-provisioned only.
- **Decision:** Self-serve create merchant+user; link Google `sub` to an existing user when the verified email matches. → D-03, D-04.

## Area 3 — Session transport
- **Options:** httpOnly+Secure+SameSite cookie (recommended) / keep header token.
- **Decision:** httpOnly + Secure + SameSite cookie; server also reads Cookie header (keep header/query for compat). → D-05, D-06.

## Area 4 — Dev/demo fallback
- **Options:** dev-only login behind env flag (recommended) / mock verifier only / require real creds.
- **Decision:** Dev-only login path behind `LOCALPILOT_DEV_LOGIN`; real Google when `GOOGLE_CLIENT_ID` set; verifier mocked in tests. → D-07.

## Area 5 — Existing fake login
- **Options:** replace + keep dev bypass behind flag (recommended) / remove fully / keep both.
- **Decision:** Replace fake login with Google sign-in; keep dev bypass behind the flag. → D-08.

## Deferred Ideas
- OAuth code flow + Google API scopes/refresh tokens; multi-user/team roles; RISC/App Check; other social logins.

## the agent's Discretion (captured in CONTEXT.md)
- Endpoint shapes; cookie name/attributes/TTL; `users` columns vs identities table; GIS frontend specifics + client-ID injection; cert caching.
