---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Phase Details
status: completed
stopped_at: Completed 07-03-PLAN.md
last_updated: "2026-06-25T17:28:16.302Z"
last_activity: 2026-06-25 -- Phase 08 marked complete
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 9
  completed_plans: 9
  percent: 43
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-09)

**Core value:** A local business owner can go from one marketing idea to approved, platform-native Facebook and TikTok posts published through their own official accounts with minimal effort.
**Current focus:** Phase 08 — website-crawl-smart-onboarding

## Current Position

Phase: 08 — COMPLETE
Plan: 2 of 2
Status: Phase 08 complete
Last activity: 2026-06-25 -- Phase 08 marked complete

## Performance Metrics

**Velocity:**

- Total plans completed: 14
- Average duration: N/A
- Total execution time: N/A

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 9 | N/A | N/A |
| 02 | 1 | N/A | N/A |
| 05 | 5 | - | - |

**Recent Trend:**

- Last 5 plans: 01-05, 01-06, 01-07, 01-08, 01-09
- Trend: Phase 02 complete, Phase 03 Predis replica demo surface and backend product records implemented with committed screen smoke coverage, AI Generator assistant reply-to-post conversion, source URL and image import, Creative Editor Idea Lab scoring/apply, bulk creative variations, UGC voiceover packages, multilingual creative variants, layer layout moves, backend approval review links, notification outbox, public review route feedback loop, backend competitor source analysis, template import records, asset library records, media/storyboard asset records, structured layer controls, layer edits, resize variants, rendered preview outputs, and performance analytics dashboard

*Updated after each plan completion*
| Phase 08 P01 | 6min | 4 tasks | 4 files |
| Phase 08 P02 | 10min | 3 tasks | 3 files |
| Phase 08 P03 | 9min | 3 tasks | 6 files |
| Phase 07 P03 | 15min | 2 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Facebook production publishing is sequenced before TikTok; Xiaohongshu direct publishing is deferred to v2.
- [Roadmap]: Run a Postiz-style publishing engine spike before building deep custom Meta or TikTok provider wrappers.
- [Roadmap]: AutoCLI/browser-session automation is not allowed for production merchant publishing.
- [Roadmap]: Phase 03 now prioritizes a Predis.ai-style customer demo surface while keeping LocalPilot's local owner-approval and proof-loop wedge.
- [Roadmap]: Phase 1 preserves the current frontend demo while moving publish-critical state to backend-owned records.
- [Plan 01-07]: Debug publishing diagnostics are exposed through a read-only support endpoint with redacted token-boundary refs and provider diagnostics.
- [Plan 01-09]: Browser localStorage is limited to allowlisted preferences and final gates cover backend workflow, debug, storage, build, and packaging.
- [Phase 08]: Used stdlib urllib for homepage fetch and MiniMax chat completions to avoid new dependencies.
- [Phase 08]: Onboarding routes require an authenticated merchant session instead of the demo fallback path.
- [Phase 08]: Confirmed onboarding profiles seed brand_kits in place for downstream generation flows.
- [Phase 08]: Kept website onboarding inside the existing AppDemo shell and hid the workspace until the profile is confirmed.
- [Phase 08]: Reused Modal, toasts, and the requestJson client boundary for crawl, save, replace, and confirm actions.
- [Phase 08]: ONBOARD-03 voiceover/avatar defaults now persist through crawl drafts and confirm into brand_kits.voice_json.
- [Phase 08]: Rewrote the Phase 08 roadmap goal into user-story form so MVP verification can run cleanly.
- [Phase 07]: Expose /api/v1/auth dev-login capability from google_auth.dev_login_enabled().
- [Phase 07]: Fetch backend auth capability only for the no-client-ID login modal path so configured Google sign-in stays unchanged.

### Pending Todos

- Review the Scribe creator-style video workflow with the user in the running UI and decide whether to deepen actor/template rendering or keep the deterministic storyboard boundary for the next slice.
- Fold `.planning/quick/20260617-facebook-demo-publish-loop/` and `.planning/quick/20260617-facebook-oauth-connect/` into the Phase 03 execution slices as the Facebook adapter.
- Replace the local in-memory token vault with encrypted or secret-managed token persistence in the Facebook hardening phase.

### Blockers/Concerns

- Meta app review and current permission requirements must be verified in an authenticated Meta developer account before production Facebook rollout.
- Phase 03 uses local in-memory OAuth token vault for demo only; production needs encrypted/secret-managed token persistence, rotation, and app review hardening in Phase 4.
- Exact Predis in-app UI may differ behind login; Phase 03 execution should capture screenshots if the user provides login access.
- TikTok Direct Post remains gated by app audit, scopes, creator-info UX, privacy/disclosure settings, and official eligibility.
- Postiz-style reuse fit, licensing, deployment, status mapping, and token residency must be resolved before deep provider implementation.
- Exact Predis in-app UI can still differ behind login; the current Scribe-backed parity covers the documented creator-style video workflow without copying proprietary media assets.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Xiaohongshu | Direct merchant-owned organic note publishing | Deferred to v2 pending official or partner route | Roadmap creation |
| Analytics | Production provider ingestion, phone/booking/POS evidence, deep ROI dashboard, and weekly reporting | Deferred to v2 after publishing proof | Roadmap creation |
| Channels | Instagram and Google Business Profile publishing | Deferred until Facebook/TikTok proof is stable | Roadmap creation |

## Session Continuity

Last session: 2026-06-25T17:27:29.947Z
Stopped at: Completed 07-03-PLAN.md
Resume file: None
