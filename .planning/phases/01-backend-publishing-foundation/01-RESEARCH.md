# Phase 01: Backend Publishing Foundation - Research

**Researched:** 2026-06-10
**Confidence:** HIGH for Phase 1 architecture and contract shape; MEDIUM for exact backend framework choice because the planner may still choose implementation details.

## Planning-Relevant Findings

- Phase 1 must create backend-owned publishing records before any live Facebook, TikTok, OAuth, or provider-specific integration work. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md] [VERIFIED: .planning/ROADMAP.md]
- The requirements mapped to Phase 1 are `FOUND-01` through `FOUND-06`, `SEC-01` through `SEC-04`, `SEC-06`, `APPR-04` through `APPR-06`, `STATUS-01`, and `STATUS-02`. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/ROADMAP.md]
- Current app state is frontend-only: `src/main.jsx` owns routing, demo data builders, approval handlers, localStorage persistence, and the `/` and `/app` routes. [VERIFIED: src/main.jsx] [VERIFIED: .planning/codebase/ARCHITECTURE.md]
- Publish-critical browser state today includes `localpilot-demo-input`, `localpilot-demo-plans`, approval status updates, and `localpilot-export-package`; Phase 1 should move these behind backend APIs. [VERIFIED: src/main.jsx]
- Low-risk UI preferences can remain localStorage-backed for now: language, active module, selected module, selected post/channel/indexes. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md] [VERIFIED: src/main.jsx]
- Prior project research recommends a backend API, durable database, async job/attempt model, server-side secrets boundary, and fake adapter before real provider credentials. [VERIFIED: .planning/research/SUMMARY.md] [VERIFIED: .planning/research/ARCHITECTURE.md]

## Recommended Implementation Shape

- Add a backend boundary deliberately instead of extending the frontend-only prototype. The prior stack research recommends FastAPI, PostgreSQL, SQLAlchemy/Alembic, server-side auth/session handling, and async publishing jobs as the long-term direction. [VERIFIED: .planning/research/STACK.md]
- Implement Phase 1 as a local/demo-capable backend API with production-shaped records and a fake `PublishingProvider`; do not call Meta, TikTok, Postiz, OAuth providers, or live publishing engines yet. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Use `/api/v1` endpoints from the start so later Facebook/TikTok work can extend the contract without breaking the React client. [VERIFIED: .planning/research/ARCHITECTURE.md]
- Keep LocalPilot domain records separate from provider-engine mechanics: LocalPilot owns merchants, users, campaigns, platform drafts, versions, approvals, jobs, attempts, events, idempotency, and support diagnostics. [VERIFIED: .planning/research/ARCHITECTURE.md]
- Start with deterministic seeded demo data on the backend to preserve current `/app` behavior, then have React load and mutate that backend state through an API client. [VERIFIED: src/main.jsx] [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Suggested backend logical modules: `merchants`, `campaigns`, `drafts`, `approvals`, `publish_jobs`, `publish_attempts`, `publish_events`, `fake_publisher`, and `diagnostics`. [ASSUMED]
- Suggested frontend modules: `src/api/`, `src/models/`, `src/routes/`, `src/components/`, `src/publishing/`, and route-specific workspace components, following the phase decision to use symbo-style frontend organization as a reference. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]

## Data And API Contract Implications

- Campaign records should store the source business input currently represented by `campaignInput`: business, business type, offer, goal, audience, and future local-business metadata. [VERIFIED: src/main.jsx]
- Platform drafts should be distinct per platform, not copied captions; Phase 1 can seed current channel plans but should persist them as backend draft records. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: src/main.jsx]
- Draft versions must be immutable: each edit/regeneration creates a new version, approval targets exactly one version, and publishing reads only the approved version. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Approval snapshots must freeze the full future publish contract: platform, draft version, caption/body, CTA, media refs, connected-channel placeholder, provider payload, disclosure/settings placeholder, approver, timestamps, and idempotency key. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Publish jobs should aggregate user-facing lifecycle state; publish attempts should be immutable execution records with attempt number, trace ID, request digest, normalized status, redacted diagnostics, timestamps, and retry classification. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/research/ARCHITECTURE.md]
- Publish events should be append-only timeline records for merchant-facing status and support diagnostics. [VERIFIED: .planning/REQUIREMENTS.md]
- Use generic lifecycle states in Phase 1: `draft`, `needs_review`, `approved`, `queued`, `publishing`, `published`, `failed`, `retry_needed`, and `manual_fallback_required`. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Idempotency should be derived from the approved draft version plus platform/channel target, so retrying the same approved version creates a new attempt without creating a duplicate publish outcome. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md] [VERIFIED: .planning/REQUIREMENTS.md]
- Minimal endpoint set for planning: `GET/POST /api/v1/campaigns`, `GET /api/v1/campaigns/:id`, `POST /api/v1/campaigns/:id/drafts`, `PATCH /api/v1/drafts/:id`, `POST /api/v1/drafts/:id/approve`, `POST /api/v1/approvals/:id/publish`, `POST /api/v1/publish-jobs/:id/retry`, `GET /api/v1/publish-jobs/:id`, `GET /api/v1/debug/publish-jobs`. [ASSUMED]
- Backend responses should include safe presentation fields for current UI parity plus stable IDs and version fields for future contract correctness. [ASSUMED]

## Frontend Structure Implications

- Preserve current `/` marketing route and `/app` workspace route; add a hidden operator route such as `/app/debug` or `/app/admin` for Phase 1 diagnostics. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md] [VERIFIED: src/main.jsx]
- Extract API calls into `src/api/` before replacing UI state mutations. This lets the planner sequence backend creation, client adapter creation, then UI migration. [ASSUMED]
- Extract model normalization away from `src/main.jsx` so backend contracts and frontend models mirror each other explicitly. Current relevant helpers are `normalizeCampaignInput`, `buildPlansFromInput`, `createInitialPlans`, `normalizePlan`, and localStorage loaders. [VERIFIED: src/main.jsx]
- Replace `approvePlan`, `requestChanges`, `regeneratePlan`, and `exportPackage` local mutations with API-backed actions that refresh campaign/draft/job state. [VERIFIED: src/main.jsx]
- Keep localStorage only for non-sensitive preferences in Phase 1: `localpilot-language`, `localpilot-demo-active-module`, and selected index keys. [VERIFIED: src/main.jsx] [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Stop writing publish-critical records to localStorage: campaign input, generated plans, approval state, export/publish package, jobs, attempts, events, and diagnostics. [VERIFIED: src/main.jsx] [VERIFIED: .planning/REQUIREMENTS.md]
- Reuse existing UI cards, buttons, toasts, and CSS tokens where possible; this is a structure-and-state phase, not a total redesign. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md] [VERIFIED: .planning/codebase/CONCERNS.md]

## Security And Compliance Constraints

- OAuth secrets, refresh tokens, API keys, app secrets, provider credentials, and future platform tokens must never live in browser localStorage or committed files. [VERIFIED: AGENTS.md provided in prompt] [VERIFIED: .planning/REQUIREMENTS.md]
- Phase 1 must not make real provider calls, start real OAuth flows, or store live provider credentials. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- The fake adapter should still exercise approval, job, attempt, event, retry, and redaction behavior so later official API adapters inherit safe workflow boundaries. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/research/PITFALLS.md]
- Debug/admin responses must show trace IDs, statuses, error classes, redacted provider diagnostics, and next recommended action, but never tokens, raw OAuth payloads, cookies, secrets, or authorization headers. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Publishing must require explicit merchant approval before any live platform request in later phases; Phase 1 should enforce the same rule even for fake jobs. [VERIFIED: .planning/REQUIREMENTS.md]
- Production publishing must remain compatible with official Facebook/TikTok API paths and must not introduce scraping, cookie posting, browser automation, or AutoCLI-style production posting. [VERIFIED: AGENTS.md provided in prompt] [VERIFIED: .planning/research/PITFALLS.md]

## Verification Strategy

- Add contract/unit tests around backend lifecycle transitions: create campaign, create drafts, create immutable version, approve exact version, create fake job, execute attempt, retry transient failure, and prevent duplicate outcome through idempotency. [ASSUMED]
- Add redaction tests that intentionally pass token-like fields through fake provider diagnostics and assert responses/events/log-shaped payloads do not expose secrets. [VERIFIED: .planning/REQUIREMENTS.md]
- Add frontend smoke coverage for `/`, `/app`, hidden debug route, campaign regeneration, draft approval, fake publish, retry, and status timeline. Current repo has no test framework or `test` script, so Wave 0 should add minimal test infrastructure or explicit build/smoke checks. [VERIFIED: package.json] [VERIFIED: .planning/codebase/CONCERNS.md]
- Keep `npm run build` as a required regression check because existing deployment packaging depends on Vite output plus `scripts/prepare-sites-dist.mjs`. [VERIFIED: package.json] [VERIFIED: .planning/codebase/ARCHITECTURE.md]
- Add fixture tests for corrupted/old localStorage only where preferences remain browser-owned; publish-critical state should be verified through backend API fixtures instead. [VERIFIED: .planning/codebase/CONCERNS.md]
- Validate no provider network calls are reachable in Phase 1 by keeping fake adapter dependency-injected and failing tests if provider-specific environment variables are required. [ASSUMED]

## Risks And Mitigations

- Risk: Phase 1 becomes a broad frontend rewrite. Mitigation: extract only route/API/model/component/publishing seams needed to move publish-critical state off localStorage. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Risk: Backend records mirror current plan cards instead of future publish contracts. Mitigation: model immutable versions, approval snapshots, jobs, attempts, events, idempotency, and redacted diagnostics from the first schema. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
- Risk: Retry logic duplicates future external posts. Mitigation: one job can have many attempts, but idempotency is tied to the exact approved draft version and channel target. [VERIFIED: .planning/research/PITFALLS.md]
- Risk: Debug route leaks sensitive data. Mitigation: create redacted diagnostics as first-class fields and never expose raw provider payloads, tokens, OAuth URLs, cookies, or authorization headers. [VERIFIED: .planning/REQUIREMENTS.md]
- Risk: The current localStorage schema continues to drive source-of-truth behavior. Mitigation: centralize remaining preference storage and delete/ignore publish-critical keys after API migration. [VERIFIED: src/main.jsx] [VERIFIED: .planning/codebase/CONCERNS.md]
- Risk: No tests make the migration fragile. Mitigation: add minimal backend contract tests, frontend smoke tests, redaction tests, and `npm run build` gate before deeper refactors. [VERIFIED: .planning/codebase/CONCERNS.md]

## Suggested Plan Slices

1. **Backend skeleton and contracts:** Create backend app boundary, `/api/v1` routing, config, health endpoint, and typed publishing workflow schemas. Depends on no other slice. [ASSUMED]
2. **Persistence model and seed data:** Add merchants, users, business profiles, connected channel placeholders, campaigns, platform drafts, draft versions, approvals, publish jobs, attempts, and events. Depends on backend skeleton. [VERIFIED: .planning/REQUIREMENTS.md]
3. **Fake publishing lifecycle:** Implement fake adapter, deterministic success/failure paths, automatic retry rules, manual retry endpoint, idempotency enforcement, and event timeline. Depends on persistence model. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
4. **Redacted diagnostics and hidden debug route:** Add backend debug endpoint and frontend `/app/debug` or `/app/admin` view with jobs, attempts, trace IDs, error classes, redacted diagnostics, and next action. Depends on fake lifecycle. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
5. **Frontend API/model extraction:** Add `src/api`, `src/models`, route/component seams, and migrate campaign/draft/approval/job state from localStorage to API responses while preserving current visible behavior. Depends on backend contract. [VERIFIED: .planning/phases/01-backend-publishing-foundation/01-CONTEXT.md]
6. **LocalStorage cleanup and guardrails:** Keep language/module/index preferences, stop persisting publish-critical keys, and add reset/migration handling for stale demo state. Depends on frontend API migration. [VERIFIED: src/main.jsx]
7. **Verification wave:** Add backend lifecycle/redaction/idempotency tests, frontend route/workflow smoke tests, and build/package smoke checks. Depends on implementation slices. [VERIFIED: .planning/codebase/CONCERNS.md]

