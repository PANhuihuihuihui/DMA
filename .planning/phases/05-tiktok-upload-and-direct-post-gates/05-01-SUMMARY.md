# 05-01 Summary — Multi-Channel Foundation + Session Auth

**One-liner:** Added the Phase 5 foundation schema and auth slice: `channel_registry`, `sessions`, `scheduled_posts`, `publish_dispatch_queue`, connected-channel extensions, calendar-slot migration, and tenant-bound session resolution.

## What Was Built
- `backend/app/store.py`
  Added `sessions`, `channel_registry`, `scheduled_posts`, and `publish_dispatch_queue` tables.
  Extended `connected_channels` with `channel_registry_id`, `connected_by_user_id`, and `capabilities_json`.
  Seeded channel registry records for Facebook, TikTok, Xiaohongshu, Instagram, and Google Business Profile.
  Added demo-session seeding and `calendar_slots -> scheduled_posts` migration with deterministic scheduled-post IDs.
  Added `advance_scheduled_post_status()` to enforce the channel-connected gate before `approved -> queued -> publishing`.
- `backend/app/sessions.py`
  Added `create_session`, `resolve_session`, `expire_session`, and `SessionError`.
- `backend/app/contracts.py`
  Added `serialize_session()` and extended lifecycle statuses with `cancelled`.
- `backend/tests/test_channel_registry.py`
  Covers registry seeding and connected-channel extension columns.
- `backend/tests/test_scheduled_posts.py`
  Covers zero-loss `calendar_slots -> scheduled_posts` migration and the disconnected-channel queue gate.
- `backend/tests/test_session_auth.py`
  Covers create/resolve, seeded demo session, expiry, logout, and serializer redaction.

## Deviations
- `channel_registry` now also seeds `instagram` and `google_business` as `coming_soon`.
  This is broader than the original minimum three-row seed, but it was needed to migrate all existing Phase 3 calendar slots into `scheduled_posts` without dropping rows or mis-linking platforms.
- Existing Phase 3 and fake-publish flows still read `calendar_slots` and approval-first publish jobs.
  This slice establishes the new foundation and migration path; later Phase 5 plans will move active scheduling/publish flows onto `scheduled_posts`.

## Verification
- `python3 -m unittest backend.tests.test_channel_registry backend.tests.test_scheduled_posts backend.tests.test_session_auth -v`
- `python3 -m unittest discover backend/tests -v`

## Self-Check: PASS
- New schema objects exist and initialize cleanly in fresh databases.
- Existing backend tests remained green after the migration and seed changes.
- Session tokens remain server-only, and serializers do not echo the raw token.
