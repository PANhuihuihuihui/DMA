---
estimated_steps: 7
estimated_files: 1
skills_used: []
---

# T01: Added VIDEO_CAPABILITIES constant, materialize_video_package, and build_video_job_handoff to store.py, and wired build_video_job_handoff into serialize_generation_job.

Why: Carousel jobs call materialize_carousel_package on success to create a generated_creative; video jobs need the same pattern so they surface in the Content Library and can be approved.

Do:
1. Add constant VIDEO_CAPABILITIES = frozenset({"video", "avatar_video"}) near CAROUSEL_WORKFLOW_TYPE.
2. Add materialize_video_package(conn, merchant_id, job_row, output_row): determine format from job_row["capability"] ("ugc_video" for avatar_video, "short_video" for video); create content_batches row; create generated_creatives row (platform="facebook", format derived above, title from job_row["prompt"][:180], status="needs_review"); create calendar_slots row; create proof_links row with code SHORTV-{creative_id[-6:].upper()}; create creative_media_assets row (asset_type="video", format="9:16 short video", aspect_ratio="9:16", storage_ref=output_row["storage_ref"], prompt=job_row["prompt"], provider=job_row["provider_key"]); update generation_outputs metadata_json to include {"creativeId": creative_id, "mediaAssetId": asset_id}; call ensure_review_link_for_creative; return {"creativeId": creative_id, "mediaAssetId": asset_id}.
3. Add build_video_job_handoff(outputs, request_payload): find first output where isinstance(o.get("metadata"), dict) and o["metadata"].get("creativeId"); if found return {"workflowType": "video", "creativeId": that creative_id}; else return {}.
4. In serialize_generation_job: after payload.update(build_carousel_job_handoff(outputs, request_payload)) add payload.update(build_video_job_handoff(outputs, request_payload)).

Done when: python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short exits 0 (existing tests still pass); materialize_video_package and build_video_job_handoff are importable from backend.app.store.

## Inputs

- `backend/app/store.py`

## Expected Output

- `backend/app/store.py`

## Verification

python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short

## Observability Impact

materialize_video_package logs generated_creative id at INFO; build_video_job_handoff is a pure function with no side effects
