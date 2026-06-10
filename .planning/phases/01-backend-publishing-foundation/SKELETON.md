# Walking Skeleton - LocalPilot AI

**Phase:** 1
**Generated:** 2026-06-10

## Capability Proven End-to-End

A merchant can open the existing `/app` workspace, load backend-owned campaign, platform draft, media asset, connected-channel, and approval records, approve one exact platform draft version, queue a fake publish job, retry a failed fake attempt, and inspect redacted diagnostics through `/app/debug` while `/` and `/app` remain usable.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | Existing React 19/Vite SPA plus a deliberately separate backend API process | Preserves the current marketing and demo routes while adding the backend boundary required by Phase 1 without a broad frontend rewrite. |
| API boundary | Versioned `/api/v1` endpoints with Vite dev proxy | Gives the React client a stable publishing workflow contract and keeps provider-specific integrations outside Phase 1. |
| Data layer | SQLite database accessed through Python stdlib `sqlite3` | Provides real server-side read/write persistence without npm, pip, or cargo package installs; records are shaped for merchants, users, business profiles, connected channels, campaigns, drafts, versions, approvals, media assets, jobs, attempts, events, idempotency keys, and provider token boundary refs. |
| Token boundary | Server-only `backend/app/token_boundary.py` plus `provider_token_boundaries` records | Satisfies the Phase 1 SEC-02 boundary without live OAuth by modeling `storageMode: "external_secret_ref"`, `secretRef`, and rotation metadata. Public serializers expose redacted token boundary refs only; browser code never handles token payloads. |
| Publishing adapter | Fake provider module only | Exercises approval, queue, publishing, failure, retry, attempt, event, idempotency, and redaction behavior without OAuth, Meta, TikTok, Postiz, scraping, browser automation, cookie posting, or live provider calls. |
| Auth | Existing demo session remains a UI convenience; backend records include explicit approver fields | Phase 1 needs approver auditability but not a role/permission model. No OAuth secrets, refresh tokens, API keys, provider credentials, cookies, or authorization headers are stored or displayed. |
| Deployment target | Local full-stack run command plus unchanged static build/package commands | Walking skeleton proves the full backend-backed workflow locally while preserving the existing OpenAI/Sites static packaging path for the frontend. |
| Directory layout | `backend/app/*`, `backend/tests/*`, `src/api/*`, `src/models/*`, `src/components/*`, `src/routes/*`, `src/publishing/*`, `src/storage/*` | Matches D-07 and D-08 by introducing backend contract/token-boundary, model, route, component, API-client, publishing workflow, and preference-storage boundaries while keeping the current source entry intact. |

## Stack Touched in Phase 1

- [ ] Project scaffold - backend app package, backend tests, dev orchestration script, Vite proxy, and package scripts
- [ ] Routing - preserve `/` and `/app`; add hidden `/app/debug`
- [ ] Database - SQLite-backed workflow records with at least one real read and one real write, including `media_assets` and provider token boundary refs
- [ ] UI - `Approve exact draft`, `Queue fake publish`, `Retry publish`, frozen snapshot, timeline, and debug diagnostics wired to `/api/v1`
- [ ] Security boundary - browser responses and localStorage expose redacted token boundary refs only, with tests proving token-like data stays out of frontend payloads
- [ ] Deployment - `npm run dev:full` exercises the full stack locally; `npm run build` and `npm run package:sites` continue to validate the existing static frontend packaging path

## Phase 1 Plan Waves

| Wave | Plans | Capability |
|---|---|---|
| 1 | `01-01-PLAN.md` | Backend approval, media refs, token boundary, and workflow persistence foundation |
| 2 | `01-02-PLAN.md` | `/app` approval UI, frontend API/model boundary, and frozen snapshot display |
| 3 | `01-03-PLAN.md` | Backend fake publish jobs, attempts, events, and lifecycle tests |
| 4 | `01-04-PLAN.md`, `01-05-PLAN.md` | Frontend timeline UI can proceed in parallel with backend retry/idempotency/redaction |
| 5 | `01-06-PLAN.md`, `01-07-PLAN.md` | Retry UI can proceed in parallel with backend debug diagnostics API |
| 6 | `01-08-PLAN.md` | Hidden `/app/debug` route extraction and diagnostics UI |
| 7 | `01-09-PLAN.md` | Browser storage guardrails and aggregate verification gates |

## Out of Scope

- Real OAuth flows
- Meta provider calls
- TikTok provider calls
- Postiz or publishing-engine wrapping
- Scraping, browser automation, cookie posting, AutoCLI production publishing, or live provider sessions
- Full role/permission model for diagnostics
- Provider-specific Meta/TikTok substates
- Direct Xiaohongshu publishing
- Paid ads publishing

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without renegotiating the architectural decisions above:

- Phase 2: Decide whether LocalPilot wraps Postiz-style publishing infrastructure or uses native provider adapters.
- Phase 3: Turn one local offer into editable Facebook and TikTok draft records with local CTA context.
- Phase 4: Connect official Facebook Pages and publish approved Facebook drafts first.
- Phase 5: Connect TikTok and deliver approved TikTok drafts through official upload/draft paths with Direct Post gated.
- Phase 6: Add safe manual fallback and pilot support workflows for blocked jobs.
