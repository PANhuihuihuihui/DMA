# Phase 1: Backend Publishing Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-10
**Phase:** 1-Backend Publishing Foundation
**Areas discussed:** Backend shape, Demo bridge, Approval snapshot, Status timeline, Support diagnostics

---

## Backend Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Production-shaped skeleton | FastAPI + Postgres + migrations + backend API contracts from the start. More setup, but best foundation for OAuth, tokens, publish jobs, and future provider adapters. | |
| Local lightweight API | A small local/dev API with simple file or in-memory persistence. Faster to demo, but likely gets replaced when real Facebook/TikTok auth arrives. | |
| Hybrid foundation | Production-shaped API/data model, but fake adapter and minimal auth in Phase 1. Keeps the architecture real while avoiding OAuth/provider complexity too early. | yes |
| Other | User-defined backend shape. | |

**User's choice:** Hybrid foundation.
**Notes:** Backend should be production-shaped enough for future OAuth/token/publish jobs, but Phase 1 should avoid real provider complexity.

---

## Demo Bridge

| Option | Description | Selected |
|--------|-------------|----------|
| Publish-critical only | Move only approval snapshots, publish jobs, attempts, events, and platform status to the backend. Keep campaign input/demo plans mostly local for now. | |
| Campaign + publish workflow | Move campaign records, platform drafts, approvals, publish jobs, attempts, and events to the backend. Keep only non-sensitive preferences like language/module selection in localStorage. | yes |
| Full demo state migration | Move nearly everything currently in localStorage to backend records, including session-ish demo state, active module, selected indexes, plans, and export package. | |
| Other | User-defined bridge. | |

**User's choice:** Campaign + publish workflow.
**Notes:** User added that Phase 1 should begin restructuring frontend code into model, router, component, and API boundaries while keeping current behavior the same. User wants `symbo` as reference.

---

## Approval Snapshot

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal snapshot | Freeze title/caption/platform/status fields only. Simpler, but may need redesign once real providers arrive. | |
| Full publish contract | Freeze platform, draft version, caption/body, CTA, media refs, connected-channel placeholder, provider payload, disclosure/settings placeholder, approver, timestamps, and idempotency key. | yes |
| Human-readable snapshot first | Freeze exactly what the merchant sees in the UI, then derive provider payload later. Better for trust, less precise for provider integration. | |
| Other | User-defined snapshot. | |

**User's choice:** Full publish contract.
**Notes:** User said `symbo` has full future publish contract thinking and should be referenced.

### Approval Snapshot Source Of Truth

| Option | Description | Selected |
|--------|-------------|----------|
| Backend schema first | Define the canonical contract in backend models/API schemas, then frontend models mirror it. Best for persistence, audit, and future provider adapters. | yes |
| Shared frontend/backend types | Define a shared contract package or schema file used by both frontend and backend. Best consistency, but more setup in a JS + Python stack. | |
| Frontend model first | Define the contract in frontend models first, then backend persists it. Faster for UI iteration, weaker for audit/source-of-truth. | |
| Other | User-defined source of truth. | |

**User's choice:** Backend schema first.
**Notes:** Frontend should mirror the backend contract.

### Approval Snapshot Versioning

| Option | Description | Selected |
|--------|-------------|----------|
| Strict immutable versions | Every draft edit creates a new version. Approval always points to one exact version. Publishing only uses that approved version. | yes |
| Version on approval only | Drafts can change freely while editing. When approved, the system freezes one snapshot version. | |
| Loose snapshot history | Store snapshots for visibility, but allow the current draft to remain the main source. Simpler, but weaker audit safety. | |
| Other | User-defined versioning. | |

**User's choice:** Strict immutable versions.
**Notes:** Applies even with the fake adapter.

---

## Status Timeline

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal lifecycle | `draft -> approved -> publishing -> published/failed`. Faster, but likely too thin for future provider mapping. | |
| Realistic lifecycle | `draft -> needs_review -> approved -> queued -> publishing -> published | failed | retry_needed | manual_fallback_required`, plus attempt/event records. | yes |
| Provider-shaped lifecycle | Model generic states plus provider-specific substates now, such as Meta review/error states and TikTok inbox/moderation states. More future-proof, but heavier for Phase 1. | |
| Other | User-defined lifecycle. | |

**User's choice:** Realistic lifecycle.
**Notes:** Do not overfit to provider-specific substates in Phase 1.

### Retry Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Manual retry only | Failed or retry-needed jobs wait for a user/operator action. Simple and transparent. | |
| Auto retry transient failures | Fake adapter simulates transient failures and retries automatically with attempt records. More realistic for future worker behavior. | |
| Both manual and auto retry | System can auto retry transient fake failures, but user/operator can also manually retry eligible jobs. Strongest model, more UI/state complexity. | yes |
| Other | User-defined retry behavior. | |

**User's choice:** Both manual and auto retry.
**Notes:** Auto retry should be small and deterministic; every retry must create an attempt and respect idempotency.

---

## Support Diagnostics

| Option | Description | Selected |
|--------|-------------|----------|
| API/data only | Store redacted events, attempts, provider diagnostics, and trace IDs. No UI yet. Fastest and enough for planner/executor. | |
| Simple admin/debug view | Add an internal support/debug surface in the app showing publish jobs, attempts, statuses, error classes, trace IDs, and next action. More useful for pilots. | yes |
| Developer logs only | Rely on console/server logs and database records. Least product work, but weak for support. | |
| Other | User-defined diagnostic surface. | |

**User's choice:** Simple admin/debug view.
**Notes:** Must not expose tokens, secrets, raw OAuth payloads, or sensitive credentials.

### Debug View Access

| Option | Description | Selected |
|--------|-------------|----------|
| Hidden dev/operator route | A non-public route like `/app/debug` or `/app/admin` available in local/demo mode. Fastest and enough for Phase 1. | yes |
| Role-gated operator view | Add a basic role/permission model so only internal operators can see it. More production-shaped, but may pull auth complexity forward. | |
| Build data/API only first | Store the diagnostics and defer the visible debug view until later, despite choosing the debug-view direction. | |
| Other | User-defined access model. | |

**User's choice:** Hidden dev/operator route.
**Notes:** Full role/permission model is deferred.

---

## the agent's Discretion

- Exact backend framework details remain planner discretion inside the production-shaped backend direction.
- Exact hidden debug route name is planner discretion.
- Exact frontend folder names are planner discretion as long as they establish model/router/component/API/publishing-workflow boundaries.

## Deferred Ideas

- Full frontend rewrite.
- Full role/permission model for operator diagnostics.
- Provider-specific Meta/TikTok lifecycle substates.
- Real OAuth/provider publishing.
