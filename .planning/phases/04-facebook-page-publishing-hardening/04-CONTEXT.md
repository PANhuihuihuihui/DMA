# Phase 4: Facebook Page Publishing Hardening - Context

**Gathered:** 2026-06-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 hardens the *already-working* Facebook Page publishing path for production readiness. The OAuth code exchange, long-lived token exchange, Page fetch, live text + scheduled posting, error/retry classification, and permalink/post-ID capture already exist (`backend/app/facebook_oauth.py`, `backend/app/facebook_publisher.py`). This phase closes the production gaps: durable encrypted token persistence (replacing the in-memory token vault), merchant-driven Page selection (replacing silent auto-pick), permission/capability health before publishing is allowed, single-image + link media publishing with pre-job validation, failure → reconnect/retry/fallback affordances, and Meta app-review evidence.

Requirements in scope: ACCT-01, ACCT-02, ACCT-03, FB-01, FB-02, FB-03, FB-04, FB-05, FB-06, MEDIA-03.

This phase does NOT introduce TikTok work (Phase 5), full account disconnect/ACCT-07 (Phase 5), or the manual fallback package lifecycle STATUS-03/04/05 (Phase 6). Multi-photo and video Facebook publishing are out of scope for this phase.

</domain>

<decisions>
## Implementation Decisions

### Token Persistence
- **D-01:** Replace the in-memory `_PAGE_TOKENS` dict (`backend/app/facebook_token_vault.py`) with a durable encrypted tokens table in the existing SQLite database (`.localpilot-dev/backend.sqlite`). Store ciphertext only.
- **D-02:** Wire stored tokens through the existing `token_boundary` abstraction (`backend/app/token_boundary.py`) — persist the redacted ref + credential fingerprint + rotation metadata that model already defines; never serialize raw tokens to clients.
- **D-03:** Encryption uses a single app key supplied via an environment variable (e.g. `LOCALPILOT_TOKEN_KEY`), with symmetric authenticated encryption (Fernet or AES-GCM).
- **D-04:** Production fails closed — the backend refuses to start (or refuses to persist/use tokens) if the key is missing in production.
- **D-05:** Dev has a graceful, clearly-labeled insecure fallback — when no key is set, behavior degrades to the current ephemeral/in-memory mode so the demo still runs, but it is explicitly marked insecure.
- **D-06:** Persist token expiry / issued-at metadata returned by Graph, and detect invalidation on use — when a publish or health call returns a Facebook auth error (e.g. code 190), mark the connected channel `reconnect_required`. No proactive background refresh this phase.
- **D-07:** Key the token store per (merchant, connected_channel/page) and tie it to existing `connected_channels` records, future-proofing multi-page / multi-merchant even though the demo surfaces one Page.

### Page Selection
- **D-08:** The OAuth callback must stop auto-committing. It fetches the merchant's managed Pages and returns them (no silent `choose_page()` write); the UI presents a "Choose your Page" picker; a second API call commits the chosen Page and stores its token.
- **D-09:** Support connecting multiple managed Pages with exactly one marked as the active publish target (future-proofs multi-location merchants).
- **D-10:** In-scope management actions: select a Page at connect, switch which connected Page is active, and re-run OAuth to refresh tokens. Full disconnect/cleanup (ACCT-07) stays in Phase 5.

### Capability & Permission Health
- **D-11:** ACCT-03 (verify the selected Page has required publishing capability before jobs are allowed) is in scope, but its detailed mechanism is left to the planner. The planner may infer capability/permission states from the existing failure classification in `facebook_publisher.py` (`classify_error_class`) and the `pages_manage_posts` scope already requested in `facebook_oauth.py`. Surface connected / missing-permission / reconnect-required states to the merchant before allowing publish.

### Media Validation
- **D-12:** Facebook media scope for this phase: link posts + single image. Multi-photo and video publishing are deferred.
- **D-13:** Validate media before creating the publish job (Facebook spec checks): allowed file type (jpg/png/gif), file size, and that the media/link is server-accessible. Map failures to clear merchant-facing errors before job creation (MEDIA-05 intent).
- **D-14:** Deliver images to Graph by public URL (e.g. `POST /{page-id}/photos?url=...`), assuming Phase 3 server-side media assets are reachably served. (If assets are not publicly served, the planner may revisit byte upload.)

### the agent's Discretion
- Exact tokens-table schema, column names, and migration approach within the decided SQLite-encrypted direction.
- Exact crypto library choice (Fernet vs AES-GCM) and key-format handling, as long as it is authenticated symmetric encryption keyed from the env var and fails closed in production.
- The concrete mechanism, timing, and UI presentation of capability/permission health (D-11), provided it gates publishing per ACCT-03.
- Exact Graph API media endpoint orchestration for the single-image + link path, and whether to fall back to byte upload if Phase 3 assets are not publicly reachable (D-14).
- Depth and format of the Meta app-review evidence artifact (FB-01), provided it documents the app, required permissions/scopes, test Page, and screencast checklist needed for production readiness.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project And Phase Scope
- `.planning/PROJECT.md` — Project intent, platform priority (Facebook first), security constraints, owner-control constraint.
- `.planning/REQUIREMENTS.md` — Phase 4 requirement IDs (ACCT-01..03, FB-01..06, MEDIA-03) and full v1 traceability.
- `.planning/ROADMAP.md` §"Phase 4: Facebook Page Publishing Hardening" — goal, success criteria, MVP mode, dependencies.
- `.planning/STATE.md` — Current project state.
- `.planning/phases/01-backend-publishing-foundation/01-CONTEXT.md` — Phase 1 decisions still binding: approval-snapshot contract, generic lifecycle states, redacted diagnostics, token-boundary intent, frontend structure boundaries.

### Existing Facebook Implementation (hardening targets)
- `backend/app/facebook_oauth.py` — OAuth flow; `choose_page()` auto-pick to replace (D-08); `connection_status()`; scope list (`pages_show_list`, `pages_read_engagement`, `pages_manage_posts`).
- `backend/app/facebook_publisher.py` — Live publisher; `build_facebook_message` (text-only today), `classify_error_class`/`classify_error_message` (FB-05), retry classification (FB-06), permalink/post-ID capture (FB-04). Extend for single-image + link (FB-03, D-12/D-14).
- `backend/app/facebook_token_vault.py` — In-memory `_PAGE_TOKENS` dict to replace with encrypted SQLite persistence (D-01..D-07).
- `backend/app/token_boundary.py` — Existing redacted token-boundary ref / fingerprint / rotation model to persist through (D-02).
- `backend/app/store.py` — `connected_channels`, media assets, publish jobs/attempts/events, `StoreError`; token table + Page records integrate here.
- `src/api/publishingClient.js` — Frontend API client (`loadFacebookConnection`, `publishFacebookPost`); add Page-list/Page-select/active-Page endpoints.

### Research
- `.planning/research/SUMMARY.md` — Recommended stack, architecture, risk summary.
- `.planning/research/PITFALLS.md` — Security, OAuth, token, retry, and platform risk prevention.
- `.planning/research/ARCHITECTURE.md` — Provider adapter model and component boundaries.

### Codebase Maps
- `.planning/codebase/INTEGRATIONS.md` — Integration boundary map.
- `.planning/codebase/ARCHITECTURE.md` — Backend/frontend architecture and data flow.
- `.planning/codebase/CONCERNS.md` — Security/persistence risks.

### Tests
- `backend/tests/test_facebook_oauth.py`, `backend/tests/test_facebook_publisher.py`, `backend/tests/test_token_boundary.py` — Existing coverage to extend for persistence, Page selection, and media validation.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/token_boundary.py`: already models `storageMode: "external_secret_ref"`, `credentialFingerprint`, and rotation status — the persistence layer should populate/store these rather than inventing a new shape.
- `backend/app/facebook_publisher.py` error classification + retry classification: directly support FB-05/FB-06 and can inform capability-health states (D-11) without new classification logic.
- `store.create_publish_job` / `create_publish_attempt` / `append_publish_event` / `record_publish_outcome`: the publish lifecycle plumbing is in place; media + validation slot in ahead of `publish_approved_snapshot`.
- Phase 3 server-side media assets (`store.py` media-asset functions): source for single-image publishing (D-14).

### Established Patterns
- Manual route matching in `backend/app/server.py` (`match_*` helpers, if/else chain) — new Page-list/select/active endpoints follow the same pattern; errors raise `store.StoreError(status, message)`.
- Frontend calls go through `src/api/publishingClient.js` `requestJson` and are proxied by Vite (`/api/v1` → `:8787`); add Facebook Page endpoints there.
- Approval snapshots are frozen and idempotent (Phase 1); publishing only ever uses the approved version — media/link must be captured into the snapshot contract, not read live at publish time.

### Integration Points
- OAuth callback (`complete_callback`) is the seam for the Page-picker change (D-08): split "fetch pages" from "commit selected page + store token".
- `connected_channels` rows are the anchor for active-Page selection (D-09/D-10) and per-channel token records (D-07).
- `connection_status()` is the natural place to expose connected / missing-permission / reconnect-required health (D-11) to the merchant UI.

</code_context>

<specifics>
## Specific Ideas

- The biggest concrete concern surfaced: Page tokens currently live in a plain in-memory dict and are lost on restart — durable encrypted persistence is the headline outcome of this phase.
- The merchant must actively choose their Page (no silent auto-pick), with a dedicated picker step right after OAuth.
- Keep the local demo runnable without secrets (graceful insecure dev mode), but make production refuse to run without the token encryption key.

</specifics>

<deferred>
## Deferred Ideas

- Multi-photo and video Facebook publishing — deferred beyond this phase (this phase covers link + single image only).
- Proactive token validation/refresh (background `debug_token`/refresh before expiry) — deferred; this phase detects invalidation on use.
- Full account disconnect + stop-jobs cleanup (ACCT-07) — Phase 5.
- Manual fallback package lifecycle (STATUS-03/04/05) — Phase 6; this phase only provides failure → reconnect/retry affordances and a handoff point.
- Per-campaign Page targeting (choosing a different Page per campaign) — deferred; this phase uses one active publish target.
- Envelope encryption / per-record data keys and KMS/Vault integration — deferred; single env key is sufficient for this phase.

</deferred>

---

*Phase: 4-Facebook Page Publishing Hardening*
*Context gathered: 2026-06-23*
