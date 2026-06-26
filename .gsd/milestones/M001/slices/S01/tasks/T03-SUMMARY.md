---
id: T03
parent: S01
milestone: M001
key_files:
  - backend/app/generation_providers/heygen_adapter.py
  - backend/app/store.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T06:03:27.200Z
blocker_discovered: false
---

# T03: Created HeyGen avatar adapter and updated catalog seed from ccdance_stub to heygen:ready

**Created HeyGen avatar adapter and updated catalog seed from ccdance_stub to heygen:ready**

## What Happened

Created backend/app/generation_providers/heygen_adapter.py implementing HeyGenAvatarAdapter. submit() calls POST /v2/video/generate with avatar_id, script, and voice_id derived from job settings/request; returns HeyGen video_id. poll() calls GET /v1/video_status.get?video_id={id} and normalizes pending/processing/waiting → running, completed → succeeded with storageRef/previewRef, anything else → failed. HEYGEN_API_KEY read from env. Updated store.py seed_generation_model_catalog: CCDANCE_AVATAR_MODEL_ID entry now has provider_key="heygen", model_key="heygen-avatar", display_name="HeyGen UGC Avatar", readiness_status="ready". The seed uses update on conflict so existing DBs pick up the change on next startup.

## Verification

Verification evidence recorded: `python3 -c 'from backend.app.generation_providers import get_adapter; a = get_adapter("heygen:avatar_video"); print(type(a).__name__)'` exited 0 (HeyGenAvatarAdapter instantiated correctly).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -c 'from backend.app.generation_providers import get_adapter; a = get_adapter("heygen:avatar_video"); print(type(a).__name__)'` | 0 | HeyGenAvatarAdapter instantiated correctly | 290ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/app/generation_providers/heygen_adapter.py`
- `backend/app/store.py`
