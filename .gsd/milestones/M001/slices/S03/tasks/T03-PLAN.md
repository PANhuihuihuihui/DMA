---
estimated_steps: 9
estimated_files: 1
skills_used: []
---

# T03: Add pytest tests for video creative materialization

Why: T01 and T02 add the store function and dispatch wiring but the existing tests only verify credits and lifecycle; we need tests that assert a generated_creative is created and creativeId appears in the serialized job.

Do:
1. Add MockVideoSuccessAdapter class (like MockSuccessAdapter) with poll() returning {"status": "succeeded", "outputs": [{"kind": "video", "storageRef": "https://example.com/video.mp4", "previewRef": "https://example.com/thumb.jpg", "metadata": {"providerJobId": "mock_video_job"}}]}.
2. Add VideoPackageHandoffTest(unittest.TestCase) with setUp that calls store.ensure_database(db_path) and uses DEMO_MERCHANT_ID:
   - test_dispatch_video_job_creates_generated_creative: submit a video job (dispatch=False via store.create_generation_job), then call generation_dispatch.dispatch_generation_job with MockVideoSuccessAdapter; assert the returned job has "creativeId" set and "workflowType" == "video"; also query DB to assert a generated_creatives row exists with merchant_id = DEMO_MERCHANT_ID.
   - test_dispatch_ugc_video_job_creates_ugc_creative: same but use CCDANCE_AVATAR_MODEL_ID and MockUgcVideoSuccessAdapter returning kind="avatar_video"; assert format == "ugc_video" in DB.
   - test_video_creative_has_video_media_asset: after dispatch, query creative_media_assets where creative_id = job["creativeId"]; assert asset_type == "video" and storage_ref == "https://example.com/video.mp4".
3. Add MockUgcVideoSuccessAdapter similarly with kind="avatar_video".

Done when: python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short exits 0 with all three new tests passing.

## Inputs

- `backend/tests/test_generation_dispatch.py`
- `backend/app/store.py`
- `backend/app/generation_dispatch.py`

## Expected Output

- `backend/tests/test_generation_dispatch.py`

## Verification

python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short
