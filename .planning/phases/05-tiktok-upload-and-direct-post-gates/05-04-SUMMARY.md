---
phase: 05-tiktok-upload-and-direct-post-gates
plan: 04
subsystem: api
tags: [tiktok, publishing, direct-post, upload-to-inbox, publish-lifecycle]

requires:
  - phase: 05-01
    provides: publish job/attempt/event/outcome lifecycle, approval snapshots
  - phase: 05-02
    provides: assert_channel_publishable health gate
  - phase: 05-03
    provides: frozen creatorInfoSnapshot + tiktokConfirmations in the approval snapshot
provides:
  - TikTok publisher delivering via upload-to-inbox/draft by default
  - Backend-owned per-attempt route selection recorded in diagnostics
  - Direct Post eligibility gate with deterministic upload fallback
affects: [05-05]

tech-stack:
  added: []
  patterns:
    - "Per-attempt route selection persisted in provider diagnostics (no schema change)"
    - "Eligibility gate returns structured checks + blockedReasons for support diagnostics"

key-files:
  created:
    - backend/app/tiktok_publisher.py
    - backend/tests/test_tiktok_publish_routes.py
    - backend/tests/test_tiktok_direct_post_gate.py
  modified:
    - backend/app/server.py
    - src/api/publishingClient.js

key-decisions:
  - "Route metadata stored in attempt diagnostics rather than a new publish_jobs column (D-09)"
  - "Direct Post blocked unless app-audit + scopes + creator compatibility + disclosure + channel health all pass; otherwise fall back to upload (D-08, D-10)"
  - "TikTok publish reuses the existing publish lifecycle helpers for jobs/attempts/events/outcomes"

patterns-established:
  - "select_publish_route + evaluate_direct_post_gate keep route choice backend-authoritative"
  - "deliver_via_route returns redacted diagnostics with route, deliveryMode, and providerResultRef"

requirements-completed: [TT-04, TT-05, TT-06]

duration: 20min
completed: 2026-06-24
---

# Phase 5 Plan 04: TikTok Publish Delivery + Direct Post Gating Summary

**TikTok publisher delivering approved snapshots via the safer upload-to-inbox route by default, with backend-owned per-attempt route selection and a Direct Post eligibility gate that deterministically falls back to upload when any official check fails.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-06-24
- **Tasks:** 2
- **Files modified:** 2 (+1 new module, +2 new tests)

## Accomplishments
- Added `backend/app/tiktok_publisher.py` with `queue_tiktok_publish`, `select_publish_route`, `evaluate_direct_post_gate`, `deliver_via_route`, and redacted `tiktok_diagnostics`.
- Default delivery uses the upload-to-inbox/draft route; the publish lifecycle (jobs, attempts, events, outcomes) reuses the existing store helpers and records the chosen route per attempt.
- Direct Post is gated on app-audit/app-review approval, required scopes, creator-settings compatibility, disclosure confirmations, and channel health; failures fall back to upload with classified `blockedReasons`.
- Added `POST /api/v1/approvals/{id}/publish-tiktok` and the `publishTiktokPost` client call.
- Enforced the channel-health publish gate (from 05-02) before any TikTok job is created.

## Task Commits

1. **Task 1 + Task 2 (upload-first delivery + Direct Post gate)** — `4a43efc` (feat)

Implemented together because route selection, the Direct Post gate, and lifecycle writes are one cohesive publish path in the new module.

## Files Created/Modified
- `backend/app/tiktok_publisher.py` - TikTok publish path, route selection, Direct Post gate, diagnostics.
- `backend/app/server.py` - `publish-tiktok` endpoint and `tiktok_publisher` import.
- `src/api/publishingClient.js` - `publishTiktokPost` client call.
- `backend/tests/test_tiktok_publish_routes.py`, `test_tiktok_direct_post_gate.py` - New coverage.

## Decisions Made
- Route metadata persists in attempt diagnostics (no `publish_jobs` schema change), per D-09.
- Upload route is the always-available official fallback; Direct Post requires the full eligibility set.

## Deviations from Plan

None - plan executed as written. TikTok retry routing was intentionally left on the existing generic retry path (retry is out of this plan's scope and changing it would conflict with the fake-publish TikTok retry tests).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. (Real Direct Post requires TikTok app-audit approval and granted scopes, which the gate models via eligibility input.)

## Next Phase Readiness
- Publish path is ready for 05-05 to insert backend media validation before job creation and a stable failure taxonomy.

---
*Phase: 05-tiktok-upload-and-direct-post-gates*
*Completed: 2026-06-24*
