# S03: Creative Editor Handoff and Owner Approval — UAT

**Milestone:** M001
**Written:** 2026-06-26T03:32:18.622Z

## UAT Type

- UAT mode: browser-executable with runtime-executable backend verification
- Why this mode is sufficient: Video job success triggers database-backed materialization (testable via pytest) and creative appears in frontend state; browser can navigate and verify UI, but approval feedback persistence is backend-driven so we verify both layers

## Preconditions

- Backend: `cd /Users/huijie/DMA/.gsd-worktrees/M001 && python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short` passes with 18 tests
- Frontend: `npm run build` succeeds without errors
- Dev server: `npm run dev` started, listening on http://127.0.0.1:5173

## Smoke Test

1. Run backend tests: `python3 -m pytest backend/tests/test_generation_dispatch.py::VideoPackageHandoffTest -q` — all three tests pass, confirming generated_creative creation on video job success
2. Build frontend: `npm run build` — zero errors, all video symbols present
3. Start dev server: `npm run dev`
4. Navigate to http://127.0.0.1:5173/app, log in, select a module, submit a Short Ad Video job
5. Wait for job to succeed and appear in "Generated videos" output section
6. Click "Open in Creative Editor" — video opens in library detail modal with player
7. Click "Approve video" — toast confirms feedback persisted
8. Refresh page — approval state remains visible in the modal

## Test Cases

### 1. Video job materialization creates generated_creative record

1. Backend: call `_dispatch_job` with MockVideoSuccessAdapter for openai:video capability
2. `materialize_video_package` executes on success
3. **Expected:** Query `generated_creatives` by creativeId from serialize_generation_job output — row exists with status='needs_review', platform='facebook', format='short_video', created media asset with asset_type='video'

### 2. UGC video job materializes with correct format

1. Backend: call `_dispatch_job` with MockUgcVideoSuccessAdapter for avatar_video capability
2. `materialize_video_package` executes with capability='avatar_video'
3. **Expected:** Generated creative has format='ugc_video' and media asset exists

### 3. Frontend video output section renders for succeeded jobs

1. Frontend: AppDemo with genSucceededJobs containing workflowType='video' entries
2. Render AI Studio output area
3. **Expected:** "Generated videos" heading visible, one article card per video job with thumbnail, model name, prompt preview, and "Open in Creative Editor" button

### 4. Video opens in Creative Editor with player

1. Click "Open in Creative Editor" on a video job card
2. Library detail modal opens with selectedPost = creativeId
3. **Expected:** Video player renders with <video> tag, controls visible, poster image (if different from storageRef) displayed

### 5. Approval buttons persist feedback

1. Video open in library detail modal
2. Click "Approve video"
3. **Expected:** Toast shows "Approval saved", approvalFeedback entry created in DB, button disabled during pending state
4. Click "Request changes"
5. **Expected:** Toast shows feedback persisted, backend DB updated

### 6. Approval state persists after page refresh

1. Video approved in library detail modal
2. Refresh page (F5)
3. Navigate back to same video in library detail
4. **Expected:** Approval state still visible, no re-approval possible (button conditional on prior state)

## Edge Cases

### Video job with no output rows

1. Backend: dispatch video job that produces no output_rows
2. **Expected:** materialize_video_package guarded by `if first_row is not None` — no crash, job settled with status=succeeded

### Multiple video jobs in output section

1. Frontend: AppDemo with 3 succeeded video jobs (mix of short_video and ugc_video)
2. **Expected:** All three render in order, each with correct thumbnail and capability label, each button independently callable

### Non-video creative in library modal

1. Frontend: library detail modal showing a carousel creative (assetType != 'video')
2. **Expected:** Approval buttons hidden (conditional on assetType === 'video')

## Failure Signals

- Backend test `test_dispatch_video_job_creates_generated_creative` fails — materialization not called on success
- Backend test `test_video_creative_has_video_media_asset` fails — media asset not created or format wrong
- `npm run build` errors or warnings
- Video output section missing in AI Studio ("Generated videos" heading not rendered)
- Video player missing in library modal when video creative selected
- Approval buttons not visible or not callable
- Approval feedback not persisted after page refresh

## Not Proven By This UAT

- Real Sora 2 video generation (deferred to S04 smoke test with real provider)
- Real HeyGen UGC video generation (deferred to S04)
- Credit cost validation and job submission blocking on insufficient balance (S04)
- End-to-end user flow with multiple approval rounds (S04 integration)
- Platform-specific publish flow after approval (post-milestone close-out)
- Analytics / feedback loop from published posts to ROI signals (future milestone)
