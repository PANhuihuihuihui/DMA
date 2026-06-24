# Phase 6: Manual Fallback And Pilot Support - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 makes blocked publishing safe to operate during a pilot. It delivers: (1) automatic marking of publish jobs as `manual_fallback_required` when official direct publishing is blocked, (2) an internal operator support console that inspects merchant/channel/job/attempt/error state with fully redacted diagnostics, (3) safe operator actions (retry, mark a manual support path) that never expose tokens or secrets, and (4) a per-job redacted app-review/pilot evidence export.

It does **not** build a merchant-facing manual publishing package or manual completion tracking this phase (see Deferred). It does not add new channels or rework Phase 3 content generation or Phase 4/5 publish mechanics.

In-scope requirements: STATUS-03, ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04.
Deferred this phase: STATUS-04 (merchant manual package), STATUS-05 (manual completion tracking).
</domain>

<decisions>
## Implementation Decisions

### Manual Fallback Trigger (STATUS-03)
- **D-01:** Auto-mark a publish job `manual_fallback_required` on **terminal, non-retryable** failure classes: `authentication`, `scope`, `creator_setting`, `media_validation`, `audit_or_visibility_block`, and `unknown`. Retryable classes (`rate_limit`, `platform_transient`) stay `retry_needed` and are **not** auto-routed to manual fallback.
- **D-02:** Auto-marking applies consistently to both the Facebook and TikTok publish paths, driven off the existing normalized error/failure class on the publish outcome.
- **D-03:** No dedicated merchant manual-package workflow is built this phase; an operator may still mark/clear a manual support path on a blocked job (see D-07).

### Operator Support Console (ADMIN-01, ADMIN-02, ADMIN-03)
- **D-04:** Introduce a new `/api/v1/admin/*` namespace for operator surfaces (e.g., list/inspect publish jobs, retry, mark-support). Reuse the existing redacted serializers (`serialize_debug_publish_job`, `list_debug_publish_jobs`) rather than inventing a parallel diagnostics shape.
- **D-05:** Gate the admin namespace behind an **operator/owner role resolved from the authenticated session** (via `sessions.resolve_session` → user role), plus a localhost/dev allowance so the demo can exercise it. All responses pass through `redact`/`safe_diagnostics`; tokens and secrets are never returned.
- **D-06:** Operator inspection must surface merchant, connected-channel, job, attempt, and error status with redacted provider IDs, trace IDs, error classes, and next recommended action (ADMIN-01/02).
- **D-07:** Operator actions (ADMIN-03): a **safe retry** reuses the existing retry paths (`facebook_publisher.retry_facebook_publish` / generic retry), and a **mark manual support path** action records an operator-sourced event/marker on the job without exposing secrets. Neither action ever reads or returns tokens.

### App-Review / Pilot Evidence (ADMIN-04)
- **D-08:** Provide a per-job **redacted evidence export** (e.g., `GET /api/v1/admin/publish-jobs/{id}/evidence`) that bundles merchant, channel, job, attempts, events, and diagnostics together with app-review-relevant fields already captured upstream: required/granted scopes, chosen publish route, Direct Post gate results, and TikTok creator/disclosure confirmations. It composes existing data only — no new capture — and is fully redacted (no tokens/secrets).

### the agent's Discretion
- Exact `/api/v1/admin/*` route shapes and how much of `serialize_debug_publish_job` is reused vs lightly extended.
- How the operator role is represented (reuse `users.role = 'owner'` vs add an explicit `operator` role) and the precise dev/localhost allowance mechanism.
- Where auto-fallback marking is invoked in the publish-outcome handling for both Facebook and TikTok (publisher vs a shared store helper).
- Whether the evidence export is a new serializer or a composition of existing serializers, and the exact field set within the agreed boundaries.
- Whether "mark manual support path" is a new lifecycle marker/event vs a status annotation, as long as it does not require STATUS-04/05 merchant features.
</decisions>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md` — security constraints (no secrets in browser/responses), owner-approval and official-API requirements.
- `.planning/REQUIREMENTS.md` — STATUS-03 and ADMIN-01..04 (in scope); STATUS-04/STATUS-05 (deferred this phase).
- `.planning/ROADMAP.md` §"Phase 6: Manual Fallback And Pilot Support" — goal and success criteria.
- `.planning/STATE.md` — current execution context.
- `backend/app/server.py` — `/api/v1/debug/publish-jobs` route, `resolve_merchant_id`/session resolution, route registration pattern, retry dispatch.
- `backend/app/store.py` — `serialize_debug_publish_job`, `list_debug_publish_jobs`, `LIFECYCLE_STATUSES` (`manual_fallback_required`), `update_publish_job_status`, `append_publish_event`, publish job/attempt/outcome model.
- `backend/app/contracts.py` — `redact`, `safe_diagnostics`, `summarize_approval_snapshot`, `redacted_token_boundary_ref`, lifecycle statuses.
- `backend/app/facebook_publisher.py` — `recommended_action_for`, `retry_facebook_publish`, error-class mapping.
- `backend/app/tiktok_publisher.py` — `FAILURE_CLASSES`, `classify_tiktok_failure`, route/Direct-Post diagnostics, simulated failures.
- `backend/app/sessions.py` — `resolve_session` / `SessionError` (operator role gating).
- `backend/tests/test_debug_redaction.py` — established redaction expectations the admin surface must keep satisfying.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `serialize_debug_publish_job` / `list_debug_publish_jobs` already produce the redacted operator view (merchant, platform, jobStatus, attemptCount, latestTraceId, errorClass, nextAction, attempts, events, redactedDiagnostics, approvalSnapshotSummary) — the backbone for ADMIN-01/02.
- Retry already exists end-to-end (`/publish-jobs/{id}/retry` → `facebook_publisher.retry_facebook_publish` / generic) for ADMIN-03 safe retry.
- `manual_fallback_required` is already a valid lifecycle status in `contracts.LIFECYCLE_STATUSES`.
- A stable failure taxonomy already exists across Facebook (`classify_error_class`) and TikTok (`classify_tiktok_failure` / `FAILURE_CLASSES`) to drive the auto-fallback decision (D-01).
- App-review-relevant data is already captured: required/granted scopes, chosen route, Direct Post gate results (`tiktok_publisher`), and creator/disclosure confirmations (approval snapshot).

### Established Patterns
- All diagnostics pass through `redact` / `safe_diagnostics`; token boundaries are redacted via `redacted_token_boundary_ref`. The admin surface must preserve this.
- Routes are registered manually in `JsonHandler.route_request` with small `match_*` helpers; sessions resolve via `resolve_merchant_id` (header `X-LocalPilot-Session` or `session` query, with demo fallback).
- Publish lifecycle is append-only: status transitions via `update_publish_job_status`, history via `append_publish_event`.

### Integration Points
- Auto-fallback marking should hook into the publish-outcome handling in `facebook_publisher` and `tiktok_publisher` (or a shared store helper) right after the terminal status is computed.
- The operator console and evidence export are new `/api/v1/admin/*` routes composing existing serializers; the frontend `src/api/publishingClient.js` can add operator client calls but the backend remains the source of truth.
</code_context>

<specifics>
## Specific Ideas

- Operator surfaces must be unmistakably read-mostly and secret-free; the only mutations are safe retry and marking a manual support path.
- The evidence export should be a single downloadable JSON per job so it can be attached directly to Meta/TikTok app-review submissions or pilot troubleshooting tickets.
- Auto-fallback should make the "why" obvious: the job's error class and next recommended action already explain the block; manual fallback is the terminal state for non-retryable blocks.
</specifics>

<deferred>
## Deferred Ideas

- **STATUS-04** — Merchant-facing manual publishing package (download/copy caption, hashtags, CTA, media checklist, disclosure notes, instructions). Deferred to a later phase/milestone.
- **STATUS-05** — Merchant manual completion tracking (mark a manual fallback package as completed; reflect manual completion in the draft timeline). Deferred with STATUS-04.
- Full manual-upload media workflow and any merchant self-serve manual posting UI.
</deferred>

---

*Phase: 6-Manual Fallback And Pilot Support*
*Context gathered: 2026-06-24*
