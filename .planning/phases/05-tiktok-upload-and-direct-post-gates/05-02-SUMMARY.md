---
phase: 05-tiktok-upload-and-direct-post-gates
plan: 02
subsystem: api
tags: [channel-health, disconnect, facebook, tiktok, publishing-gate, sqlite]

requires:
  - phase: 05-01
    provides: channel_registry, sessions, scheduled_posts, connected_channels extensions
provides:
  - Canonical per-channel health states for Facebook and TikTok
  - Merchant-scoped channel health read API
  - Channel disconnect/reconnect mutations that preserve history
  - Server-enforced schedule/publish gating on channel health
affects: [05-03, 05-04, 05-05, manual-fallback-and-pilot-support]

tech-stack:
  added: []
  patterns:
    - "Canonical channel-health enum with alias normalization for stale provider states"
    - "Merchant-scoped session resolution at the HTTP boundary with demo-session fallback"

key-files:
  created:
    - backend/tests/test_channel_health.py
    - backend/tests/test_channel_disconnect.py
  modified:
    - backend/app/store.py
    - backend/app/server.py
    - backend/app/facebook_publisher.py
    - src/api/publishingClient.js

key-decisions:
  - "Reused connected_channels.status as the canonical health column rather than adding a new column"
  - "Publish gate checks stored connection status only; provider-specific page health stays in each publisher"

patterns-established:
  - "normalize_channel_health maps stale/unknown provider states into the six canonical states"
  - "resolve_merchant_id resolves a session token (header or query) and falls back to the demo merchant"

requirements-completed: [ACCT-04, ACCT-05, ACCT-06, ACCT-07]

duration: 18min
completed: 2026-06-24
---

# Phase 5 Plan 02: Channel Health Visibility + Disconnect Gates Summary

**Canonical per-channel health states for Facebook and TikTok with merchant-scoped read APIs, a history-preserving disconnect mutation, and server-enforced schedule/publish gating.**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-06-24
- **Tasks:** 2
- **Files modified:** 4 (+2 test files)

## Accomplishments
- Added the canonical channel-health enum (`connected`, `missing_permission`, `expired_token`, `review_blocked`, `reconnect_required`, `disconnected`) with alias normalization so stale provider states resolve into one documented status.
- Added `get_channel_health`, `serialize_channel_health`, `set_channel_health`, `disconnect_channel`, and `assert_channel_publishable` to `store.py`, all merchant-scoped and secret-redacted.
- Added `GET /api/v1/channels/health`, `POST /api/v1/channels/{id}/disconnect`, and `POST /api/v1/channels/{id}/reconnect` with session-based merchant resolution.
- Enforced the gate server-side in the Facebook publisher (disconnect backstop) and in `advance_scheduled_post_status`, while keeping content creation/editing available regardless of channel health.
- Extended `src/api/publishingClient.js` with `loadChannelHealth`, `disconnectChannel`, and `reconnectChannel`.

## Task Commits

1. **Task 1 + Task 2 (health visibility + disconnect gates)** — `7845c94` (feat)

Tasks were implemented together because the health read path and disconnect/gate enforcement share the same `store.py` functions and `connected_channels.status` column; they were committed as one cohesive feat commit with both test suites.

## Files Created/Modified
- `backend/app/store.py` - Health enum, normalization, channel-health read/serialize, disconnect/reconnect, publish gate.
- `backend/app/server.py` - Channel health/disconnect/reconnect routes and merchant/session resolver.
- `backend/app/facebook_publisher.py` - Disconnect backstop before queueing a Facebook publish.
- `src/api/publishingClient.js` - Channel health and disconnect/reconnect client calls.
- `backend/tests/test_channel_health.py` - Canonical state coverage, normalization, merchant scoping, redaction.
- `backend/tests/test_channel_disconnect.py` - Disconnect/reconnect behavior and publish-gate regressions.

## Decisions Made
- Kept `connected_channels.status` as the single source of truth for channel health instead of adding a parallel column.
- The publish gate (`assert_channel_publishable`) checks only the stored connection status; Facebook Page capability remains enforced inside the Facebook publisher so fresh user-token publishes still work.

## Deviations from Plan

None - plan executed as written. (Tasks 1 and 2 share `store.py` functions, so they were committed together rather than as two separate feat commits.)

## Issues Encountered
- An initial version refined the publish gate with Facebook Page health, which blocked legitimate user-token publishes (no stored page token yet). Resolved by limiting the gate to the stored connection status and leaving page-capability checks in the publisher. Full backend suite green (81 tests).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Channel health and disconnect gating are ready for 05-03 (TikTok creator-info + disclosure gates), which builds on the same merchant-scoped channel state.

---
*Phase: 05-tiktok-upload-and-direct-post-gates*
*Completed: 2026-06-24*
