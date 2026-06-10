# Phase 01 Source Coverage Audit

**Phase:** 01 Backend Publishing Foundation  
**Status:** Complete - revised after checker iteration 2  
**Generated:** 2026-06-10

## Coverage Table

| Source | ID | Feature / requirement | Plan | Status | Notes |
|---|---|---|---|---|---|
| GOAL | - | API-backed publishing records, fake publish lifecycle, approval snapshots, retry-safe status tracking, preserved demo/marketing routes | 01-01, 01-02, 01-03, 01-04, 01-05, 01-06, 01-07, 01-08, 01-09 | COVERED | Nine focused slices cover backend contract/storage, frontend approval, fake publish backend, fake publish UI, retry backend, retry UI, debug API, debug UI, and final storage gates. |
| REQ | FOUND-01 | Store merchants, users, business profiles, connected channels, campaigns, drafts, approvals, media assets, jobs, attempts, and events outside browser localStorage | 01-01, 01-09 | COVERED | Plan 01 adds server-owned workflow storage; Plan 09 proves publish-critical browser storage is removed. |
| REQ | FOUND-02 | Versioned backend API endpoints consumed by React app | 01-01, 01-02, 01-04, 01-06, 01-07, 01-08 | COVERED | `/api/v1` workflow, approval, publish, retry, job, and debug endpoints plus React clients. |
| REQ | FOUND-03 | Fake publishing adapter exercises full lifecycle without live credentials | 01-03, 01-04 | COVERED | Backend fake adapter and frontend timeline queue/display. |
| REQ | FOUND-04 | Immutable publish attempts with metadata, normalized status, diagnostics, timestamps | 01-03, 01-05 | COVERED | Attempts/events in fake lifecycle and retry. |
| REQ | FOUND-05 | Idempotency keys prevent duplicate external posts for same approved draft version | 01-05, 01-06 | COVERED | Backend idempotency guard and retry UI. |
| REQ | FOUND-06 | Preserve current demo/marketing routes while replacing publish-critical localStorage | 01-02, 01-04, 01-06, 01-08, 01-09 | COVERED | `/`, `/app`, `/app/debug`, retry UI, and storage smoke remain covered. |
| REQ | SEC-01 | Secrets never stored in browser localStorage or committed files | 01-01, 01-02, 01-09 | COVERED | Backend serializers and frontend storage boundary block token/credential data. |
| REQ | SEC-02 | Backend stores provider tokens in a server-side encrypted or secret-managed token boundary | 01-01, 01-02, 01-09 | COVERED | Plan 01 creates `backend/app/token_boundary.py` and `provider_token_boundaries`; Plans 02 and 09 prove browser exclusion and localStorage exclusion. |
| REQ | SEC-03 | Redact secrets from logs/events/errors/admin diagnostics | 01-05, 01-06, 01-07, 01-08, 01-09 | COVERED | Backend redaction before persistence/serialization, retry UI safe rendering, debug API/UI, and storage checks. |
| REQ | SEC-04 | Explicit merchant approval before publish request | 01-01, 01-02, 01-03, 01-04 | COVERED | Approval required before fake publish queue. |
| REQ | SEC-06 | Audit trail showing approver, draft version, and publish attempts | 01-01, 01-02, 01-03, 01-05, 01-07, 01-08 | COVERED | Snapshot, attempts, events, retry, debug API, and debug view. |
| REQ | APPR-04 | Approve a specific draft version for a specific platform | 01-01, 01-02 | COVERED | `Approve exact draft`. |
| REQ | APPR-05 | Freeze approved payload snapshot | 01-01, 01-02 | COVERED | Backend approval snapshot contract and UI display. |
| REQ | APPR-06 | Show platform draft/job statuses | 01-03, 01-04, 01-07, 01-08 | COVERED | Lifecycle statuses, timeline, and debug state display. |
| REQ | STATUS-01 | Timeline for each platform publish job | 01-03, 01-04, 01-07, 01-08 | COVERED | Backend events, `PublishTimeline`, and debug events. |
| REQ | STATUS-02 | Retry transient publish failures without duplicating successful posts | 01-05, 01-06, 01-07, 01-08, 01-09 | COVERED | Retry endpoint, idempotency, retry UI, debug diagnostics, and final gates. |
| RESEARCH | R-01 | Backend-owned publishing records before live integrations | 01-01 | COVERED | Backend API, SQLite records, media assets, token boundary refs. |
| RESEARCH | R-02 | `/api/v1` endpoints from the start | 01-01, 01-03, 01-05, 01-07 | COVERED | Versioned workflow, fake publish, retry, and debug routes. |
| RESEARCH | R-03 | LocalPilot owns workflow records separate from provider mechanics | 01-01, 01-03 | COVERED | Store owns domain records; fake adapter owns simulated mechanics. |
| RESEARCH | R-04 | Seeded backend data preserves `/app` behavior | 01-01, 01-02 | COVERED | Seed records are consumed through React client. |
| RESEARCH | R-05 | Immutable draft versions and full approval snapshots | 01-01, 01-02 | COVERED | D-10 through D-14 in backend and UI. |
| RESEARCH | R-06 | Jobs, attempts, events, lifecycle statuses | 01-03, 01-04 | COVERED | Backend fake lifecycle and frontend timeline. |
| RESEARCH | R-07 | Idempotency tied to approved draft version and channel target | 01-05, 01-06 | COVERED | Retry/idempotency backend plus retry UI. |
| RESEARCH | R-08 | Hidden `/app/debug` route | 01-07, 01-08 | COVERED | Debug endpoint and direct URL route outside sidebar. |
| RESEARCH | R-09 | Replace publish-critical localStorage; keep low-risk preferences | 01-02, 01-09 | COVERED | Preference helper allowlist and storage smoke. |
| RESEARCH | R-10 | Add backend lifecycle, redaction, idempotency, smoke/build checks | 01-01, 01-03, 01-05, 01-07, 01-09 | COVERED | Tests and final gates. |
| CONTEXT | D-01 | Hybrid production-shaped backend API/data model, fake adapter, minimal demo auth | 01-01, 01-03 | COVERED | Backend skeleton and fake adapter. |
| CONTEXT | D-02 | No real OAuth, Meta, TikTok, provider-specific complexity in Phase 1 | 01-01, 01-03 | COVERED | Fake adapter only and provider-call tests. |
| CONTEXT | D-03 | Prepare for OAuth, token storage, jobs, provider adapters | 01-01 | COVERED | Server-only token boundary and workflow records. |
| CONTEXT | D-04 | Move campaigns, drafts, approvals, jobs, attempts, events behind APIs | 01-01, 01-02, 01-03, 01-05 | COVERED | Workflow, approval, fake publish, and retry endpoints. |
| CONTEXT | D-05 | Keep low-risk UI preferences in localStorage | 01-02, 01-09 | COVERED | Preference helper allowlist. |
| CONTEXT | D-06 | Preserve current marketing/demo routes while replacing publish-critical localStorage | 01-02, 01-04, 01-08, 01-09 | COVERED | Route preservation, timeline/debug UI, and storage smoke. |
| CONTEXT | D-07 | Introduce model/router/component/API/publishing boundaries | 01-02, 01-08 | COVERED | New `src/api`, `src/models`, `src/components`, `src/routes`, `src/publishing`, `src/storage`. |
| CONTEXT | D-08 | Use symbo-style frontend organization as reference | 01-02, 01-08 | COVERED | Boundaries match API, router, component, store/storage concepts. |
| CONTEXT | D-09 | Keep current visible demo behavior unless needed for backend-backed state | 01-02 | COVERED | UI path preserved with required approval CTA change. |
| CONTEXT | D-10 | Approval snapshots freeze full publish contract | 01-01, 01-02 | COVERED | Frozen snapshot fields. |
| CONTEXT | D-11 | Backend schema is source of truth for publish contract | 01-01, 01-02 | COVERED | Backend serializers and frontend model mirrors. |
| CONTEXT | D-12 | Snapshot includes platform, version, caption/body, CTA, media refs, channel reference, provider payload, disclosures, approver, timestamps, idempotency key | 01-01, 01-02 | COVERED | Approval tests and UI panel. |
| CONTEXT | D-13 | Strict immutable draft versions | 01-01 | COVERED | PATCH creates new version; approvals point to exact version. |
| CONTEXT | D-14 | Strict versioning applies to fake adapter | 01-01, 01-03 | COVERED | Fake publish uses approved version snapshot only. |
| CONTEXT | D-15 | Generic lifecycle states | 01-03, 01-04 | COVERED | Lifecycle constants and timeline. |
| CONTEXT | D-16 | Attempts and event records from first fake lifecycle | 01-03 | COVERED | Attempt/event persistence. |
| CONTEXT | D-17 | Do not overfit to Meta/TikTok substates | 01-03 | COVERED | Generic statuses only. |
| CONTEXT | D-18 | Support automatic and manual retry; deterministic Phase 1 retry | 01-05, 01-06 | COVERED | Retry endpoint and UI. |
| CONTEXT | D-19 | Every retry creates a new attempt and uses idempotency | 01-05, 01-06 | COVERED | Attempt append and idempotency guard. |
| CONTEXT | D-20 | Add internal admin/debug surface | 01-07, 01-08 | COVERED | Debug API and `/app/debug`. |
| CONTEXT | D-21 | Debug shows jobs, attempts, statuses, error classes, trace IDs, redacted diagnostics, next action | 01-07, 01-08 | COVERED | Debug API/UI. |
| CONTEXT | D-22 | Debug must not expose tokens, secrets, raw OAuth payloads, credentials | 01-07, 01-08, 01-09 | COVERED | Redaction and storage/debug tests. |
| CONTEXT | D-23 | Hidden dev/operator route instead of full role model | 01-07, 01-08 | COVERED | Read-only debug endpoint and direct URL route outside sidebar. |

## Deferred Items Excluded From Planning

- Full frontend rewrite.
- Full role/permission model for operator diagnostics.
- Provider-specific Meta/TikTok substates.
- Real OAuth and provider publishing.
- Direct Xiaohongshu publishing.
- Paid ads publishing.
- Instagram and Google Business Profile v1 publishing.

## Wave Structure

| Wave | Plans | Dependency reason |
|---|---|---|
| 1 | `01-01-PLAN.md` | Creates backend persistence, media assets, token boundary, and exact approval contract. |
| 2 | `01-02-PLAN.md` | Wires `/app` approval UI to Plan 01 backend. |
| 3 | `01-03-PLAN.md` | Requires approval snapshots before backend fake publish jobs. |
| 4 | `01-04-PLAN.md`, `01-05-PLAN.md` | Frontend fake timeline depends on fake publish backend; retry backend depends on fake jobs but not timeline UI. |
| 5 | `01-06-PLAN.md`, `01-07-PLAN.md` | Retry UI depends on timeline UI plus retry backend; debug API depends on retry backend. |
| 6 | `01-08-PLAN.md` | Debug UI depends on retry UI surfaces and debug API. |
| 7 | `01-09-PLAN.md` | Storage/final gates require workflow, retry, and debug UI to exist. |

## Scope Sanity Check

Checker-targeted broad plans were split:

- Former `01-03` fake lifecycle split into `01-03` backend fake lifecycle (7 files) and `01-04` frontend timeline UI (5 files).
- Former `01-04` retry/idempotency split into `01-05` backend retry/redaction/idempotency (7 files) and `01-06` retry UI (6 files).
- Former `01-05` debug slice split into `01-07` debug API (6 files) and `01-08` debug route/UI (6 files).
- Final storage guardrails moved to `01-09` (5 files).
- `01-01` narrowed to 10 files by omitting an unnecessary Python package marker from the planned file list.

## Authority Check

No required item is omitted. No item is deferred due to implementation difficulty. The checker blocker items remain addressed by explicit `media_assets` coverage and explicit SEC-02 token-boundary coverage, and all current plan `files_modified` lists are at or below 10 entries.
