# Project Research Summary

**Project:** LocalPilot AI
**Domain:** Local-business AI marketing operator with real merchant-owned social publishing
**Researched:** 2026-06-09
**Confidence:** MEDIUM-HIGH

## Executive Summary

LocalPilot AI is not a generic scheduler; it is a local-business marketing operator that turns one merchant offer, service, product, or event into platform-native posts and publishes only after explicit owner approval. Experts build this kind of product as a regulated integration workflow: server-side OAuth, durable account and draft state, approval snapshots, asynchronous publishing jobs, media validation, status reconciliation, retries, and support diagnostics. The current React/Vite prototype proves the user story, but real publishing requires a backend boundary before any live Facebook or TikTok integration.

The recommended v1 approach is Facebook first, TikTok second, Xiaohongshu deferred. Facebook should target merchant-owned Facebook Pages through official Page publishing paths. TikTok should start with official Upload-to-Inbox/Draft and only enable Direct Post after app audit, creator-info preflight, privacy/disclosure UX, media validation, and status handling are proven. Xiaohongshu should remain an assisted export/content-package workflow until LocalPilot confirms an official or partner route for merchant-owned organic note publishing.

The highest-leverage technical decision is to build LocalPilot's own product model and publishing state machine while investigating reusable publishing infrastructure behind an adapter. Postiz-style self-hosted/API tooling is worth a focused spike because it may already handle OAuth channels, media upload, provider schemas, scheduling, and status plumbing. AutoCLI/browser-session tooling should be rejected for production publishing because it relies on scraping/cookies/browser automation patterns that conflict with official API compliance and merchant trust.

## Key Findings

### Recommended Stack

LocalPilot should keep the existing React/Vite frontend for the merchant review workflow, then add a backend-owned publishing foundation. The backend should own account connections, token storage, campaign/draft persistence, approval audit trails, media storage, publish jobs, retries, and platform status normalization. Do not call social APIs directly from React and do not store OAuth tokens in browser `localStorage`.

**Core technologies:**
- React/Vite: merchant workflow UI - preserve the working prototype while replacing localStorage publishing state with API-backed records.
- FastAPI on Python 3.11+: backend API - matches symbo patterns and fits OAuth callbacks, typed schemas, integration adapters, and job orchestration.
- PostgreSQL with SQLAlchemy 2 and Alembic: durable product state - merchants, users, connected accounts, campaigns, drafts, approvals, media, publish jobs, attempts, and events.
- Authlib plus backend sessions/cookies: OAuth and LocalPilot auth - social token exchange and refresh must happen server-side.
- Redis plus Celery/RQ/Arq-style worker: asynchronous publishing - media uploads and platform calls need retries, idempotency, and status updates outside HTTP request handlers.
- S3/R2-compatible object storage: media assets - TikTok and publishing engines need stable HTTPS-reachable media.
- PublishingProvider interface: platform boundary - support a Postiz provider first, with native Meta/TikTok adapters as fallback.
- Structured logging and publish_event records: observability - early pilots need traceable, redacted, merchant-safe diagnostics.

Critical version/operational requirements: use explicit Graph API versions for Meta; confirm 2026 Meta permission/app-review details in an authenticated developer account; use TikTok official Content Posting API flows; keep secrets in environment/secret manager/token store only.

### Expected Features

The first real MVP should be an owner-approved publishing workbench. A merchant connects official accounts, enters one local offer, gets Facebook and TikTok drafts, edits/regenerates if needed, approves each platform variant, then publishes or receives a manual fallback package with traceable status.

**Must have (table stakes):**
- Merchant-owned account connection - Facebook Page and TikTok creator accounts, never a shared LocalPilot identity.
- Facebook Page selection and eligibility check - merchants may manage multiple Pages and need clear publish readiness.
- TikTok creator-info preflight - privacy, duet/stitch/comment, duration, and account constraints must come from TikTok.
- One-offer campaign generator - local offer input creates distinct Facebook and TikTok drafts.
- Platform-native draft editor - owners can adjust captions, CTA, hashtags, links, disclosures, and media.
- Explicit owner approval - publish jobs require an approved, frozen payload snapshot.
- Publishing lifecycle timeline - draft, needs review, approved, queued, publishing, inbox delivered, moderation pending, published, failed, retry needed, manual completion.
- Media upload and validation - server-side media storage plus platform-specific file, duration, size, URL, and disclosure checks.
- Error classification and retry - normalize auth, permission, validation, rate-limit, platform, moderation, and transient failures.
- Manual fallback package - usable outcome when app review, platform eligibility, or API access blocks direct publishing.

**Should have (competitive):**
- Local CTA library - calls, bookings, DMs, map clicks, coupon scans, saves, and walk-ins.
- Platform-specific local angles - Facebook community/context copy; TikTok hook, visual action, and short-form pacing.
- Bilingual/local-cultural variants - English/Chinese variants without requiring Xiaohongshu direct publishing.
- Brand voice and claim controls - forbidden words, regulated-claim warnings, required disclaimers, owner-safe tone.
- Pilot support/admin diagnostics - raw provider IDs, trace IDs, normalized errors, retry controls, and manual package support.
- Simple ROI metadata - UTM, coupon code, booking URL, QR/link shortener placeholders attached to drafts.

**Defer (v2+):**
- Xiaohongshu direct publishing - no confirmed general official SMB organic publishing route.
- Paid ads publishing - different APIs, permissions, budgets, and compliance model.
- Instagram, Google Business Profile, LinkedIn, X, and other channels - keep the data model extensible but do not dilute Facebook/TikTok proof.
- Advanced scheduler/calendar - immediate approved publishing is the proof point.
- Deep analytics dashboards - store IDs and CTA metadata now; analyze later.
- Multi-location franchise/agency workflow - add after one-business merchant workflow is real.
- TikTok music/sound automation and trend ingestion - use upload-to-inbox/manual TikTok completion first.

### Architecture Approach

The architecture should split LocalPilot product ownership from publishing-engine mechanics. LocalPilot owns merchant onboarding, campaign/draft generation, approval, local ROI metadata, status language, tenant checks, and audit logs. The publishing engine adapter owns provider-specific channel connection, schema mapping, media submission, status polling/webhooks, and error normalization. Postiz should be evaluated as an engine behind this adapter, not used as the LocalPilot product database or approval system.

**Major components:**
1. React/Vite app - merchant input, draft review/edit/regenerate, account connection entry points, approval actions, and status display.
2. LocalPilot API - authenticated product API for campaigns, drafts, approvals, connected channels, media, and publish jobs.
3. Campaign/Draft service - converts one local offer into platform-native draft records and versions.
4. Approval service - enforces per-platform approval tied to a specific draft version and frozen payload.
5. Publishing service and worker - creates idempotent publish jobs, executes platform submissions asynchronously, retries safely, and records attempts.
6. PublishingEngine adapter - stable port over Postiz API or native Meta/TikTok adapters.
7. PostgreSQL database - durable source of truth for merchant/product/publishing state.
8. Object storage/CDN - media assets with platform-compatible HTTPS access.
9. Secrets/token store - encrypted platform tokens and app credentials, never browser-readable.

Key patterns to follow: versioned `/api/v1` routes; tenant-aware API dependencies; immutable approval snapshots; idempotency keys by draft/channel/approved version; one job with many attempts; redacted platform diagnostics; status polling/webhook-ready design; fake publishing adapter before real credentials; Postiz HTTP API spike before native rebuild; symbo-style FastAPI/config/middleware lessons without copying secrets or ad/conversion assumptions.

### Critical Pitfalls

1. **Meta App Review and Page permission complexity** - build a Facebook connection/review phase with minimum scopes, explicit Page selection, test Page, reviewer credentials, screencast, and reconnect UX.
2. **Wrong Facebook token/account model** - support Pages only, model connected user/Page/grant/credential separately, validate Page access tokens server-side, and never ask merchants to paste tokens.
3. **Treating TikTok Direct Post as immediate public posting** - start with Upload-to-Inbox/Draft, query creator info, show actual privacy/disclosure controls, and mark public success only after status/webhook confirmation.
4. **Missing TikTok quota, privacy, disclosure, and media constraints** - preflight media/caption/settings, rate-limit per merchant/account/token, and retry only transient failures.
5. **Shipping Xiaohongshu direct publishing without an official route** - keep Xiaohongshu as assisted export until official/partner organic publishing permissions are proven.
6. **Using scraping, cookies, or browser automation for production publishing** - ban AutoCLI-style browser sessions for merchant publishing; allow only internal research against owned test accounts.
7. **Keeping OAuth tokens or PII in localStorage** - introduce backend/session/token storage before live OAuth and keep browser storage to non-sensitive preferences.
8. **Retrying publish jobs without idempotency or audit discipline** - store immutable approved payloads, attempt records, external IDs, error classes, and terminal states to prevent duplicate posts.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Backend Publishing Foundation

**Rationale:** Every real publishing path depends on server-owned auth, persistence, media, approval, jobs, and token boundaries. Building platform calls first would turn the prototype's localStorage model into a security and audit liability.

**Delivers:** FastAPI skeleton, PostgreSQL schema, API-shaped frontend service layer, merchant/user/business records, campaign/draft records, connected-channel metadata, approval snapshots, media asset records, publish job/attempt/event records, fake publishing adapter, and basic status UI.

**Addresses:** `REQ-ACCOUNT-*`, `REQ-CAMPAIGN-001`, `REQ-DRAFT-001`, `REQ-APPROVAL-*`, `REQ-STATUS-001`, `REQ-MEDIA-001` foundations.

**Avoids:** localStorage token/PII risk, accidental publishing without frozen approval, synchronous platform calls, no audit trail.

### Phase 2: Publishing Engine Reuse Spike

**Rationale:** Postiz may already solve OAuth channels, provider schemas, media upload, status, and retries. Validate reuse before rebuilding platform-specific request layers, but keep LocalPilot's domain model independent.

**Delivers:** `PublishingProvider` contract, Postiz API sandbox/self-hosted spike, Facebook Page connection/post test, TikTok upload/direct feasibility test, media hosting test, status/error mapping notes, AGPL/deployment review, and go/no-go decision: Postiz provider vs native Meta-first adapter.

**Addresses:** CLI/MCP/self-hosted publishing engine reuse investigation, especially AutoCLI vs Postiz-style tooling.

**Avoids:** premature custom integration build, production shelling out to CLI, Postiz becoming the product database, AutoCLI/browser automation in customer workflows.

### Phase 3: Facebook Page Connection and Review Readiness

**Rationale:** Facebook is first, but production merchants will not work without correct OAuth, Page selection, permissions, app review, token validation, and reconnect flows.

**Delivers:** Meta developer app configuration checklist, backend OAuth flow, Page listing/selection, permission/capability checks, connected Page health, reconnect UX, test Page, App Review artifacts, and admin diagnostics.

**Addresses:** merchant-owned Facebook Page connection, Page eligibility, server-side token storage, account health, minimum permission review.

**Avoids:** developer-only publishing, wrong token type, profile/group targeting, unreviewable Meta permission requests.

### Phase 4: Facebook Approved Publishing Proof

**Rationale:** The first field-sales proof is one merchant offer becoming an approved Facebook Page post through the merchant's own official Page.

**Delivers:** approved immediate Facebook Page text/link/image publishing, frozen payload snapshot, media validation, job worker submission, platform post ID/public URL capture where available, normalized errors, retry/reconnect/manual fallback states, and owner-facing status timeline.

**Addresses:** Facebook Page publishing first, explicit approval, media validation, publishing lifecycle, error taxonomy, manual fallback package.

**Avoids:** duplicate posts, unsupported Facebook targets, hidden permission failures, generic "failed" status.

### Phase 5: TikTok Upload-to-Inbox/Draft Proof

**Rationale:** TikTok is second and has official paths, but public Direct Post requires audit and creator-specific settings. Upload-to-Inbox/Draft gives a compliant v1 TikTok outcome while preserving owner control.

**Delivers:** TikTok OAuth, creator-info query, video media validation, privacy/disclosure/settings snapshot, Upload-to-Inbox/Draft submission, `publish_id` storage, status polling/webhook-ready updates, inbox-delivered/manual-completion state, and rate-limit-aware retries.

**Addresses:** merchant-owned TikTok connection, TikTok creator info preflight, explicit consent, media validation, status lifecycle, manual finish state.

**Avoids:** overpromising public Direct Post, hard-coded privacy settings, music-rights complexity, retrying validation or policy failures.

### Phase 6: Local-Business Differentiation and Pilot Support

**Rationale:** Publishing alone makes LocalPilot a scheduler. Local business value comes from offer-to-post strategy, local CTAs, bilingual/cultural variants, brand-safety controls, and supportable pilot operations.

**Delivers:** local offer schema, CTA library, platform-specific generation rules, bilingual variants, brand/claim/disclaimer controls, simple ROI metadata, admin diagnostics, merchant-friendly next-action guidance, and support tools for manual packages.

**Addresses:** `REQ-LOCAL-*`, `REQ-BRAND-001`, `REQ-ROI-001`, `REQ-ADMIN-*`, `REQ-FALLBACK-*`, `REQ-UX-001`.

**Avoids:** generic scheduling commodity trap, unsupported claims, opaque pilot failures, weak field-sales story.

### Phase 7: TikTok Direct Post Hardening

**Rationale:** Direct Post should be enabled only after audit/scopes, explicit consent UX, creator-info refresh, moderation/status behavior, and public/private outcomes are validated.

**Delivers:** Direct Post eligibility gates, app audit evidence, privacy/disclosure UI from live creator info, public/private status mapping, moderation-pending state, webhook/polling reconciliation, and stronger TikTok support diagnostics.

**Addresses:** conditional TikTok Direct Post, official consent, public publish lifecycle, advanced TikTok constraints.

**Avoids:** private posts mislabeled as public, unapproved `video.publish` assumptions, disclosure violations.

### Phase 8: Xiaohongshu Assisted Export and Partner Spike

**Rationale:** Xiaohongshu remains strategically valuable, but direct publishing should not block v1 and should not be promised without official/partner proof.

**Delivers:** RED-native assisted content package, title/body/cover-text/hashtag checklist, manual completion tracking, and a separate partner-access research spike covering eligibility, scopes, permitted write actions, token model, sandbox, compliance terms, and production approval.

**Addresses:** Xiaohongshu deferred strategy, compliant assisted value, future integration discovery.

**Avoids:** cookie/session automation, misleading direct-publish claims, confusing ads/analytics APIs with organic note publishing.

### Phase Ordering Rationale

- Phase 1 creates the security, data, and workflow substrate required by every later phase.
- Phase 2 should happen before deep platform implementation because Postiz may materially reduce integration work, while AutoCLI should be formally excluded from production publishing.
- Facebook precedes TikTok because Page text/link/image publishing is the clearest local merchant proof and lower media complexity than TikTok video.
- TikTok starts with Upload-to-Inbox/Draft because it aligns with official APIs and app-audit uncertainty.
- Differentiation follows the first publishing proofs so generation and ROI work stays grounded in actual platform constraints.
- Xiaohongshu stays assisted/deferred until official organic publishing access is confirmed.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Postiz self-host/API/AGPL/deployment fit, token residency, status mapping, media behavior, and Facebook/TikTok live test results.
- **Phase 3:** Authenticated Meta developer research for current 2026 permission names, app mode/review requirements, Page access token behavior, and screencast expectations.
- **Phase 5:** TikTok Upload-to-Inbox media transfer mode, verified domain/public URL requirements, creator-info UX, and status/webhook handling.
- **Phase 7:** TikTok Direct Post audit, public visibility, moderation timing, disclosure requirements, and direct-post support policy.
- **Phase 8:** Xiaohongshu official/partner access validation for organic merchant-owned note publishing.

Phases with standard patterns (skip research-phase unless implementation choices change):
- **Phase 1:** Backend CRUD, auth/session boundary, PostgreSQL migrations, job tables, fake adapter, and approval state machine are established patterns.
- **Phase 4:** Once Phase 3 validates Meta app permissions, Page text/link/image publishing can be planned from the confirmed API path and adapter decision.
- **Phase 6:** Local offer generation, CTA libraries, admin diagnostics, and manual fallback UX can be planned from product requirements and existing prototype context.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Backend/persistence/secrets need is definitive; FastAPI/Postgres is supported by symbo patterns. Exact Meta mechanics and Postiz production fit need validation. |
| Features | MEDIUM-HIGH | Table-stakes requirements converge across research. TikTok is high-confidence from official docs; Facebook requires authenticated Meta verification. |
| Architecture | HIGH | Component boundaries, token model, state machine, async jobs, adapter pattern, and localStorage rejection are clear and low-risk. |
| Pitfalls | HIGH | Major risks are consistent across platform docs, project constraints, and current prototype limitations. Meta details remain medium where official docs were login-gated. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- Meta 2026 app review and permissions: verify in an authenticated Meta developer account before committing production scope and review artifacts.
- Postiz fit: run a live sandbox against Facebook Page and TikTok test accounts before deciding API/self-host/native adapter path.
- Postiz licensing/deployment: review AGPL-3.0 and operational implications if modifying, self-hosting, or embedding.
- TikTok Direct Post: confirm audit timeline, visibility behavior, creator-info constraints, and disclosure UX before promising public direct publishing.
- Media storage domain: choose object storage/CDN setup that satisfies TikTok HTTPS/verified-domain or upload-mode requirements.
- Auth provider: decide LocalPilot merchant session/auth model before social OAuth is added.
- Xiaohongshu: require written official/partner proof for organic merchant-owned note publishing before moving beyond assisted export.
- AI generation provider and policy checks: not resolved in this research; v1 can start deterministic/prompted but should add regulated-claim and disclosure checks before live pilots.

## Sources

### Primary (HIGH confidence)

- `.planning/PROJECT.md` - LocalPilot product intent, active requirements, platform priority, constraints, and decisions.
- `.planning/research/STACK.md` - recommended stack, Facebook/TikTok/Postiz/AutoCLI/symbo findings.
- `.planning/research/FEATURES.md` - table-stakes features, differentiators, anti-features, and v1 requirement mapping.
- `.planning/research/ARCHITECTURE.md` - component boundaries, data model, lifecycle, API shape, engine options, symbo patterns.
- `.planning/research/PITFALLS.md` - critical platform/compliance/security pitfalls, phase warnings, production requirements.
- TikTok Content Posting API docs - Direct Post, Upload, Creator Info, Media Transfer, Status/Webhooks, and Content Sharing Guidelines.
- Local symbo references - FastAPI/config/middleware/router/job patterns and negative secret-handling lessons.

### Secondary (MEDIUM confidence)

- Postiz Public API, CLI, MCP, provider, and self-hosting documentation - strong candidate for reusable engine; live fit still needs spike.
- Meta developer docs attempted but login-gated - Pages API posts, App Review, and permission references need authenticated confirmation.
- Meta/Postman Facebook API collection and current Facebook Graph API posting guide - corroborating Page token/posting/review mechanics.
- Stack Overflow Page publishing permission discussion - corroborating only; not authoritative.

### Tertiary (LOW confidence)

- Xiaohongshu public commercial/open-platform surfaces - useful for ecosystem mapping, but did not prove general merchant-owned organic note publishing.
- AutoCLI README - enough to reject for production publishing due to browser-session automation; useful only for internal research/tooling ideas.

---
*Research completed: 2026-06-09*
*Ready for roadmap: yes*
