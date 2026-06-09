# Architecture Research: LocalPilot AI Publishing Foundation

**Project:** LocalPilot AI
**Researched:** 2026-06-09
**Mode:** Architecture ecosystem research
**Overall confidence:** HIGH for component boundaries and secrets model; MEDIUM for Postiz fit until a live Facebook/TikTok spike confirms account review, media, and status behavior.

## Recommendation

LocalPilot should add a real server-side publishing foundation before attempting any direct Facebook or TikTok publishing from the current React/Vite demo. The v1 architecture should keep the existing frontend as the review and approval UI, introduce a backend API with durable persistence, and isolate all social-publishing behavior behind a `PublishingEngine` boundary. That boundary should support two implementations: a Postiz-backed adapter for the first integration spike, and native platform adapters for any platform behavior Postiz cannot cover cleanly.

The default v1 path should be: **LocalPilot backend + database + job worker + Postiz/self-hosted engine adapter**, not a browser-only flow and not a CLI call directly from the web request. Postiz already exposes OAuth channel connection, integration listing, draft/schedule/now post creation, media upload, provider-specific settings, and MCP/CLI surfaces. Its documented architecture also separates frontend, backend, orchestrator, SQL, Redis, Temporal, and storage, which is exactly the shape LocalPilot would otherwise need to recreate for scheduling, retries, token refresh, and post status.

AutoCLI should not be the production publishing engine. It is useful as a research or operator tool because it can reuse browser sessions and run browser-backed commands for many sites, including some publish-like commands. That same browser-session/cookie model is the wrong boundary for merchant-owned official publishing: it is difficult to audit, fragile under platform UI changes, and conflicts with the project constraint to use official API paths rather than scraping or browser automation.

## Recommended V1 Component Boundaries

```text
React/Vite App
  -> LocalPilot API
      -> Auth and Merchant Workspace
      -> Campaign/Draft Service
      -> Approval Service
      -> Publishing Service
      -> Publishing Job Worker
      -> Publishing Engine Adapter
          -> Postiz API or self-hosted Postiz
          -> Native Meta/TikTok adapters when needed
      -> Database
      -> Object Storage/CDN
      -> Secrets/Token Store
```

| Component | Responsibility | Owns | Must Not Own |
|-----------|----------------|------|--------------|
| React app | Merchant input, draft review, edit/regenerate controls, connect buttons, approval actions, status display. | UI state, optimistic loading state, non-secret form values. | OAuth secrets, access/refresh tokens, API keys, final source of truth for publishing state. |
| LocalPilot API | Authenticated product API for merchants, campaigns, drafts, approvals, account connections, and status reads. | Request validation, tenant checks, business rules, audit events. | Platform-specific HTTP details in controllers. |
| Campaign/Draft service | Convert one merchant offer into platform-native drafts. | Prompt inputs, generated copy, media references, draft versions. | Publishing side effects. |
| Approval service | Enforce explicit owner approval before publishing. | Approval state, approver, approved version hash, audit trail. | Token refresh or platform calls. |
| Publishing service | Convert approved drafts into engine-specific jobs. | Idempotency keys, job records, lifecycle state, retry policy. | Long-running synchronous publish calls inside HTTP request handlers. |
| Publishing worker | Execute publish jobs and poll status. | Background retries, platform result normalization, failure classification. | Merchant-facing route rendering. |
| Publishing engine adapter | Stable internal port over Postiz/native adapters. | `connectChannel`, `listChannels`, `validateDraft`, `publishNow`, `createDraft`, `getStatus`. | LocalPilot business logic. |
| Database | Durable product state. | Merchants, users, connected channels metadata, campaigns, drafts, approvals, publish jobs, publish attempts, results. | Raw unencrypted secrets. |
| Object storage/CDN | Media assets for Facebook/TikTok upload. | Images/videos and signed/public delivery paths. | OAuth tokens. |
| Secrets/token store | Encrypted tokens and app credentials. | Refresh tokens, access tokens, Postiz API/OAuth tokens, Meta/TikTok app secrets. | Browser-readable values. |

## Canonical Data Model

Use these as logical records even if the implementation starts with fewer columns.

| Entity | Key Fields | Notes |
|--------|------------|-------|
| `Merchant` | `id`, `business_name`, `timezone`, `locale`, `created_at` | Tenant boundary for all records. |
| `User` | `id`, `merchant_id`, `email`, `role` | Needed for approval/audit attribution. |
| `ConnectedChannel` | `id`, `merchant_id`, `platform`, `external_account_id`, `display_name`, `status`, `engine`, `engine_integration_id`, `token_ref` | Store token references, not token values. |
| `Campaign` | `id`, `merchant_id`, `source_input`, `goal`, `status` | Source of generated drafts. |
| `DraftPost` | `id`, `campaign_id`, `platform`, `content`, `media_asset_ids`, `settings`, `version`, `status` | Platform-specific fields live in `settings`. |
| `Approval` | `id`, `draft_post_id`, `version`, `approved_by`, `approved_at`, `decision`, `note` | Publishing must require `decision=approved` for the current version. |
| `PublishJob` | `id`, `draft_post_id`, `channel_id`, `state`, `idempotency_key`, `scheduled_for`, `engine` | State machine source of truth. |
| `PublishAttempt` | `id`, `job_id`, `attempt_no`, `request_digest`, `engine_request_id`, `external_post_id`, `status`, `error_code`, `error_message`, `raw_result_ref` | Keep raw payloads redacted or stored behind restricted access. |
| `MediaAsset` | `id`, `merchant_id`, `kind`, `storage_url`, `public_url`, `mime_type`, `size_bytes`, `duration_ms` | TikTok and Postiz require HTTPS-reachable media for URL-based flows. |

## Publishing Lifecycle

Use a product-level state machine that does not leak platform-specific states into the UI.

```text
draft
  -> needs_review
  -> approved
  -> queued
  -> publishing
  -> published

failure branches:
  publishing -> retry_needed
  publishing -> failed
  queued/publishing -> cancelled

editing branch:
  needs_review/approved -> draft
```

Rules:

- Approval is tied to a draft version. Editing approved content invalidates the approval and returns the draft to `needs_review`.
- Publishing jobs are idempotent by `(draft_post_id, channel_id, approved_version)`.
- A job may have many attempts; the job state is the user-facing aggregate.
- Platform result fields should normalize to `external_post_id`, `external_url`, `engine_request_id`, `published_at`, `error_code`, `error_message`, and `retryable`.

## Data Flow

```text
Merchant input
  -> LocalPilot API stores Campaign
  -> Draft service generates Facebook/TikTok DraftPost records
  -> React review UI loads drafts from API
  -> Merchant edits or regenerates
  -> Merchant approves a specific draft version
  -> Publishing service creates PublishJob
  -> Worker validates channel + media + settings
  -> PublishingEngine adapter calls Postiz API or native platform API
  -> Worker persists PublishAttempt and normalized result
  -> React polls/subscribes to job status
  -> Merchant sees published/failed/retry-needed result
```

Detailed flow:

1. Merchant enters an offer, service, promotion, audience, goal, and optional media in the React app.
2. React sends the input to `POST /api/campaigns`; the API validates lengths, tenant, and basic content safety, then stores the campaign.
3. `Campaign/Draft service` creates platform-native `DraftPost` rows for Facebook and TikTok. For v1 this can start deterministic, then later call an AI provider.
4. React displays stored drafts, not localStorage-only objects. User edits call `PATCH /api/drafts/{id}` and create a new version.
5. User approves with `POST /api/drafts/{id}/approve`; the API records who approved which version.
6. User publishes with `POST /api/drafts/{id}/publish`. The API verifies the draft is approved, the connected channel belongs to the merchant, required media/settings exist, and then creates a `PublishJob`.
7. The worker picks up the job. It uploads media if needed, maps the draft to engine schema, and calls either Postiz or a native adapter.
8. The worker stores `PublishAttempt` with redacted request/result metadata and moves the job to `published`, `failed`, or `retry_needed`.
9. React reads `GET /api/publish-jobs/{id}` or `GET /api/campaigns/{id}/status` to display result, error, retry action, and external post URL if available.

## Token and Secrets Boundary

Browser `localStorage` is insufficient for real publishing because it is readable by any JavaScript running in the page, persists beyond logout unless explicitly cleared, has no server-side revocation, is vulnerable to XSS token exfiltration, and cannot safely perform refresh-token rotation or platform secret exchange. The current code stores demo sessions, campaign inputs, generated plans, pilot request data, and export packages under `localpilot-*` keys in `src/main.jsx`; that is acceptable for a prototype but must not become the security model for OAuth.

Production rules:

- OAuth client secrets, Postiz API keys, Meta app secrets, TikTok client secrets, access tokens, and refresh tokens live only server-side.
- The browser receives only session cookies or short-lived opaque session tokens, never platform tokens.
- Use `HttpOnly`, `Secure`, `SameSite=Lax` or stricter cookies for LocalPilot auth.
- Store platform tokens encrypted at rest with a token reference on `ConnectedChannel`.
- Redact tokens from logs, job payloads, error messages, browser responses, and support exports.
- Token refresh belongs in the backend worker or publishing engine, not in React.
- Merchant account connection should start from the backend, which creates an OAuth authorization URL and validates callback state/PKCE before storing tokens.

The symbo reference reinforces both sides of this boundary. `apps/event_service/main.py` uses FastAPI dependencies to validate API keys/basic auth and maps credentials to retailer IDs before ingesting data. That pattern is useful. `apps/conversion_uploader/conversion_service.py` contains a hard-coded Facebook access token; that is the negative pattern LocalPilot must explicitly avoid.

## Publishing Engine Options

### Option A: Wrap Postiz Public API or Self-Hosted Postiz

**Recommendation:** Use this as the first implementation spike and likely v1 engine if Facebook/TikTok behavior passes acceptance tests.

What it provides:

- OAuth channel connection via `/public/v1/social/{integration}`.
- Integration listing with provider identifiers including `facebook` and `tiktok`.
- Post creation with `type` values for `draft`, `schedule`, and `now`.
- Provider-specific schemas: Facebook page posts need `__type: "facebook"` with optional URL; TikTok requires privacy, duet, stitch, comments, brand toggles, AI disclosure, and `content_posting_method`.
- Media upload APIs and a documented architecture with backend, orchestrator, SQL database, Redis, Temporal, and storage.

Pros:

- Avoids rebuilding every provider's OAuth, media, schema, schedule, token-refresh, retry, and status machinery.
- Lets LocalPilot focus on merchant onboarding, local campaign generation, approval UX, and ROI loop.
- Supports both cloud and self-hosted base URLs, which keeps a migration path.
- MCP and CLI are useful admin/agent surfaces once the core API integration is proven.

Cons:

- Adds another product/runtime to operate if self-hosted.
- Public API rate limits and feature coverage need real validation under LocalPilot's publish cadence.
- LocalPilot must still maintain its own approval state and tenant model; Postiz should not become the product database.
- Mapping statuses and errors may require adapter glue, especially for partial platform failures or missing release IDs.

V1 posture:

- Build the LocalPilot `PublishingEngine` interface first.
- Implement `PostizPublishingEngine` using HTTP API, not shelling out to the CLI in web requests.
- Run a focused spike: connect one Facebook Page, create a Facebook draft and now-post, connect TikTok, test `UPLOAD` and `DIRECT_POST`, verify media hosting and status/result mapping.
- Prefer self-hosted Postiz if LocalPilot needs direct control of token residency, logs, uptime, and merchant data boundaries. Postiz Cloud can be used for a development spike if credentials and test data are non-sensitive.

### Option B: Wrap Postiz CLI

**Recommendation:** Use only for local development, internal scripts, or emergency admin tooling.

Pros:

- Fastest to try from a developer machine.
- The CLI wraps the same public API and can manage integrations, upload media, and create posts.

Cons:

- Web servers invoking shell commands create quoting, environment, timeout, process, concurrency, and credential-file risks.
- CLI credentials are stored in user-level files such as `~/.postiz/credentials.json`, which does not map cleanly to multi-merchant SaaS tenancy.
- It is harder to guarantee idempotency and structured error handling than with direct HTTP calls.

V1 posture:

- Do not put CLI execution in the production request path.
- If kept, wrap it behind the same `PublishingEngine` contract as a dev-only adapter.

### Option C: Use Postiz MCP

**Recommendation:** Do not use MCP as the primary runtime publish path. Use it later for operator/agent workflows.

Pros:

- Exposes useful tools such as listing integrations, reading platform schemas, and scheduling/drafting/publishing posts through a standardized tool interface.
- Helpful for internal AI-assisted operations and debugging.

Cons:

- MCP is a tool-calling interface for agents, not the simplest deterministic backend integration for a product workflow.
- User-facing publishing needs explicit approval, durable idempotency, structured retries, and predictable API responses.

V1 posture:

- Keep MCP out of the merchant production path.
- Revisit after the backend state machine exists.

### Option D: Custom Native Meta and TikTok Adapters

**Recommendation:** Keep as fallback and long-term escape hatch; implement Facebook native first only if Postiz fails the spike.

Pros:

- Maximum control over UX, errors, retries, media handling, app review, and token storage.
- No dependency on a third-party engine's feature lag or data model.

Cons:

- Requires rebuilding platform-specific OAuth, token exchange, permissions, media upload, status polling, rate-limit handling, error taxonomy, app-review workflows, and version upgrades.
- TikTok has non-trivial Direct Post requirements: creator info/privacy choices, public HTTPS media, upload URL expiry, Direct Post audit/private-account restrictions, scopes, and status polling.
- Meta Page publishing requires correct Page access tokens and app mode/review/permissions; media and Reels have multi-step upload/status flows.

V1 posture:

- Define native adapter interfaces now, but avoid implementing both platforms from scratch until the Postiz spike produces evidence that reuse is insufficient.

### Option E: AutoCLI

**Recommendation:** Reject for production publishing; allow only research/prototyping.

Pros:

- Broad command/adaptor ecosystem and single-binary operation.
- Useful for gathering public social context and testing browser-session automation ideas.

Cons:

- Browser-session reuse and UI/cookie automation are fragile and less compliant than official OAuth/API publishing.
- It does not provide the product-grade merchant token boundary, approval ledger, durable publish jobs, and platform status model LocalPilot needs.
- The project explicitly rules out scraping, reverse engineering, and cookie-based posting for production.

## Facebook Architecture Notes

Facebook v1 should mean Page publishing, not personal profile publishing. The integration should store a connected `facebook` channel per Page, not just per user. The backend must handle app review/app mode and permissions as deployment prerequisites before field-sales customers rely on it.

Minimum v1 fields:

- `page_id`
- `page_name`
- `page_access_token_ref`
- `permissions_granted`
- `tasks` or capability metadata if available
- `engine_integration_id`
- `connection_status`

If Postiz is used, LocalPilot should still model Facebook settings internally as:

```json
{
  "__type": "facebook",
  "url": "https://optional-localpilot-or-merchant-link"
}
```

If native Meta publishing is needed, implement separate methods for text/link, photo, video, and Reels rather than a single generic `publishFacebookPost` function. Meta media flows and status checks differ enough that a generic call will become hard to debug.

## TikTok Architecture Notes

TikTok v1 should support both:

- `UPLOAD`: send media to TikTok for manual posting or draft-like merchant completion where Direct Post is blocked.
- `DIRECT_POST`: publish directly only when the merchant's connected account, app audit state, privacy choice, media, and scopes satisfy TikTok requirements.

Minimum v1 fields:

- `open_id` or engine account identifier
- `display_name`
- `privacy_level_options`
- `direct_post_allowed`
- `content_posting_method`
- `engine_integration_id`
- `connection_status`

TikTok media must be treated as a first-class architecture concern. For URL-pull flows, media must be public over HTTPS from a verified/allowed domain. For file upload flows, the worker must respect upload URL expiry and chunk metadata. The UI should surface privacy options from creator info rather than hard-coding only `PUBLIC_TO_EVERYONE`.

If Postiz is used, LocalPilot should map TikTok drafts into:

```json
{
  "__type": "tiktok",
  "title": "Short local-business title",
  "privacy_level": "SELF_ONLY",
  "duet": false,
  "stitch": false,
  "comment": true,
  "autoAddMusic": "no",
  "brand_content_toggle": false,
  "brand_organic_toggle": false,
  "video_made_with_ai": false,
  "content_posting_method": "UPLOAD"
}
```

Default TikTok v1 to `UPLOAD`/private-safe settings until Direct Post audit and public posting behavior are verified.

## Patterns Borrowed From symbo

| symbo Path | Pattern to Borrow | LocalPilot Application |
|------------|-------------------|------------------------|
| `/Users/huijie/Documents/symbo/apps/api/external-api-template.yaml` | Explicit API gateway contract, versioned paths, API key security definitions, backend address as deployment substitution. | Define `/api/v1` OpenAPI routes for campaigns, drafts, approvals, connected channels, and publish jobs before frontend wiring gets too large. |
| `/Users/huijie/Documents/symbo/apps/event_service/main.py` | FastAPI app with Pydantic request models, auth dependencies, tenant/retailer resolution, and endpoint-specific validation. | Put tenant resolution and validation in API dependencies/middleware, not in React. Use typed request/response models for publish actions. |
| `/Users/huijie/Documents/symbo/apps/event_service/main.py` | Startup refresh loop for credentials and background async work. | Use a worker/loop for token refresh and job processing rather than synchronous frontend-triggered publishing. |
| `/Users/huijie/Documents/symbo/apps/event_service/main.py` | Asynchronous write pattern with `safe_bq_insert`, retry count, structured logging, and sample-row diagnostics. | Persist publish attempts/results asynchronously with redacted diagnostics and retryable/non-retryable classification. |
| `/Users/huijie/Documents/symbo/apps/event_service/README.md` | Clear data-flow documentation from API requests to raw tables, merged analytics, staging, and downstream consumers. | Document LocalPilot's flow from input to drafts to approvals to publish attempts to ROI/analytics so future reporting does not couple directly to the UI. |
| `/Users/huijie/Documents/symbo/apps/conversion_uploader/conversion_service.py` | CLI entrypoint with platform dispatch, platform SDK calls, partial failure handling, and upload history. | For platform adapters, normalize partial failures and record attempt history. Keep CLI as an internal batch/admin pattern only. |
| `/Users/huijie/Documents/symbo/apps/conversion_uploader/conversion_service.py` | Hard-coded Facebook access token. | Negative pattern: never commit or embed platform tokens; use server-side secret storage and redacted logs. |

## API Shape

Recommended initial endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/campaigns` | Create campaign from merchant input and generate initial drafts. |
| `GET /api/v1/campaigns/{id}` | Fetch campaign with drafts and publish summary. |
| `PATCH /api/v1/drafts/{id}` | Edit draft content/settings and create a new draft version. |
| `POST /api/v1/drafts/{id}/regenerate` | Generate a new version with merchant instructions. |
| `POST /api/v1/drafts/{id}/approve` | Approve the current version. |
| `POST /api/v1/drafts/{id}/publish` | Create publish job after approval check. |
| `GET /api/v1/publish-jobs/{id}` | Read normalized job status/result. |
| `POST /api/v1/channels/{platform}/connect` | Create OAuth URL or start engine connection. |
| `GET /api/v1/channels` | List connected merchant channels. |
| `POST /api/v1/media` | Upload media and create a `MediaAsset`. |

## Build Order Implications

1. **Extract frontend storage assumptions.** Keep the current demo UI, but introduce API-shaped service functions and stop treating localStorage plans as the source of truth for publishing-related state.
2. **Add backend skeleton and database.** Create merchants, users, campaigns, draft posts, approvals, connected channels, publish jobs, attempts, and media assets. Add auth/session before OAuth.
3. **Implement approval-version state machine.** This prevents accidental publish of edited/unapproved copy and becomes the core trust feature for local merchants.
4. **Implement `PublishingEngine` interface with a fake adapter.** The frontend can exercise queued/publishing/published/failed states before real platform credentials are ready.
5. **Spike Postiz via HTTP API.** Validate connect/list integrations, upload media, Facebook Page text/media, TikTok upload/direct settings, result IDs, failures, and rate limits.
6. **Decide engine posture.** If Postiz passes, run self-hosted or controlled Postiz behind `PostizPublishingEngine`; if it fails, keep the interface and implement native Meta first.
7. **Ship Facebook Page publishing first.** It is the lower-risk local merchant proof point and validates account connection, approval, job processing, and result display.
8. **Ship TikTok second with upload/private-safe defaults.** Direct Post/public visibility should wait until audit, HTTPS media, and privacy options are verified.
9. **Add observability and support tooling.** Publish attempts, redacted platform errors, retry controls, and merchant-visible failure messages are not optional for field sales.

## Architecture Anti-Patterns To Avoid

- Calling Meta or TikTok APIs directly from React.
- Storing OAuth tokens, refresh tokens, Postiz API keys, or platform app secrets in browser localStorage.
- Publishing from the same HTTP request that records user approval.
- Treating Postiz as the only product database instead of an engine behind LocalPilot's own campaign and approval model.
- Using CLI subprocesses as the production publishing path.
- Using AutoCLI/browser sessions for merchant-owned official publishing.
- Hard-coding platform privacy options instead of reading or validating allowed choices.
- Logging raw platform tokens, OAuth callback payloads, upload URLs, or customer content without redaction.

## Sources

- LocalPilot project context: `/Users/huijie/DMA/.planning/PROJECT.md`
- LocalPilot codebase map: `/Users/huijie/DMA/.planning/codebase/ARCHITECTURE.md`
- LocalPilot structure and concerns: `/Users/huijie/DMA/.planning/codebase/STRUCTURE.md`, `/Users/huijie/DMA/.planning/codebase/CONCERNS.md`
- symbo API contract: `/Users/huijie/Documents/symbo/apps/api/external-api-template.yaml`
- symbo event service: `/Users/huijie/Documents/symbo/apps/event_service/README.md`, `/Users/huijie/Documents/symbo/apps/event_service/main.py`
- symbo conversion uploader: `/Users/huijie/Documents/symbo/apps/conversion_uploader/conversion_service.py`
- Postiz CLI introduction: https://docs.postiz.com/cli/introduction
- Postiz MCP introduction: https://docs.postiz.com/mcp/introduction
- Postiz Public API create post/list integrations/connect channel/how it works/provider settings: https://docs.postiz.com/public-api/posts/create, https://docs.postiz.com/public-api/integrations/list, https://docs.postiz.com/public-api/integrations/connect, https://docs.postiz.com/howitworks, https://docs.postiz.com/public-api/providers/facebook, https://docs.postiz.com/public-api/providers/tiktok
- Postiz provider setup notes for Facebook/TikTok: https://docs.postiz.com/providers/facebook, https://docs.postiz.com/providers/tiktok
- AutoCLI repository: https://github.com/nashsu/AutoCLI
- TikTok Direct Post API reference: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Meta/Postman Facebook API collection for Page tokens and Reels upload/status flow: https://www.postman.com/meta/facebook/documentation/r56bjfd/facebook-api

## Confidence and Gaps

| Area | Confidence | Notes |
|------|------------|-------|
| Component boundaries | HIGH | Current frontend-only limitations and standard publishing workflow needs are clear. |
| Secrets boundary | HIGH | Browser localStorage is categorically unsuitable for platform tokens and refresh secrets. |
| Postiz as engine | MEDIUM | Docs show strong fit, but live tests must verify Facebook/TikTok account review, media, status, and error mapping. |
| AutoCLI rejection for production | HIGH | Its browser-session automation model conflicts with official API/compliance requirements. |
| Native Meta/TikTok details | MEDIUM | Official TikTok docs were checked; Meta docs were partially gated, so Page token/media notes are supported by Meta's Postman collection and Postiz provider docs. |

Open questions for the next phase:

- Will LocalPilot self-host Postiz or use Postiz Cloud for the first field pilot?
- Which backend stack should be introduced in this repo: Node/TypeScript to match Vite, or FastAPI/Python to mirror symbo operating patterns?
- What auth provider will own LocalPilot merchant sessions before social OAuth is added?
- What object storage/CDN domain will satisfy TikTok HTTPS/public media requirements?
- What is the minimum TikTok UX before audit: upload-to-draft only, private Direct Post, or both?
