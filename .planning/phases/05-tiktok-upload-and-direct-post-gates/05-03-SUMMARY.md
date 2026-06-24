---
phase: 05-tiktok-upload-and-direct-post-gates
plan: 03
subsystem: api
tags: [tiktok, creator-info, disclosure, approval-snapshot, sqlite]

requires:
  - phase: 05-01
    provides: connected_channels extensions, approval snapshot pipeline
  - phase: 05-02
    provides: channel health and merchant-scoped channel state
provides:
  - Versioned TikTok creator-info snapshots on the connected channel
  - Approval snapshots that freeze creator info + confirmations for TikTok
  - Backend-authoritative disclosure/privacy/interaction confirmation gates
affects: [05-04, 05-05]

tech-stack:
  added: []
  patterns:
    - "Versioned provider settings snapshot persisted per connected channel"
    - "Approval snapshot freezes creator settings + confirmations for later publish validation"

key-files:
  created:
    - backend/tests/test_tiktok_creator_info.py
    - backend/tests/test_tiktok_disclosure_gates.py
  modified:
    - backend/app/store.py
    - backend/app/contracts.py
    - backend/app/server.py
    - src/api/publishingClient.js
    - backend/tests/test_facebook_publisher.py
    - backend/tests/test_fake_publish_lifecycle.py
    - backend/tests/test_debug_redaction.py
    - backend/tests/test_retry_redaction_idempotency.py

key-decisions:
  - "Stored creator info in a new connected_channels.creator_info_json column (migrate-only, matching the Phase 5 column pattern)"
  - "Embedded creatorInfoSnapshot + tiktokConfirmations directly into the frozen approval snapshot so refresh never mutates history"
  - "Confirmation validation lives in store.validate_tiktok_confirmations (StoreError-based); contracts only freezes the data"

patterns-established:
  - "validate_tiktok_confirmations enforces privacy/disclosure/interaction + stale-version checks server-side"
  - "TikTok approval requires tiktokConfirmations; Facebook approval path is untouched"

requirements-completed: [TT-01, TT-02, TT-03]

duration: 22min
completed: 2026-06-24
---

# Phase 5 Plan 03: TikTok Creator-Info + Disclosure Gates Summary

**Versioned TikTok creator-info snapshots persisted per channel, frozen into approval snapshots, with backend-authoritative disclosure/privacy/interaction confirmation gates and stale-version rejection.**

## Performance

- **Duration:** ~22 min
- **Completed:** 2026-06-24
- **Tasks:** 2
- **Files modified:** 4 source (+2 new tests, +4 prior-phase test helpers updated)

## Accomplishments
- Added `connected_channels.creator_info_json` (migrate-only) and `default_tiktok_creator_info`, `get_tiktok_creator_info`, `refresh_tiktok_creator_info`, and `ensure_tiktok_creator_info_seed` for versioned creator settings.
- Extended `build_approval_snapshot` to freeze `creatorInfoSnapshot` + `tiktokConfirmations` into TikTok approval snapshots (D-05, D-07).
- Added `validate_tiktok_confirmations` enforcing valid privacy level, required disclosure/interaction confirmations, interaction-setting consistency, commercial-disclosure rules, and creator-info version freshness.
- Wired `approve_draft` to require + validate confirmations for TikTok only, leaving Facebook approval unchanged.
- Added `GET /api/v1/tiktok/creator-info` and `POST /api/v1/tiktok/creator-info/refresh`, plus `loadTiktokCreatorInfo`/`refreshTiktokCreatorInfo` client calls.

## Task Commits

1. **Task 1 + Task 2 (creator-info persistence + disclosure gates)** — `4d6daba` (feat)

Implemented together because creator-info persistence and the disclosure gate both flow through `approve_draft` and the shared approval snapshot.

## Files Created/Modified
- `backend/app/store.py` - Creator-info column/seed, snapshot getters/refresh, confirmation validation, approve_draft wiring.
- `backend/app/contracts.py` - Approval snapshot freezes creator info + confirmations for TikTok.
- `backend/app/server.py` - Creator-info read/refresh endpoints.
- `src/api/publishingClient.js` - Creator-info client calls.
- `backend/tests/test_tiktok_creator_info.py`, `test_tiktok_disclosure_gates.py` - New coverage.
- `backend/tests/test_facebook_publisher.py`, `test_fake_publish_lifecycle.py`, `test_debug_redaction.py`, `test_retry_redaction_idempotency.py` - Updated TikTok approval helpers to supply confirmations.

## Decisions Made
- Creator info stored as a single versioned JSON column on the channel; refreshing bumps the version and never rewrites past approval snapshots.
- Validation logic kept in `store` (has `StoreError`); `contracts` only freezes the validated data.

## Deviations from Plan

### Required test updates (intended behavior change)
**1. [Rule 2 - Missing Critical] Updated prior-phase TikTok approval helpers**
- **Found during:** Task 2 (disclosure gate)
- **Issue:** Requiring TikTok disclosure confirmations broke four prior-phase tests that approved TikTok drafts without them.
- **Fix:** Updated their `approve_tiktok`/`approve_platform` helpers to fetch creator-info version and submit valid confirmations, preserving each test's original intent.
- **Files modified:** test_facebook_publisher.py, test_fake_publish_lifecycle.py, test_debug_redaction.py, test_retry_redaction_idempotency.py
- **Verification:** Full suite green (89 tests).
- **Committed in:** 4d6daba

---

**Total deviations:** 1 (required prior-phase test alignment with the new gate)
**Impact on plan:** No scope creep; change was mandated by the plan's TikTok approval requirement.

## Issues Encountered
None beyond the expected test alignment above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Frozen creator-info + confirmations are ready for 05-04 to validate at publish time and gate Direct Post.

---
*Phase: 05-tiktok-upload-and-direct-post-gates*
*Completed: 2026-06-24*
