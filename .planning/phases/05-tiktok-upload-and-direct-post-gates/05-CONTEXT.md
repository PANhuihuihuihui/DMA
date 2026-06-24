# Phase 5: TikTok Upload And Direct-Post Gates - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 enables TikTok as the second production channel after Facebook, while keeping Facebook disconnection/health behavior operational. The phase delivers connection status visibility, creator/disclosure controls, TikTok-specific publish-path gating, and TikTok media validation that classifies blocking failures before publish jobs are created. It does **not** add full manual-fallback workflows; it does **not** rework phase-3 content generation.

In-scope scope: ACCT-04, ACCT-05, ACCT-06, ACCT-07, TT-01, TT-02, TT-03, TT-04, TT-05, TT-06, TT-07, MEDIA-04.

Out of scope: generic Phase 6 manual fallback package lifecycle and additional channels.
</domain>

<decisions>
## Implementation Decisions

### Channel Connection Health and Disconnect
- **D-01:** Use persistent per-channel status with explicit states (`connected`, `missing_permission`, `expired_token`, `review_blocked`, `reconnect_required`, `disconnected`) backed by `connected_channels` and related token metadata.
- **D-02:** Keep content creation/editing active regardless of channel health; only publishing/scheduling actions for that channel are blocked when health is not `connected`.
- **D-03:** Channel disconnect (`ACCT-07`) marks that channel inactive/disconnected and immediately blocks new publish scheduling for that channel while preserving historical drafts/jobs.
- **D-04:** Publish UI and APIs for each channel must consistently enforce gating, not just display warnings (defense in depth against stale UI state).

### Creator Settings and Disclosure
- **D-05:** Fetch creator settings at connect/refresh, persist a versioned `creatorInfoSnapshot` per TikTok channel, and re-embed required creator info into each TikTok approval snapshot.
- **D-06:** TikTok approval workflow must require explicit disclosure/privacy/interaction confirmations before approval can be submitted for that draft.
- **D-07:** TikTok publish endpoints validate confirmation gates against the stored creator snapshot before queueing or publishing.

### Publish Path and Direct-Post Gate
- **D-08:** Default TikTok flow is upload-to-inbox/draft-style delivery for v1 to reduce risk.
- **D-09:** Backend owns route selection per publish attempt and exposes chosen route in job diagnostics.
- **D-10:** Direct Post is an opt-in mode but only enabled when app-audit eligibility, required scopes, creator-settings compatibility, and disclosure confirmations are all `true`.

### Media Validation and Generation Strategy
- **D-11:** TikTok media validation is backend-authoritative before publish-job creation; front-end checks may be optimistic-only.
- **D-12:** Failure classes must include media validation reasons aligned to `MEDIA-04` and `TT-07` taxonomy: file type, size, duration, URL accessibility, and media format compatibility.
- **D-13:** Draft generation should prefer assets that satisfy **the strictest relevant channel constraints** before variant expansion; TikTok variants should be generated only when needed for actual publish compliance/performance, not by default.

### Multi-Channel Foundation And Real Auth (added 2026-06-24)
- **D-14:** Phase 5 begins with a foundational schema slice (plan 05-01) that lands BEFORE TikTok-specific work. It introduces the multi-channel publishing backbone so TikTok (and later channels) plug into one pipeline instead of a TikTok-only path.
- **D-15:** Add a `channel_registry` table — a catalog of supported platforms (`facebook`, `tiktok`, future `xiaohongshu`/`instagram`/`google_business`) with per-platform capabilities (`max_caption_length`, `supported_media_json`, `required_scopes_json`, `platform_config_json`, `status` of `enabled|coming_soon|disabled`). Adding a channel = one INSERT + an adapter; no posts-table migration.
- **D-16:** Add a `scheduled_posts` table that REPLACES the disconnected `calendar_slots` surface and bridges scheduling to the publish pipeline. It carries a frozen content snapshot, a `channel_config_json`, scheduling fields (`scheduled_for`, `timezone`, `slot_label`), a unified status machine (`draft|approved|queued|publishing|published|failed|cancelled`), and FK linkage `approval_id` + `publish_job_id`. `calendar_slots` rows migrate with status mapping `scheduled→queued`, `in_review→draft`, `assisted→draft`.
- **D-17:** Add a `publish_dispatch_queue` table (mirrors symbo `CampaignUpdateQueue`) holding `scheduled_post_id`, `dispatch_at`, `status`, `attempt_count`, and `error_json` so a worker fires queued posts at their scheduled time with retry/backoff.
- **D-18:** Extend `connected_channels` with `channel_registry_id` (FK), `connected_by_user_id` (FK to users), and `capabilities_json`. A merchant has N connected channels (one per platform account); each keeps its own status + token boundary.
- **D-19:** Tenancy model is **one merchant = one local business; a user belongs to exactly one merchant** (no agency-of-many-businesses layer, no memberships join table). Every query is scoped by the resolved `merchant_id`.
- **D-20:** Replace the demo/fake login with **real authentication now**. Add a `sessions` table (`user_id`, `merchant_id`, `status` of `authenticated|expired|logged_out`, `created_at`, `last_seen_at`, `expires_at`, `user_agent`, `ip_hash`). The backend reads a session cookie → resolves `user_id`+`merchant_id` → scopes all data; expired/absent sessions are rejected. Never store raw IPs or secrets.
- **D-21:** The three state machines stay independent: session (login), channel-connection, and post lifecycle. Gate: a post may advance `approved → queued → publishing` only when its `connected_channel.status == connected`; otherwise it holds at `approved` and the UI shows a reconnect prompt. Content creation/editing is never blocked (consistent with D-02).
- **Reference:** Design canvas `[user-channel-post-model]` and `[scheduled-post-redesign]`; symbo `Campaign`/`ChannelCampaign`/`CampaignUpdateQueue` in `/Users/huijie/Documents/symbo/libs/orm/advertiser/models.py` and platform-isolated routers in `/Users/huijie/Documents/symbo/apps/api/apps/{meta,tiktok}/router.py`.

### the agent's Discretion
- Exact per-channel health refresh cadence and cache strategy (pure read-through vs periodic sync).
- Exact TT failure-class taxonomy and enum keys, as long as they remain mappable into backend analytics and operator diagnostics.
- Exact media validation location within `publish` vs `queue` service functions and whether a shared policy module is used.
- Whether TikTok route metadata is stored directly on `publish_jobs` as a dedicated `publishMode` field or in serialized diagnostics.

</decisions>

<canonical_refs>
## Canonical References

### Project And Scope
- `.planning/PROJECT.md` — platform order, security constraints, merchant-owned account requirement, and owner-approval requirement.
- `.planning/REQUIREMENTS.md` — TT/ACCT/MEDIA requirements referenced by this phase.
- `.planning/ROADMAP.md` §"Phase 5: TikTok Upload And Direct-Post Gates" — phase goal, requirements, and success criteria.
- `.planning/STATE.md` — current execution context when phase planning starts.

### Existing Backend Seams
- `backend/app/server.py` — API contract pattern for channel-specific routes (`/api/v1/connect`, `/api/v1/approvals/.../publish-*`) and manual route registration style.
- `backend/app/contracts.py` — approval snapshot + diagnostics contracts used by publish jobs.
- `backend/app/store.py` — `connected_channels`, `publish_jobs`, `publish_attempts`, `publish_outcomes`, and migration-friendly schema surface.
- `backend/app/facebook_oauth.py` — channel health/status model and session/token handoff pattern directly applicable to TikTok.
- `backend/app/facebook_publisher.py` — publish attempt lifecycle and provider diagnostics pattern to mirror for TikTok.
- `backend/app/token_boundary.py` and `backend/app/token_crypto.py` — secure secret boundary and encrypted/ref redaction practices.
- `backend/app/facebook_token_vault.py` — token persistence pattern for channel-scoped token metadata.
- `src/api/publishingClient.js` — frontend API client extension points for TikTok status, creator info, and publish queue calls.

### Tests and Validation
- `backend/tests/test_facebook_oauth.py` — reference for secure callback/session state handling.
- `backend/tests/test_facebook_publisher.py` — reference for job lifecycle assertions and diagnostics redaction.
- `backend/tests/test_token_boundary.py` — token boundary expectations that should remain stable for TikTok extension.

### Planner Reference Maps
- `.planning/codebase/ARCHITECTURE.md` — current architecture and extension seam at backend route + DB.
- `.planning/codebase/INTEGRATIONS.md` — current integration boundary and existing auth/credential patterns.
- `.planning/codebase/STACK.md` — runtime/dependency constraints for backend-first phase changes.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `JsonHandler.route_request` in `backend/app/server.py` provides predictable route matching style for new TikTok endpoints.
- `connection_status`, `list_pages_for_session`, and explicit session state patterns in `backend/app/facebook_oauth.py` can be adapted for TikTok connection state.
- `publish_approved_snapshot` + `provider_diagnostics` in `backend/app/facebook_publisher.py` provide status transition and diagnostics scaffolding.
- `contracts.serialize_draft_version` / `build_approval_snapshot` are already structured for adding TikTok-specific payload fields.

### Established Patterns
- Token-boundary and redaction patterns remain unchanged: no raw secrets in workflow outputs.
- Route-level errors use `store.StoreError` with stable status/message.
- Backend writes canonical publish events (`approved`, `queued`, `publishing`, terminal state) and attempts/outcomes in normalized tables, which TikTok should reuse.

### Integration Points
- Existing frontend workflow uses `publish-facebook` endpoint and publish-job views (`loadPublishJob`, `retryPublishJob`) in `src/api/publishingClient.js`; TikTok endpoints should mirror these patterns.
- App session and campaign/workspace flows remain in phase-3 services and should continue to call a stable backend `loadPublishingWorkflow` shape.

</code_context>

<specifics>
## Specific Ideas

- Content creation should never be blocked by a channel disconnect; only scheduling/publishing for that channel is blocked.
- TikTok connection state should be visible as a first-class operational state (including `review_blocked` and `reconnect_required`) and should stop new job starts for that channel.
- Media generation should default to one compliant variant that satisfies strongest cross-channel constraints, and generate additional variants only when needed for performance or higher conversion potential.

</specifics>

<deferred>
## Deferred Ideas

- Full automatic channel token refresh/expiry remediation (beyond simple `expired_token` marking) can be revisited in a later maintenance phase.
- Full media transcoding/normalization pipeline and multi-format variant generation can be postponed until performance testing proves necessity.
- Cross-channel shared TikTok content variant engine governance should be decided after Phase 6 manual fallback and retry hardening.

</deferred>

---

*Phase: 5-TikTok Upload And Direct-Post Gates*
*Context gathered: 2026-06-24*
