# Phase 4: Facebook Page Publishing Hardening - Research

**Researched:** 2026-06-23
**Phase goal:** Production-ready Facebook Page publishing — secure token persistence, Page selection, permission/capability health, media validation, retry/fallback, app-review evidence.
**Requirement IDs:** ACCT-01, ACCT-02, ACCT-03, FB-01, FB-02, FB-03, FB-04, FB-05, FB-06, MEDIA-03

> Note: this artifact was authored by the orchestrator after the researcher subagent run was interrupted. External Graph API facts were verified against Meta developer docs (v25.0, 2026); environment facts were verified directly in the repo.

## TL;DR for the Planner

1. **Token encryption needs a new Python dependency.** The backend today is pure stdlib (`http.server`, `sqlite3`, `urllib`, `hashlib`, `secrets`) with **no `requirements.txt`**. `cryptography` is NOT installed and Python's stdlib has **no AEAD cipher** (no AES/ChaCha). Implementing D-03 (Fernet/AES-GCM) requires adding `cryptography` (Fernet) and introducing a `requirements.txt`. This is the first third-party Python dep — call it out explicitly.
2. **Most of the live path already works.** `facebook_oauth.py` (OAuth + Page fetch) and `facebook_publisher.py` (text + scheduled `/feed`, error classification, permalink capture) are implemented. Phase 4 is hardening + filling gaps, not greenfield.
3. **Version drift bug:** `facebook_publisher.py` uses `GRAPH_API_BASE = v20.0` while `facebook_oauth.py` uses `v25.0`. Align both to `v25.0`.
4. **Persistence is the headline.** Replace the in-memory `_PAGE_TOKENS` dict with an encrypted SQLite table wired through `token_boundary.py`. Today tokens vanish on restart.
5. **Graph endpoints confirmed (v25.0):** single image = `POST /{page-id}/photos` with `url=`; link post = `POST /{page-id}/feed` with `message` + `link`; both need a Page token with `pages_manage_posts`.

## Existing Code Map (hardening targets)

| File | Current state | Phase 4 change |
|------|---------------|----------------|
| `backend/app/facebook_token_vault.py` | In-memory `_PAGE_TOKENS = {}` dict; lost on restart; plaintext | Replace with encrypted SQLite-backed store keyed per (merchant, channel/page); ciphertext only |
| `backend/app/token_boundary.py` | Models `storageMode: external_secret_ref`, `credentialFingerprint`, rotation; redacted serializer | Persist these records; store points to the encrypted secret |
| `backend/app/facebook_oauth.py` | Real OAuth; `choose_page()` auto-picks; `update_demo_facebook_channel` writes single channel; scopes `pages_show_list, pages_read_engagement, pages_manage_posts`; v25.0 | Split callback: fetch+return Pages (no auto-commit) → second "select page" call commits + stores token; persist multiple Pages, mark one active; expose capability health |
| `backend/app/facebook_publisher.py` | Text + scheduled `/feed`; `classify_error_class` (auth/permission/validation/rate_limit/transient); retry classification; permalink/post-ID capture; v20.0 | Add link + single-image (`/photos?url=`) publishing; pre-job media validation; read Page token from new persistent vault; align to v25.0; map 190→reconnect_required |
| `backend/app/server.py` | Manual route matching (`match_*`, if/else); `StoreError`→JSON | Add routes: list Pages, select active Page, capability/health, (media validation surfaces via existing publish path) |
| `backend/app/store.py` | `connected_channels`, media assets, publish jobs/attempts/events | New `facebook_page_tokens` table + Page records on `connected_channels`; media validation helpers |
| `src/api/publishingClient.js` | `loadFacebookConnection`, `publishFacebookPost` | Add Page-list / select-Page / health client fns |
| `src/main.jsx` / routes / components | `/app` workspace, connection UI | Page picker screen, health badges, failure-action buttons (UI hint: yes) |

## Topic 1 — Encrypted Token Persistence (D-01..D-07)

**Finding:** No stdlib AEAD. Recommended approach:
- Add dependency `cryptography` and use **Fernet** (`cryptography.fernet.Fernet`). Fernet = AES-128-CBC + HMAC-SHA256, URL-safe base64 key, authenticated, versioned, simplest correct option.
- Key from env var `LOCALPILOT_TOKEN_KEY` (a Fernet key string). Support `Fernet.generate_key()` for dev key generation in docs.
- **Fail-closed in production, graceful in dev** (D-04/D-05): determine "prod" via an explicit env signal (e.g. `LOCALPILOT_ENV=production`). If prod and key missing → refuse to start / refuse to persist. If dev and key missing → log a clear `INSECURE: token encryption disabled` warning and fall back to the current ephemeral path (store nothing durable, or store a clearly-marked dev placeholder).
- Create `backend/requirements.txt` pinning `cryptography`. Update README/AGENTS dev setup. Tests must run with a generated key (set `LOCALPILOT_TOKEN_KEY` in test setup).

**Schema (D-07):** new table, e.g.
```
facebook_page_tokens(
  id text primary key,
  merchant_id text,
  connected_channel_id text references connected_channels(id),
  page_id text,
  ciphertext blob,            -- Fernet token of the page access token
  credential_fingerprint text, -- from token_boundary (sha256:...)
  token_expires_at text,       -- D-06 expiry metadata (nullable; page tokens often long-lived)
  issued_at text,
  status text,                 -- active | reconnect_required
  is_active integer,           -- one active publish target per merchant (D-09)
  created_at text, updated_at text
)
```
Wire each row to a `token_boundary` record (`create_token_boundary(...)`) so the client only ever sees the redacted ref + fingerprint (existing `serialize_token_boundary_ref`).

**Invalidation detection (D-06):** Graph error **code 190** = invalid/expired OAuth token; **code 200/10** = permission. On a publish or health call returning 190 → set channel/token `status = reconnect_required`. No background refresh this phase.

**Pitfall:** existing tests `reset_for_tests()` clear the in-memory vault; the new store needs an equivalent test reset (delete rows / use a temp DB — the test harness already passes a temp sqlite path).

## Topic 2 — Page Selection (ACCT-01/02, D-08..D-10)

- `me/accounts?fields=id,name,category,link,tasks,access_token` already fetched in `fetch_pages`. The `tasks` array indicates capability — a Page the user can publish to includes `CREATE_CONTENT` (and/or `MANAGE`) in `tasks`. Use this for capability health (Topic 3).
- **Split the callback:** `complete_callback` currently calls `choose_page()` + `update_demo_facebook_channel` and redirects. Change to: store the long-lived user token (or the per-page tokens) transiently keyed to a connect session, return/redirect to a picker; a new endpoint (e.g. `POST /api/v1/facebook/pages/select`) commits the chosen page_id, stores its encrypted page token, marks it active.
- **Multiple Pages, one active (D-09):** persist all returned Pages as `connected_channels` (or page-token rows); `is_active` flag picks the publish target. Switching = flip `is_active` (D-10). Reconnect = re-run OAuth.

## Topic 3 — Capability & Permission Health (ACCT-03)

- Pre-publish gate states: `connected` (active page token present, `tasks` includes create/manage), `missing_permission` (token present but `pages_manage_posts` not granted / `tasks` lacks CREATE_CONTENT), `reconnect_required` (no token or last call returned 190).
- Cheap check: derive from stored `tasks` + token presence at selection time; confirm lazily on publish via existing `classify_error_class`. Optionally call `GET /me/permissions` or `debug_token` for a stronger check (planner's discretion per D-11).
- Surface via `connection_status()` / a per-channel health field consumed by the UI. Block `queue_facebook_publish` when not `connected` with a clear `StoreError`.

## Topic 4 — Media Validation + Publishing (FB-02/03, MEDIA-03, D-12..D-14)

- **Link post:** `POST /{page-id}/feed` with `message` + `link` (existing feed path; add `link` param).
- **Single image:** `POST /{page-id}/photos` with `url=<public asset url>` + `message`. Returns `{id, post_id}`; capture `post_id`/permalink (extend existing detail GET).
- **Pre-job validation (MEDIA-03/MEDIA-05):** before creating the publish job, validate:
  - file type in {jpg/jpeg, png, gif} (Graph supports more, but scope to these),
  - file size within Facebook limit (photos up to ~10MB — enforce a conservative cap, e.g. ≤ 10MB),
  - the asset/link URL is server-accessible (HEAD/GET returns 2xx and an image content-type for images).
  - Surface failures as `StoreError(400, ...)` with actionable messages BEFORE `create_publish_job`.
- **Snapshot integrity:** media ref + link must be captured into the approved snapshot (Phase 1 immutability), not read live at publish — publish reads from the frozen snapshot.
- Relevant Graph errors to map: 324 (missing/invalid image), 100 (invalid param), 368 (abusive), 200 (permissions), 190 (token).

## Topic 5 — App Review Evidence (FB-01)

Document (a markdown artifact under `docs/`):
- Meta app: App ID/secret config via env (`FACEBOOK_APP_ID/SECRET`), redirect URI, app mode.
- Permissions/scopes requested: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts` — `pages_manage_posts` requires **App Review + Business Verification + Advanced Access** for use on Pages the app doesn't own; Page admins/test users get standard access without review.
- Test Page + test user setup; screencast checklist demonstrating connect → select Page → approve → publish.
- Redacted diagnostics already satisfy "no token leakage" review concerns.

## Validation Architecture

**Dimension 8 (Nyquist) validation targets for this phase:**

- **Token encryption round-trip:** encrypt→store→load→decrypt yields original token; ciphertext column never equals plaintext; client serialization never contains the raw token (assert redacted ref only).
- **Fail-closed behavior:** with `LOCALPILOT_ENV=production` and no key → backend refuses to persist/use tokens (raises/exits); dev without key → labeled-insecure fallback, demo still runs.
- **Invalidation path:** simulated Graph 190 → channel becomes `reconnect_required`; publish blocked until reconnect.
- **Page selection:** OAuth callback returns N pages without committing; select endpoint commits exactly one active page + stores its token; switching flips active.
- **Capability gate:** publish blocked with clear error when health != connected; allowed when connected.
- **Media validation:** invalid type/oversize/unreachable URL → `400` before job creation; valid single image → `/photos?url=` job created; link post → `/feed` with link.
- **Idempotency preserved:** retrying an approved image/link publish does not create a duplicate post (existing idempotency + new media path).
- **No regressions:** existing `test_facebook_oauth.py`, `test_facebook_publisher.py`, `test_token_boundary.py` still pass (adapted for the persistent vault + required test key).

**Test seams:** backend tests inject a temp sqlite db path and use `opener`/fixtures for Graph calls (see `queue_facebook_publish(..., opener=None)` and `graph_base` params). Reuse these to simulate photo/link/error responses without network.

## Risks / Pitfalls

- **New dependency footprint:** adding `cryptography` changes deployment (the Cloudflare-worker static packaging is frontend-only and unaffected, but the Python backend now needs `pip install`). Document it.
- **Key management mistakes:** committing a key, or silently running insecure in prod. The fail-closed gate + `.gitignore` for any dev key file mitigate this.
- **Version drift:** unify Graph version to v25.0 to avoid behavioral mismatch between OAuth and publisher.
- **Page token longevity:** page tokens derived from a long-lived user token are effectively long-lived but revocable; do not assume non-expiry — store metadata and detect 190.
- **Public-URL media requirement:** if Phase 3 assets are not publicly reachable, `/photos?url=` fails; planner should confirm asset serving or flag byte-upload fallback (deferred per D-14).

## Canonical References
- `.planning/phases/04-facebook-page-publishing-hardening/04-CONTEXT.md` — locked decisions D-01..D-14.
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` §Phase 4, `.planning/STATE.md`.
- Existing code: `backend/app/facebook_oauth.py`, `facebook_publisher.py`, `facebook_token_vault.py`, `token_boundary.py`, `store.py`, `server.py`; `src/api/publishingClient.js`.
- Meta docs (v25.0): Pages API Posts (`/{page-id}/feed`), Page Photos (`/{page-id}/photos?url=`), Graph API error codes (190/200/324/368/100).

## RESEARCH COMPLETE
