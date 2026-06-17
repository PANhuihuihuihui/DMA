# Phase 02: Publishing Engine Reuse Decision - Research

**Researched:** 2026-06-10  
**Domain:** Postiz-style publishing engine reuse for Facebook and TikTok merchant publishing  
**Confidence:** MEDIUM

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENGINE-01 | Team can run a focused spike comparing Postiz-style self-hosted/API/MCP publishing reuse against native provider adapters. | Postiz exposes Public API, CLI, MCP, and self-hosted auth surfaces, so the spike can exercise an adapter boundary instead of only a UI flow [CITED: https://docs.postiz.com/introduction] [CITED: https://docs.postiz.com/cli/introduction] [CITED: https://docs.postiz.com/cli/authentication]. |
| ENGINE-02 | System defines a `PublishingProvider` contract that can wrap Postiz-style APIs, native Meta adapters, native TikTok adapters, or the fake adapter without changing product workflow records. | Postiz already separates integrations from posts at the API level (`/integrations`, `/social/{integration}`, `/posts`) and uses provider-specific `__type` schemas, which makes adapter wrapping plausible but also shows the contract is not the same as LocalPilot's workflow record model [CITED: https://docs.postiz.com/public-api/integrations/list] [CITED: https://docs.postiz.com/public-api/integrations/connect] [CITED: https://docs.postiz.com/public-api/posts/create]. |
| ENGINE-03 | Spike records whether Postiz-style tooling can connect Facebook Pages, handle TikTok posting/upload flows, submit media, return status, expose errors, and meet deployment/licensing needs. | Facebook/TikTok provider docs, public API post schemas, list/status fields, self-host deployment docs, and repo license metadata cover the required evaluation surface [CITED: https://docs.postiz.com/public-api/providers/facebook] [CITED: https://docs.postiz.com/public-api/providers/tiktok] [CITED: https://docs.postiz.com/public-api/posts/list] [CITED: https://docs.postiz.com/configuration/reference] [CITED: https://github.com/gitroomhq/postiz-app]. |
| ENGINE-04 | Spike explicitly rejects AutoCLI/browser-session automation for production publishing, while allowing it only as internal research tooling if needed. | Postiz's repo README says the hosted service uses official OAuth flows and does not automate or scrape content, while TikTok and Meta docs define official API-based publishing paths with OAuth and review requirements [CITED: https://github.com/gitroomhq/postiz-app] [CITED: https://developers.facebook.com/docs/pages-api/posts/] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation] [CITED: https://developers.tiktok.com/doc/our-guidelines-developer-guidelines]. |
| ENGINE-05 | Team makes a documented go/no-go decision before building deep custom Facebook or TikTok request wrappers. | Postiz's current docs and repo shape are enough to decide whether wrapping is viable, but several gaps remain around LocalPilot-specific workflow records, redacted diagnostics, and operational fit [CITED: https://docs.postiz.com/public-api/posts/create] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts]. |
| SEC-05 | System rejects scraping, cookie-based posting, and browser-session automation for production merchant publishing. | Postiz explicitly says it does not automate or scrape content, Meta and TikTok official docs point to API/OAuth publishing flows, and TikTok's guidelines require app review, explicit consent, and audit-gated direct posting [CITED: https://github.com/gitroomhq/postiz-app] [CITED: https://developers.facebook.com/docs/pages-api/posts/] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation] [CITED: https://developers.tiktok.com/doc/content-sharing-guidelines] [CITED: https://developers.tiktok.com/doc/our-guidelines-developer-guidelines]. |
| SEC-04 | System requires explicit merchant approval before any live platform publish request is submitted. | Postiz has post-state and review-related surfaces, but no public documentation in this research proves an approval snapshot model that matches LocalPilot's Phase 01 boundary; the planner should treat this as a LocalPilot-owned requirement, not something to inherit implicitly from Postiz [CITED: https://docs.postiz.com/public-api/posts/create] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts]. |
</phase_requirements>

## Summary

Postiz is positioned as an open-source, self-hosted social media scheduling tool that helps users manage social accounts, schedule social posts/articles, generate posts with AI, and use a marketplace; its official docs expose Public API, CLI, MCP, and Developer App (OAuth2) surfaces rather than a narrow social-posting SDK [CITED: https://docs.postiz.com/introduction] [CITED: https://github.com/gitroomhq/postiz-app]. For LocalPilot, that means Postiz is a credible engine candidate, but only as an adapter-backed publishing layer, not as the source of truth for LocalPilot's backend-owned workflow records.

For Facebook and TikTok specifically, Postiz exposes `GET /integrations`, `GET /social/{integration}` for OAuth connect, `POST /posts` for create/schedule, and provider-specific `__type` settings schemas for `facebook` and `tiktok` [CITED: https://docs.postiz.com/public-api/integrations/list] [CITED: https://docs.postiz.com/public-api/integrations/connect] [CITED: https://docs.postiz.com/public-api/posts/create] [CITED: https://docs.postiz.com/public-api/providers/facebook] [CITED: https://docs.postiz.com/public-api/providers/tiktok]. The official Meta and TikTok docs also confirm the production path is official API publishing with OAuth, app review, creator-info checks, and media delivery constraints, not browser automation or cookie posting [CITED: https://developers.facebook.com/docs/pages-api/posts/] [CITED: https://developers.facebook.com/docs/pages-api/] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation] [CITED: https://developers.tiktok.com/doc/content-sharing-guidelines] [CITED: https://developers.tiktok.com/doc/our-guidelines-developer-guidelines].

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Merchant approval and publish gating | Backend/API | Frontend | LocalPilot must own the explicit approval snapshot and submission gate; Postiz docs do not prove this is a stable first-class external contract [CITED: https://docs.postiz.com/public-api/posts/create] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts]. |
| Channel connect and token exchange | Backend/API | Frontend | Postiz exposes OAuth connect endpoints and CLI/device auth, so token exchange belongs behind an adapter boundary, not in browser storage [CITED: https://docs.postiz.com/public-api/integrations/connect] [CITED: https://docs.postiz.com/cli/authentication]. |
| Facebook/TikTok payload translation | Backend/API | Worker | Provider-specific `__type` schemas and media rules must be normalized before the publish call [CITED: https://docs.postiz.com/public-api/posts/create] [CITED: https://docs.postiz.com/public-api/providers/facebook] [CITED: https://docs.postiz.com/public-api/providers/tiktok]. |
| Media hosting and public delivery URLs | Database/Storage | Backend/API | TikTok and Postiz docs both require publicly reachable HTTPS media for some flows, so storage is a separate concern from post records [CITED: https://docs.postiz.com/providers/tiktok] [CITED: https://docs.postiz.com/public-api/uploads/upload-from-url]. |
| Publish status, retries, and diagnostics | Backend/API | Worker | Postiz has `state`, `releaseId`, `releaseURL`, and `error` fields plus Temporal-backed worker retries, but LocalPilot still needs its own workflow record model and redaction policy [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts] [CITED: https://github.com/gitroomhq/postiz-app/blob/main/apps/orchestrator/src/workflows/post-workflows/post.workflow.v1.0.1.ts]. |

## Fit Assessment

| Area | Assessment | Evidence | Planner implication |
|------|------------|----------|---------------------|
| Current positioning | Good engine candidate, not product fit by itself | Postiz is explicitly a self-hosted scheduling tool with API/CLI/MCP/OAuth surfaces [CITED: https://docs.postiz.com/introduction] [CITED: https://docs.postiz.com/cli/introduction]. | Use it only behind a LocalPilot adapter, never as the product database or approval authority. |
| Facebook surface | Sufficient for a spike | Facebook provider docs expose page posting settings and OAuth channel connect [CITED: https://docs.postiz.com/public-api/providers/facebook] [CITED: https://docs.postiz.com/public-api/integrations/connect] [CITED: https://developers.facebook.com/docs/pages-api/posts/]. | Verify Page-only publishing, permissions, and any app-review friction before deeper work. |
| TikTok surface | Sufficient for a spike, but more constrained | TikTok docs require public HTTPS media, creator info, direct-post/upload modes, app review, and audit-gated visibility [CITED: https://docs.postiz.com/public-api/providers/tiktok] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation] [CITED: https://developers.tiktok.com/doc/content-sharing-guidelines]. | Treat TikTok as the stricter compliance gate and validate the exact post flow in the spike. |
| Workflow-record fit | Partial | Public docs expose posts/integrations/state/errors, but not a first-class immutable approval snapshot or attempt-history contract [CITED: https://docs.postiz.com/public-api/posts/list] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts]. | Keep LocalPilot's backend-owned workflow records and map Postiz into them through `PublishingProvider`. |
| Retry/attempt fit | Partial | Postiz's workflow code uses Temporal retries, and repository code persists state/error fields, but the public API does not expose attempt rows as a stable contract [CITED: https://github.com/gitroomhq/postiz-app/blob/main/apps/orchestrator/src/workflows/post-workflows/post.workflow.v1.0.1.ts] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts]. | LocalPilot should keep its own attempt ledger and idempotency behavior. |
| Diagnostics fit | Weak | I found serialized error persistence in the repository, but no public redacted-diagnostics contract in the docs [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts]. | Do not assume Postiz can replace LocalPilot's redacted support surface. |
| Licensing/deployment fit | Mixed | The repo is AGPL-3.0, self-hosting is recommended via Docker Compose, and Postiz's runtime stack includes PostgreSQL, Redis, and Temporal services [CITED: https://github.com/gitroomhq/postiz-app] [CITED: https://docs.postiz.com/quickstart] [CITED: https://docs.postiz.com/installation/development]. | Validate AGPL obligations and ops cost before adopting it as a reused engine. |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Channel connection and OAuth token handling | Browser-session or cookie-based publishing flow | Official Meta/TikTok APIs or a self-hosted Postiz adapter layer | The official docs define API/OAuth publishing, and Postiz explicitly says it does not automate or scrape content [CITED: https://developers.facebook.com/docs/pages-api/posts/] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation] [CITED: https://github.com/gitroomhq/postiz-app]. |
| TikTok media delivery | Local/private upload paths | Public HTTPS object storage or a storage-backed upload flow | TikTok and Postiz both require publicly reachable media for some publishing flows [CITED: https://docs.postiz.com/providers/tiktok] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation]. |
| Retry and status bookkeeping | Ad hoc publish retries in request handlers | Backend-owned workflow records with idempotency and worker retries | Postiz internally uses Temporal retries, but LocalPilot must preserve its own publish record semantics [CITED: https://github.com/gitroomhq/postiz-app/blob/main/apps/orchestrator/src/workflows/post-workflows/post.workflow.v1.0.1.ts]. |

## Common Pitfalls

### Pitfall 1: Treating Postiz as the product database
**What goes wrong:** LocalPilot would lose its backend-owned approval snapshot, attempt ledger, and redacted diagnostics boundary.  
**Why it happens:** Postiz's public surfaces are post and integration oriented, not LocalPilot workflow oriented [CITED: https://docs.postiz.com/public-api/posts/list] [CITED: https://docs.postiz.com/public-api/integrations/list].  
**How to avoid:** Keep Postiz behind `PublishingProvider` and keep LocalPilot workflow records in LocalPilot.  
**Warning signs:** Planning tasks start reading or mutating Postiz internals instead of LocalPilot records.

### Pitfall 2: Assuming Postiz exposes immutable approval snapshots
**What goes wrong:** The planner may skip a required LocalPilot approval gate and later discover the engine only gives stateful posts.  
**Why it happens:** The docs expose drafts, schedules, and state transitions, but not a documented immutable approval snapshot contract [CITED: https://docs.postiz.com/public-api/posts/create] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts].  
**How to avoid:** Validate snapshot semantics directly in the planner and keep the snapshot in LocalPilot.  
**Warning signs:** Reuse plans talk about "posting directly" without naming the approved payload version.

### Pitfall 3: Using private/local media URLs for TikTok
**What goes wrong:** Upload or publish requests fail even when content exists locally.  
**Why it happens:** TikTok requires publicly reachable HTTPS media for the supported posting flows [CITED: https://docs.postiz.com/providers/tiktok] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation].  
**How to avoid:** Put media behind public object storage or a verified public URL flow.  
**Warning signs:** Planner tasks reference `/uploads`, localhost, or other private paths for TikTok publishing.

### Pitfall 4: Letting retry bugs become double-post bugs
**What goes wrong:** A post can be sent more than once if the worker fails after the external API call.  
**Why it happens:** The Postiz repo already contains retry-related workflow code and issue history around repeated publishing and status handling [CITED: https://github.com/gitroomhq/postiz-app/blob/main/apps/orchestrator/src/workflows/post-workflows/post.workflow.v1.0.1.ts] [CITED: https://github.com/gitroomhq/postiz-app/issues/1321] [CITED: https://github.com/gitroomhq/postiz-app/issues/1213].  
**How to avoid:** Keep idempotency and terminal-state handling in LocalPilot's backend records.  
**Warning signs:** Any plan that retries publish after a successful external call without a dedupe key.

## Recommended Decision Criteria

1. Prefer Postiz reuse only if the spike proves it can connect Facebook Pages, handle TikTok posting or upload flows, return usable status, and stay compatible with LocalPilot's backend-owned workflow records [CITED: https://docs.postiz.com/public-api/providers/facebook] [CITED: https://docs.postiz.com/public-api/providers/tiktok] [CITED: https://docs.postiz.com/public-api/posts/list].
2. Reject Postiz as the primary source of truth if it cannot preserve LocalPilot's approval snapshot, attempt ledger, and redacted diagnostics boundary without schema contortions [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts].
3. Reject any production path that depends on scraping, cookie posting, or browser-session automation; keep those only as internal research tools if needed [CITED: https://github.com/gitroomhq/postiz-app] [CITED: https://developers.tiktok.com/doc/our-guidelines-developer-guidelines].
4. Treat AGPL-3.0 and the self-host stack as first-order adoption criteria, not afterthoughts, because they affect deployment and support boundaries [CITED: https://github.com/gitroomhq/postiz-app] [CITED: https://docs.postiz.com/quickstart] [CITED: https://docs.postiz.com/installation/development].
5. Validate the exact terms `PublishingProvider`, `approval snapshot`, `attempt`, `retry`, `releaseId`, `releaseURL`, `DIRECT_POST`, and `UPLOAD` directly in the planner spike before assuming a one-to-one mapping to LocalPilot's records [CITED: https://docs.postiz.com/public-api/posts/create] [CITED: https://docs.postiz.com/public-api/providers/tiktok] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts].

## Open Questions

1. Does the spike need Postiz Cloud, self-hosted Postiz, or both? The docs support all three surfaces, but token residency and ops cost differ materially [CITED: https://docs.postiz.com/introduction] [CITED: https://docs.postiz.com/cli/authentication] [CITED: https://docs.postiz.com/quickstart].
2. Can LocalPilot map its approval snapshot to Postiz's `draft`/`schedule`/`QUEUE`/`PUBLISHED` state model without losing the approved payload version? [CITED: https://docs.postiz.com/public-api/posts/create] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts].
3. Do we need TikTok `DIRECT_POST` only, or do we need `UPLOAD`/draft-to-inbox behavior as a fallback path? The Postiz docs expose both, but LocalPilot must decide which merchant promise it is making [CITED: https://docs.postiz.com/public-api/providers/tiktok].
4. Does the planner want to treat Postiz's CLI and MCP surfaces as developer-only spike tooling, or as a runtime integration path? The docs present them as first-class surfaces, but the LocalPilot boundary should stay API-backed [CITED: https://docs.postiz.com/cli/introduction] [CITED: https://docs.postiz.com/introduction].

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| None | None. I kept the findings tied to official docs or repository metadata, and the remaining recommendations are explicit planner judgments rather than hidden assumptions. | N/A | N/A |

## Sources

### Primary
- Postiz docs home and introduction: [https://docs.postiz.com/introduction](https://docs.postiz.com/introduction)
- Postiz Public API intro, integrations, posts, and provider docs: [https://docs.postiz.com/public-api/introduction](https://docs.postiz.com/public-api/introduction), [https://docs.postiz.com/public-api/integrations/list](https://docs.postiz.com/public-api/integrations/list), [https://docs.postiz.com/public-api/integrations/connect](https://docs.postiz.com/public-api/integrations/connect), [https://docs.postiz.com/public-api/posts/create](https://docs.postiz.com/public-api/posts/create), [https://docs.postiz.com/public-api/posts/list](https://docs.postiz.com/public-api/posts/list), [https://docs.postiz.com/public-api/providers/facebook](https://docs.postiz.com/public-api/providers/facebook), [https://docs.postiz.com/public-api/providers/tiktok](https://docs.postiz.com/public-api/providers/tiktok)
- Postiz CLI and auth docs: [https://docs.postiz.com/cli/introduction](https://docs.postiz.com/cli/introduction), [https://docs.postiz.com/cli/authentication](https://docs.postiz.com/cli/authentication)
- Postiz installation/config docs: [https://docs.postiz.com/quickstart](https://docs.postiz.com/quickstart), [https://docs.postiz.com/installation/development](https://docs.postiz.com/installation/development), [https://docs.postiz.com/configuration/reference](https://docs.postiz.com/configuration/reference)
- Postiz media upload docs: [https://docs.postiz.com/public-api/uploads/upload-from-url](https://docs.postiz.com/public-api/uploads/upload-from-url)
- Postiz repo metadata/README/license: [https://github.com/gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app)
- Postiz workflow/repository code: [https://github.com/gitroomhq/postiz-app/blob/main/apps/orchestrator/src/workflows/post-workflows/post.workflow.v1.0.1.ts](https://github.com/gitroomhq/postiz-app/blob/main/apps/orchestrator/src/workflows/post-workflows/post.workflow.v1.0.1.ts), [https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts](https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts)
- Postiz issue history on retries and workflow termination: [https://github.com/gitroomhq/postiz-app/issues/1321](https://github.com/gitroomhq/postiz-app/issues/1321), [https://github.com/gitroomhq/postiz-app/issues/1213](https://github.com/gitroomhq/postiz-app/issues/1213)
- Meta Pages API docs: [https://developers.facebook.com/docs/pages-api/](https://developers.facebook.com/docs/pages-api/), [https://developers.facebook.com/docs/pages-api/posts/](https://developers.facebook.com/docs/pages-api/posts/)
- TikTok developer docs: [https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation](https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation), [https://developers.tiktok.com/doc/content-sharing-guidelines](https://developers.tiktok.com/doc/content-sharing-guidelines), [https://developers.tiktok.com/doc/our-guidelines-developer-guidelines](https://developers.tiktok.com/doc/our-guidelines-developer-guidelines)

## Key Findings

- Postiz is a self-hostable, AGPL-3.0 social scheduler with Public API, CLI, MCP, and OAuth2 entry points, so it is a plausible reuse layer but not a LocalPilot domain model replacement [CITED: https://github.com/gitroomhq/postiz-app] [CITED: https://docs.postiz.com/introduction].
- Facebook and TikTok are exposed through provider-specific docs and public API settings schemas, with TikTok requiring public HTTPS media, explicit creator-info flow, and audit-gated direct posting [CITED: https://docs.postiz.com/public-api/providers/facebook] [CITED: https://docs.postiz.com/public-api/providers/tiktok] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation].
- The public API exposes posts/integrations/state/error fields, but I found no official evidence of a LocalPilot-style immutable approval snapshot or first-class attempt ledger [CITED: https://docs.postiz.com/public-api/posts/list] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts].
- Postiz's own repo and docs still point to a substantial self-host stack (Docker Compose, PostgreSQL, Redis, Temporal, public HTTPS media), so deployment fit is not trivial [CITED: https://docs.postiz.com/quickstart] [CITED: https://docs.postiz.com/installation/development] [CITED: https://docs.postiz.com/providers/tiktok].
- The strongest evidence for rejecting production scraping/browser-session automation is Postiz's own README plus the official Meta/TikTok API docs, which all point to OAuth/API-based publishing rather than browser automation [CITED: https://github.com/gitroomhq/postiz-app] [CITED: https://developers.facebook.com/docs/pages-api/posts/] [CITED: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post?enter_method=left_navigation].

## Fit Assessment

**Go if:** the spike proves Postiz can be wrapped behind `PublishingProvider`, returns enough status/error data for LocalPilot support, and does not force LocalPilot to surrender its backend-owned workflow records [CITED: https://docs.postiz.com/public-api/posts/list] [CITED: https://github.com/gitroomhq/postiz-app/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts].  
**No-go if:** the spike shows that approval snapshots, attempts, retries, or redacted diagnostics would need to live inside Postiz rather than LocalPilot, or if the licensing/deployment cost outweighs the adapter benefit [CITED: https://github.com/gitroomhq/postiz-app] [CITED: https://docs.postiz.com/quickstart] [CITED: https://docs.postiz.com/installation/development].
