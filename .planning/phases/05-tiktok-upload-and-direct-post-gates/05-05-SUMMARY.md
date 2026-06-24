---
phase: 05-tiktok-upload-and-direct-post-gates
plan: 05
subsystem: api
tags: [tiktok, media-validation, failure-taxonomy, media-policy, publishing]

requires:
  - phase: 05-04
    provides: TikTok publisher and publish lifecycle
provides:
  - Backend-authoritative TikTok media validation before publish-job creation
  - Stable TikTok failure taxonomy with retry disposition
  - Strictest-relevant-channel-first media generation policy
affects: [manual-fallback-and-pilot-support]

tech-stack:
  added: []
  patterns:
    - "Pre-job media validation with stable reason codes (file_type, format_incompatible, duration, file_size, url_unreachable)"
    - "Normalized failure taxonomy shared across simulated and real provider errors"

key-files:
  created:
    - backend/tests/test_tiktok_media_validation.py
    - backend/tests/test_tiktok_failure_taxonomy.py
  modified:
    - backend/app/tiktok_publisher.py
    - backend/app/store.py
    - backend/app/server.py
    - src/api/publishingClient.js

key-decisions:
  - "Media validation runs before create_publish_job; invalid media returns HTTP 400 with a media_validation reason and no job is created"
  - "Server-owned media refs skip the network reachability check; only public http(s) URLs are HEAD-checked"
  - "Strictest-channel media policy defaults generateVariants=false (D-13)"

patterns-established:
  - "classify_tiktok_failure + normalize_failure_class produce the stable taxonomy from status codes or explicit classes"
  - "validate_tiktok_media raises TiktokMediaError carrying classified diagnostics"

requirements-completed: [TT-07, MEDIA-04]

duration: 21min
completed: 2026-06-24
---

# Phase 5 Plan 05: TikTok Media Validation + Failure Taxonomy Summary

**Backend-authoritative TikTok media validation before publish-job creation, a stable eight-class failure taxonomy with retry disposition, and a strictest-relevant-channel-first media generation policy.**

## Performance

- **Duration:** ~21 min
- **Completed:** 2026-06-24
- **Tasks:** 2
- **Files modified:** 3 source (+2 new tests)

## Accomplishments
- Added `validate_tiktok_media` (file type, format, duration, size, URL accessibility) that runs before `create_publish_job`; invalid media returns HTTP 400 with a stable `media_validation` reason and creates no job.
- Added the TikTok failure taxonomy (`authentication`, `scope`, `creator_setting`, `media_validation`, `rate_limit`, `audit_or_visibility_block`, `platform_transient`, `unknown`) with `classify_tiktok_failure`/`normalize_failure_class` and retry disposition.
- Added `simulateFailure` support so each taxonomy class is exercised end-to-end through the publish lifecycle and diagnostics.
- Added `store.strictest_channel_media_policy` (generateVariants=false by default; TikTok is the strictest enabled channel) and `GET /api/v1/tiktok/media-policy` + `loadTiktokMediaPolicy`.

## Task Commits

1. **Task 1 + Task 2 (media validation + failure taxonomy + media policy)** — `62bb979` (feat)

Implemented together because validation, classification, and the generation policy are one cohesive pre-publish media gate in the TikTok publisher.

## Files Created/Modified
- `backend/app/tiktok_publisher.py` - Media validation, failure taxonomy, simulated failures, pre-job gate wiring.
- `backend/app/store.py` - `strictest_channel_media_policy`.
- `backend/app/server.py` - `tiktok/media-policy` endpoint.
- `src/api/publishingClient.js` - `loadTiktokMediaPolicy` client call.
- `backend/tests/test_tiktok_media_validation.py`, `test_tiktok_failure_taxonomy.py` - New coverage.

## Decisions Made
- Server-owned media refs are trusted as validated assets and skip the network reachability check; only public http(s) URLs are HEAD-checked for type/size.
- Media generation defaults to a single strictest-channel-compliant asset; variants are opt-in.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered
- Initial taxonomy test reset deleted `approvals` before `idempotency_keys`, tripping a FK constraint. Fixed by deleting in FK-safe order. Full suite green (102 tests).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 5 is complete: TikTok connection health, creator-info/disclosure gates, upload-first delivery with Direct Post gating, and media validation/taxonomy are all in place. Ready for Phase 6 (manual fallback and pilot support), which can build on the failure taxonomy.

---
*Phase: 05-tiktok-upload-and-direct-post-gates*
*Completed: 2026-06-24*
