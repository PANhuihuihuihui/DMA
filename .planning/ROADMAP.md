# Roadmap: LocalPilot AI

## Overview

LocalPilot AI moves from a frontend-only React/Vite demo into a real merchant-owned publishing MVP. The work starts by adding backend-owned publishing records, approval snapshots, status tracking, and a fake adapter while preserving the current demo. A Postiz-style publishing engine spike happens before deep custom provider wrappers. Phase 3 is now the top-priority customer-demo MVP: replicate Predis.ai's recognizable content creation, brand kit, creative editor, scheduling, approval, competitor idea, and analytics loop, then make it 1% better for local SMBs with owner approval and a measurable response/proof loop. Facebook OAuth publishing remains the first real adapter inside that broader product. TikTok and other channels follow through assisted or official paths as they become reliable. Xiaohongshu remains deferred to v2 until a compliant official or partner publishing route is proven.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Backend Publishing Foundation** - Adds API-backed workflow state, fake publishing, approval snapshots, status tracking, and preserves the current demo. (completed 2026-06-10)
- [x] **Phase 2: Publishing Engine Reuse Decision** - Spikes Postiz-style engine reuse and rejects AutoCLI-style production publishing before custom provider wrappers. (completed 2026-06-10)
- [ ] **Phase 3: Predis Replica Plus Local Proof Loop MVP** - Replicates Predis.ai's core prompt-to-content, brand kit, editor, calendar, approval, competitor idea, and analytics loop, then adds local owner approval, Facebook OAuth publishing, and measurable response hooks.
- [ ] **Phase 4: Facebook Page Publishing Hardening** - Hardens merchant-owned Facebook Page publishing for production readiness, including encrypted token persistence, permission health, app review evidence, media validation, retries, and fallback.
- [x] **Phase 5: TikTok Upload And Direct-Post Gates** - Connects TikTok second and delivers approved TikTok drafts through official upload/draft paths while gating Direct Post. (completed 2026-06-24)
- [x] **Phase 6: Manual Fallback And Pilot Support** - Gives merchants and operators safe paths for blocked jobs, manual packages, retries, and diagnostics. (completed 2026-06-25)

**Milestone v2.0 — Predis-style Generative Engine + Smart Onboarding:**

- [ ] **Phase 7: Google Login And Auth** - Adds real Google OAuth sign-in with backend ID-token verification on top of the v1.0 sessions foundation.
- [ ] **Phase 8: Website-Crawl Smart Onboarding** - Crawls a merchant's website to auto-generate a brand/business profile, style, and content-setting defaults.
- [ ] **Phase 9: Generation Engine And Image Generation** - Adds a provider-agnostic async generation contract and real image/ad-creative generation.
- [ ] **Phase 10: Credit Metering And Model Selection** - Meters generation credits per model/type/duration, exposes model selection, and enforces plan limits.
- [ ] **Phase 11: Carousel Generation** - Generates multi-slide carousels from an idea/URL using real image generation and brand layout.
- [ ] **Phase 12: Text-To-Video And UGC Avatar** - Generates short videos and UGC avatar videos through video-model providers with voiceover.

## Phase Details

### Phase 1: Backend Publishing Foundation

**Goal**: LocalPilot has API-backed publishing records, a fake publish lifecycle, approval snapshots, retry-safe status tracking, and preserved current demo/marketing routes.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, SEC-01, SEC-02, SEC-03, SEC-04, SEC-06, APPR-04, APPR-05, APPR-06, STATUS-01, STATUS-02
**Success Criteria** (what must be TRUE):

  1. Merchant can keep using the existing marketing page and demo workspace while publish-critical records are persisted through backend APIs instead of browser localStorage.
  2. Merchant can approve a specific platform draft version and see the frozen payload snapshot that will be used for publishing.
  3. Merchant can run a fake publish job through draft, approved, queued, publishing, published, failed, and retry-needed states with a visible per-platform timeline.
  4. Retrying an approved fake publish job records a new immutable attempt without duplicating the approved external outcome.
  5. Support-visible diagnostics and events show approver, draft version, timestamps, and redacted provider details without exposing tokens or secrets.

**Plans**: 9 plans

Plans:

- [x] 01-01-PLAN.md — Backend contract and persistence foundation
- [x] 01-02-PLAN.md — Frontend backend-backed approval workflow
- [x] 01-03-PLAN.md — Backend fake publish lifecycle
- [x] 01-04-PLAN.md — React fake publish timeline
- [x] 01-05-PLAN.md — Retry, idempotency, and redaction backend
- [x] 01-06-PLAN.md — Retry publish control and attempt timeline UI
- [x] 01-07-PLAN.md — Read-only redacted debug diagnostics API
- [x] 01-08-PLAN.md — Hidden debug route and route extraction
- [x] 01-09-PLAN.md — Storage boundary and final verification scripts

**UI hint**: yes

### Phase 2: Publishing Engine Reuse Decision

**Goal**: The team can decide whether to wrap Postiz-style publishing infrastructure or build native adapters before deep provider-specific request wrappers.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: ENGINE-01, ENGINE-02, ENGINE-03, ENGINE-04, ENGINE-05, SEC-05
**Success Criteria** (what must be TRUE):

  1. Team can run a focused Postiz-style self-hosted/API/MCP spike against the PublishingProvider contract without changing LocalPilot workflow records.
  2. Spike evidence shows whether Postiz-style tooling can connect Facebook Pages, handle TikTok upload or posting flows, submit media, return status, expose errors, and fit licensing/deployment needs.
  3. A documented go/no-go decision selects Postiz-style wrapping or native provider adapters before deep Facebook or TikTok custom request wrappers are built.
  4. Production publishing paths reject scraping, cookie-based posting, and AutoCLI/browser-session automation, with AutoCLI allowed only for internal research if needed.

**Plans**: 1 plan

Plans:

- [x] 02-01-PLAN.md — Bounded Postiz-vs-native comparison matrix, evidence capture, and go/no-go decision memo

### Phase 3: Predis Replica Plus Local Proof Loop MVP

**Goal**: Merchant can enter one local business offer and see a Predis-style workflow that generates branded multi-platform content, previews posts/carousels/video scripts, schedules the week, requires owner approval, publishes approved Facebook content through OAuth when configured, and shows measurable local response evidence without buying ads.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: CAMP-01, CAMP-02, CAMP-03, CAMP-04, CAMP-05, CAMP-06, LOCAL-01, LOCAL-02, LOCAL-03, LOCAL-04, LOCAL-06, APPR-01, APPR-02, APPR-03, APPR-04, APPR-05, APPR-06, ACCT-01, ACCT-02, FB-02, FB-04, STATUS-01, STATUS-02, SEC-01, SEC-04, ROI-01, ROI-02
**Success Criteria** (what must be TRUE):

  1. Merchant can configure a brand kit and local business profile with location, industry, offer, audience, tone, language, and goals.
  2. Merchant can enter one local idea and generate a weekly content batch with Facebook, Instagram, TikTok/Reels, and Google Business Profile outputs.
  3. Merchant can see Predis-like surfaces for AI generation, creative previews, captions, hashtags, calendar scheduling, approvals, connected accounts, competitor ideas, and analytics.
  4. Merchant can edit drafts, preserve versions, approve exact payloads, and schedule or publish approved Facebook drafts through OAuth without pasting access tokens.
  5. Merchant can see proof hooks and response events such as short-link clicks, QR scans, call taps, direction taps, booking clicks, DMs, coupon redemptions, and owner-confirmed mentions without exact ROI claims.

**Plans**: 2 plans
Plans:

- [x] 03-01-PLAN.md — Predis replica plus local proof loop MVP
- [~] 03-02-PLAN.md — Predis logged-in reference clone hardening (implemented; build/screen gate blocked by local Rollup native binary)

**UI hint**: yes

### Phase 4: Facebook Page Publishing Hardening

**Goal**: Merchant can use production-ready Facebook Page publishing through the selected Page, with secure token persistence, permission health, media validation, retry/fallback, support diagnostics, and app-review evidence.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: ACCT-01, ACCT-02, ACCT-03, FB-01, FB-02, FB-03, FB-04, FB-05, FB-06, MEDIA-03
**Success Criteria** (what must be TRUE):

  1. Merchant can start official Facebook connection, select a managed Page, and see whether that Page has required publishing capability before jobs are allowed.
  2. Approved text-only Facebook Page drafts publish through the merchant-selected Page when required permissions are available.
  3. Approved Facebook Page drafts with links or media publish when Facebook media validation passes, and validation errors are shown before job creation.
  4. Merchant can see stored Facebook post IDs, public URLs or provider references, normalized failure classes, and Page-specific retry, reconnect, or manual fallback actions.
  5. The Meta app, permissions, app review, test Page, and screencast evidence needed for Facebook Page publishing are documented for production readiness.

**Plans**: 3 plans
Plans:

- [x] 06-01-PLAN.md — Manual fallback policy + cross-publisher terminal-state wiring
- [x] 06-02-PLAN.md — Operator-gated admin console for redacted inspection, retry, and mark-support
- [x] 06-03-PLAN.md — Redacted evidence bundle export for app review and pilot support
**UI hint**: yes

### Phase 5: TikTok Upload And Direct-Post Gates

**Goal**: Merchant can connect TikTok second, use creator-info driven settings, and deliver approved TikTok drafts through official upload/draft paths, with Direct Post gated.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: ACCT-04, ACCT-05, ACCT-06, ACCT-07, TT-01, TT-02, TT-03, TT-04, TT-05, TT-06, TT-07, MEDIA-04
**Success Criteria** (what must be TRUE):

  1. Merchant can start official TikTok connection and see connected-channel health for Facebook and TikTok, including reconnect-required, missing-permission, expired-token, or review-blocked states.
  2. Merchant can disconnect Facebook or TikTok accounts and new publish jobs stop using that connection.
  3. Merchant can choose TikTok privacy and interaction options returned by creator-info APIs and explicitly confirm disclosure settings before approval or publishing.
  4. Approved TikTok drafts can be delivered through official Upload-to-Inbox or draft-style flow after TikTok media validation, with publish IDs, status responses, and provider diagnostics stored.
  5. TikTok failures are classified by authentication, scope, creator setting mismatch, media validation, rate limit, audit/visibility block, platform transient, or unknown error, and Direct Post only becomes available when all official gates are satisfied.

**Plans**: 5 planned

Plans:

- [x] 05-01-PLAN.md — Multi-channel publishing foundation + real session auth (channel_registry, scheduled_posts, publish_dispatch_queue, sessions; calendar_slots migration)
- [x] 05-02-PLAN.md — Channel health visibility + disconnect enforcement without blocking content creation (ACCT-04..07)
- [x] 05-03-PLAN.md — Creator-info snapshot + disclosure, privacy, and interaction approval gates (TT-01..03)
- [x] 05-04-PLAN.md — TikTok upload/draft publish path + backend-owned Direct Post gating (TT-04..06)
- [x] 05-05-PLAN.md — Backend media validation + failure taxonomy + strictest-channel generation defaults (TT-07, MEDIA-04)

**UI hint**: yes

### Phase 6: Manual Fallback And Pilot Support

**Goal**: Internal operator (and the system) can resolve blocked publish jobs safely through automatic manual-fallback marking, redacted diagnostics, support actions, and app-review evidence export.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: STATUS-03, ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04
**Scope note (2026-06-24):** Merchant-facing manual package (STATUS-04) and manual completion tracking (STATUS-05) were descoped from this phase and deferred post-v1.0 (see `06-CONTEXT.md`).
**Success Criteria** (what must be TRUE):

  1. System marks a publish job manual fallback required when direct publishing is blocked by official API access, review status, account eligibility, or media constraints (terminal non-retryable failure classes).
  2. Internal operator can inspect merchant, channel, job, attempt, and error status with redacted provider IDs, trace IDs, error classes, and next recommended action.
  3. Internal operator can trigger safe retry or mark a manual support path without viewing tokens or secrets.
  4. System can export a per-job redacted app-review/pilot evidence bundle (scopes, chosen route, gate results, confirmations) for Meta/TikTok review and troubleshooting.

  _Deferred (post-v1.0): merchant download/copy manual package; merchant manual completion tracking._

**Plans**: TBD
**UI hint**: yes

---

## Milestone v2.0 Phase Details

### Phase 7: Google Login And Auth

**Goal**: A user can sign in with Google, and the backend verifies the Google ID token and issues a LocalPilot session linked to a user and merchant.
**Mode:** mvp
**Depends on**: Phase 5 (sessions/auth foundation)
**Requirements**: GAUTH-01, GAUTH-02
**Success Criteria** (what must be TRUE):

  1. A user can complete Google sign-in and reach an authenticated session.
  2. The backend verifies the Google ID token signature, `aud`, `exp`, and `iss`, and rejects invalid or mis-audienced tokens.
  3. The system uses the Google `sub` as the stable user key and links or creates the user and merchant.
  4. Provider secrets (Google client secret) stay server-side and never reach the browser or committed files.

**Plans**: TBD
**UI hint**: yes

### Phase 8: Website-Crawl Smart Onboarding

**Goal**: A merchant can enter a website URL and the backend crawls public info to auto-generate a brand/business profile, style, and content-setting defaults they can review and edit.
**Mode:** mvp
**Depends on**: Phase 7
**Requirements**: ONBOARD-01, ONBOARD-02, ONBOARD-03, ONBOARD-04, ONBOARD-05
**Success Criteria** (what must be TRUE):

  1. Merchant can submit a website URL and receive an auto-generated business profile (name, description, digital presence).
  2. System extracts brand style (logo, colors, fonts) to seed the brand kit and proposes content-setting defaults (tonality, language, timezone, voiceover, avatar).
  3. Merchant can review and edit the generated profile before confirming; re-fetch replaces details only after an explicit warning.
  4. Crawl fetches public info only, stores no site credentials, and sanitizes untrusted content.

**Plans**: TBD
**UI hint**: yes

### Phase 9: Generation Engine And Image Generation

**Goal**: The backend can route generation requests to a configured model/provider through a provider-agnostic async contract and produce real images / ad creatives.
**Mode:** mvp
**Depends on**: Phase 5 (publish lifecycle pattern)
**Requirements**: GEN-01, GEN-02, GEN-03
**Success Criteria** (what must be TRUE):

  1. A generation request routes to a configured `{provider, model}` without exposing API keys.
  2. Generation runs as an async job with a normalized status lifecycle and a result reference surfaced to the client.
  3. Merchant can generate a real image / ad creative from a prompt and brand context.
  4. The provider abstraction allows swapping models/providers via configuration.

**Plans**: TBD
**UI hint**: yes

### Phase 10: Credit Metering And Model Selection

**Goal**: The system meters generation credits, exposes model selection with per-model cost, and enforces plan limits before expensive generation runs.
**Mode:** mvp
**Depends on**: Phase 9
**Requirements**: CREDIT-01, CREDIT-02, CREDIT-03
**Success Criteria** (what must be TRUE):

  1. System meters credit usage per generation by content type, model, and duration.
  2. Merchant can select among available models with visible per-model credit cost.
  3. System enforces plan credit limits and blocks or queues generation when exhausted.

**Plans**: TBD
**UI hint**: yes

### Phase 11: Carousel Generation

**Goal**: A merchant can generate a multi-slide carousel from an idea or URL using real image generation and brand layout.
**Mode:** mvp
**Depends on**: Phase 9, Phase 10
**Requirements**: GENC-01
**Success Criteria** (what must be TRUE):

  1. Merchant can generate a multi-slide carousel from an idea or URL.
  2. Slides use real generated imagery and the merchant's brand layout.
  3. Carousel generation is metered through the credit system.

**Plans**: TBD
**UI hint**: yes

### Phase 12: Text-To-Video And UGC Avatar

**Goal**: A merchant can generate short videos and UGC avatar videos through video-model providers, with voiceover, gated by credits.
**Mode:** mvp
**Depends on**: Phase 9, Phase 10
**Requirements**: GENV-01, GENV-02
**Success Criteria** (what must be TRUE):

  1. Merchant can generate a short video from a text prompt (script, scenes, captions, voiceover).
  2. Merchant can generate a UGC avatar video by selecting an avatar and providing a script, producing a video with voiceover.
  3. Video generation is metered and gated by plan credit limits.

**Plans**: TBD
**UI hint**: yes

## Coverage

The roadmap still preserves the original Facebook-first, TikTok-second publishing order, but Phase 3 now pulls selected analytics/proof-loop requirements forward because the v3 research made measurable response evidence part of the customer-demo wedge. Xiaohongshu direct publishing remains deferred to v2.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Publishing Foundation | 9/9 | Complete   | 2026-06-10 |
| 2. Publishing Engine Reuse Decision | 1/1 | Complete | 2026-06-10 |
| 3. Predis Replica Plus Local Proof Loop MVP | 1/2 | In progress | - |
| 4. Facebook Page Publishing Hardening | 3/8 | In Progress|  |
| 5. TikTok Upload And Direct-Post Gates | 5/5 | Complete    | 2026-06-24 |
| 6. Manual Fallback And Pilot Support | 0/TBD | Not started | - |
| 7. Google Login And Auth (v2.0) | 0/TBD | Not started | - |
| 8. Website-Crawl Smart Onboarding (v2.0) | 0/TBD | Not started | - |
| 9. Generation Engine And Image Generation (v2.0) | 0/TBD | Not started | - |
| 10. Credit Metering And Model Selection (v2.0) | 0/TBD | Not started | - |
| 11. Carousel Generation (v2.0) | 0/TBD | Not started | - |
| 12. Text-To-Video And UGC Avatar (v2.0) | 0/TBD | Not started | - |

---
*Roadmap created: 2026-06-09*
*Milestone v2.0 added: 2026-06-24*
