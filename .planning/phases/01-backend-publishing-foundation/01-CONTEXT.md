# Phase 1: Backend Publishing Foundation - Context

**Gathered:** 2026-06-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 creates LocalPilot's safe publishing foundation before any live Facebook or TikTok calls. It delivers a production-shaped backend API and data model, API-backed campaign/publish workflow records, strict approval snapshots, a realistic fake publish lifecycle, retry-safe attempt/event tracking, redacted diagnostics, and a small internal debug surface while preserving the current marketing/demo experience.

This phase may introduce frontend structure needed for the publishing foundation, but it must not become a total frontend rewrite. Refactoring should create useful seams around models, routes, components, API clients, and publishing workflow modules only where those seams support Phase 1 requirements.

</domain>

<decisions>
## Implementation Decisions

### Backend Shape
- **D-01:** Use a hybrid foundation: production-shaped backend API and data model, fake publishing adapter, and minimal/local auth only as needed for the demo.
- **D-02:** Do not pull real OAuth, Meta, TikTok, or provider-specific integration complexity into Phase 1.
- **D-03:** Backend design should prepare for future OAuth, token storage, publish jobs, and provider adapters even though those are implemented later.

### Demo Bridge
- **D-04:** Move the campaign and publish workflow behind backend APIs in Phase 1: campaign records, platform drafts, approval snapshots, publish jobs, attempts, and events.
- **D-05:** Keep low-risk UI preferences in localStorage for now, such as language, active module, selected module, and selected indexes.
- **D-06:** Preserve current marketing and demo routes while replacing publish-critical localStorage state with API-backed records.

### Frontend Structure
- **D-07:** Begin restructuring the frontend away from the monolithic `src/main.jsx` shape by introducing model, router/route, component, API-client, and publishing-workflow boundaries.
- **D-08:** Use `symbo` as a reference for mature frontend organization, especially its `api`, `router`, `components`, `store`, `constants`, and channel-specific component directories.
- **D-09:** Keep the current user-visible demo behavior the same unless a change is necessary to support backend-backed campaign/publish workflow state.

### Approval Snapshot
- **D-10:** Approval snapshots must freeze a full future publish contract, not just visible text/status fields.
- **D-11:** The backend schema is the source of truth for the publish contract. Frontend models mirror backend contracts explicitly rather than inventing separate approval payload shapes.
- **D-12:** The frozen contract should include platform, draft version, caption/body, CTA, media refs, connected-channel placeholder, provider payload, disclosure/settings placeholder, approver, timestamps, and idempotency key.
- **D-13:** Use strict immutable draft versions: every draft edit creates a new version, approval points to one exact version, and publishing only uses the approved version.
- **D-14:** Strict versioning applies even when using the Phase 1 fake adapter.

### Status Timeline
- **D-15:** Model a realistic generic publish lifecycle in Phase 1: `draft`, `needs_review`, `approved`, `queued`, `publishing`, `published`, `failed`, `retry_needed`, and `manual_fallback_required`.
- **D-16:** Include publish attempts and event records from the first fake lifecycle.
- **D-17:** Do not overfit Phase 1 states to Meta-specific or TikTok-specific substates. Provider-specific substates can map into the generic model in later phases.
- **D-18:** Support both automatic and manual retry. Automatic retry should be small and deterministic in Phase 1.
- **D-19:** Every retry creates a new attempt record and uses idempotency to prevent duplicate publish outcomes.

### Support Diagnostics
- **D-20:** Add a simple internal admin/debug surface in the app for Phase 1.
- **D-21:** The debug surface should show publish jobs, attempts, statuses, error classes, trace IDs, redacted provider diagnostics, and next recommended action.
- **D-22:** The debug surface must not expose tokens, secrets, raw OAuth payloads, or sensitive credentials.
- **D-23:** Gate the Phase 1 debug view as a hidden dev/operator route, such as `/app/debug` or `/app/admin`, instead of introducing a full role/permission model.

### the agent's Discretion
- The planner may choose exact backend framework details inside the already-researched direction, as long as the design remains production-shaped and supports backend-first contracts.
- The planner may choose the exact hidden debug route name.
- The planner may choose the exact frontend folder names if they preserve the decided concepts: models, routes/router, components, API/client, and publishing workflow modules.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project And Phase Scope
- `.planning/PROJECT.md` - Project intent, core value, platform priority, CLI/reuse decision, and scope boundaries.
- `.planning/REQUIREMENTS.md` - Phase 1 requirement IDs and full v1 traceability.
- `.planning/ROADMAP.md` - Phase 1 goal, success criteria, MVP mode, and phase ordering.
- `.planning/STATE.md` - Current project state and accumulated decisions.

### Research
- `.planning/research/SUMMARY.md` - Recommended stack, architecture, phase ordering, and risk summary.
- `.planning/research/ARCHITECTURE.md` - Component boundaries, data flow, provider adapter model, and symbo lessons.
- `.planning/research/STACK.md` - Backend/API feasibility and stack recommendations.
- `.planning/research/PITFALLS.md` - Security, OAuth, token, retry, and platform risk prevention.
- `.planning/research/FEATURES.md` - Publishing-workflow feature expectations.

### Codebase Maps
- `.planning/codebase/ARCHITECTURE.md` - Current React/Vite SPA architecture and localStorage data flow.
- `.planning/codebase/INTEGRATIONS.md` - Current lack of live integrations, auth provider, database, and network calls.
- `.planning/codebase/CONCERNS.md` - Monolithic frontend, localStorage/security risk, missing backend boundary, and missing tests.
- `.planning/codebase/STRUCTURE.md` - Current repo/file organization.
- `.planning/codebase/CONVENTIONS.md` - Existing style and naming conventions.

### Symbo Reference Repo
- `/Users/huijie/Documents/symbo/apps/frontend/src/router/` - Reference for separated router/routes structure.
- `/Users/huijie/Documents/symbo/apps/frontend/src/components/` - Reference for component organization and channel-specific component directories.
- `/Users/huijie/Documents/symbo/apps/frontend/src/store/` - Reference for store/state module boundaries.
- `/Users/huijie/Documents/symbo/apps/frontend/src/api/` - Reference for API client boundaries and generated/client-side API organization.
- `/Users/huijie/Documents/symbo/apps/frontend/src/constants/Meta.ts` - Reference for platform constants.
- `/Users/huijie/Documents/symbo/apps/frontend/src/constants/Tiktok.ts` - Reference for platform constants.
- `/Users/huijie/Documents/symbo/apps/api/README.md` - Reference for API service shape.
- `/Users/huijie/Documents/symbo/apps/api/external-api-template.yaml` - Reference for API contract thinking.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/main.jsx` - Contains current routes, marketing page, demo workspace, campaign data builders, approval interactions, localStorage persistence, and module navigation. Phase 1 should extract from this file carefully rather than rewrite it wholesale.
- `src/styles.css` - Contains current visual system and responsive app layout. New debug/workflow UI should reuse existing classes/tokens where practical before introducing a new styling system.
- `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs` - Existing deployment packaging should keep working after backend/frontend structure changes.

### Established Patterns
- React Router is already used in `src/main.jsx`; Phase 1 can formalize route definitions without changing user-visible navigation.
- Browser localStorage currently stores language, demo session, campaign input, plans, selected module, selected indexes, and export package. Phase 1 should only replace publish-critical state, not every preference.
- Demo generation is deterministic and local today. Phase 1 should create API-backed campaign/draft records while preserving enough seeded/fake behavior to keep the demo usable.

### Integration Points
- `/app` is the current workspace route and should remain usable.
- A hidden route such as `/app/debug` or `/app/admin` can host Phase 1 operator diagnostics.
- Campaign generation, approval, status timeline, and export/publish package areas in `AppDemo` are the natural UI entry points for API-backed workflow state.
- There is no existing backend, database, auth provider, token store, or live social API boundary; all of these must be introduced deliberately and safely.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly wants Phase 1 to introduce frontend structure: models, router/routes, components, and API/client boundaries.
- The user wants `symbo` treated as a reference repo for mature frontend organization and future publish-contract thinking.
- The user wants to keep current behavior the same while creating a structure that can carry real publishing work.
- The approval snapshot should represent a full future publish contract, even before real provider adapters exist.

</specifics>

<deferred>
## Deferred Ideas

- Full frontend rewrite - defer. Phase 1 may introduce structure and extract publish-foundation seams, but the whole app should not be rewritten.
- Full role/permission model for operator diagnostics - defer. Phase 1 uses a hidden dev/operator route.
- Provider-specific Meta/TikTok substates - defer to Facebook/TikTok phases. Phase 1 uses generic lifecycle states.
- Real OAuth and provider publishing - defer to later phases. Phase 1 uses fake adapter and backend-first contracts.

</deferred>

---

*Phase: 1-Backend Publishing Foundation*
*Context gathered: 2026-06-10*
