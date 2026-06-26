---
id: T01
parent: S03
milestone: M001
key_files:
  - /Users/huijie/DMA/.gsd-worktrees/M001/backend/app/store.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T03:21:18.264Z
blocker_discovered: false
---

# T01: Added VIDEO_CAPABILITIES constant, materialize_video_package, and build_video_job_handoff to store.py, and wired build_video_job_handoff into serialize_generation_job.

**Added VIDEO_CAPABILITIES constant, materialize_video_package, and build_video_job_handoff to store.py, and wired build_video_job_handoff into serialize_generation_job.**

## What Happened

Read backend/app/store.py to understand the carousel patterns (materialize_carousel_package, build_carousel_job_handoff, serialize_generation_job). Added VIDEO_CAPABILITIES = frozenset({"video", "avatar_video"}) near CAROUSEL_WORKFLOW_TYPE. Implemented materialize_video_package(conn, merchant_id, job_row, output_row) which: derives format from capability ("ugc_video" for avatar_video, "short_video" for video); creates content_batches, generated_creatives (platform="facebook", status="needs_review"), calendar_slots, proof_links with code SHORTV-{creative_id[-6:].upper()}, and creative_media_assets (asset_type="video", format="9:16 short video", aspect_ratio="9:16") rows; updates generation_outputs metadata_json with creativeId and mediaAssetId; calls ensure_review_link_for_creative; returns {"creativeId", "mediaAssetId"}. Implemented build_video_job_handoff(outputs, request_payload) which scans outputs for one where metadata is a dict and contains "creativeId", returning {"workflowType": "video", "creativeId": ...} if found or {} otherwise. Added payload.update(build_video_job_handoff(outputs, request_payload)) in serialize_generation_job after the existing carousel handoff call.

## Verification

Ran python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short — all 15 existing tests pass. Confirmed materialize_video_package, build_video_job_handoff, and VIDEO_CAPABILITIES are importable from backend.app.store.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short` | 0 | 15 passed | 7960ms |
| 2 | `python3 -c "from backend.app.store import materialize_video_package, build_video_job_handoff, VIDEO_CAPABILITIES; print('Import OK')"` | 0 | Import OK | 450ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `/Users/huijie/DMA/.gsd-worktrees/M001/backend/app/store.py`
