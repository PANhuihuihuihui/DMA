# S03: Creative Editor Handoff and Owner Approval

**Goal:** Succeeded text-to-video and UGC avatar video jobs open in the Creative Editor as owner-approvable packages. Merchant uses the existing approve/request-changes surface to provide feedback, and approval state persists through page refresh via backend-stored phase3 creative feedback.
**Demo:** A succeeded video job opens in the Creative Editor as an approvable package. Merchant can approve or request changes. The approval state persists through page refresh.

## Must-Haves

- A video generation job with capability "video" or "avatar_video" that succeeds creates a generated_creative record with the video URL as a creative_media_asset. serialize_generation_job returns workflowType "video" and creativeId for succeeded video jobs. AI Studio shows succeeded video jobs with a thumbnail preview and "Open in Creative Editor" button. Clicking that button opens the library-detail modal with a video player. Approve and Request changes buttons in the modal call addApprovalFeedback which persists to the DB. npm run build succeeds; pytest test_generation_dispatch.py -q passes including new video materialization tests.

## Proof Level

- This slice proves: integration — real dispatch engine tested with mock adapters; frontend build verified statically; no real provider calls required in this slice

## Integration Closure

Upstream: generation_dispatch._dispatch_job (S01), store.serialize_generation_job (S01), generationClient.loadGenerationJobs (S02), polling useEffect (S02), phase3Workspace.generatedCreatives (existing Content Library), addApprovalFeedback/createPhase3ApprovalFeedback (existing). New wiring: materialize_video_package called from both dispatch paths on video job success → generated_creative created → appears in phase3Workspace → openVideoEditor → Content Library modal. Remaining before milestone end-to-end: S04 real provider smoke against Sora 2 + HeyGen with real credits.

## Verification

- Backend logs video creative materialization at INFO level per job. Frontend approval toast confirms feedback persisted. Creative approvalFeedback visible in library-detail modal. Job detail drawer shows creativeId for inspecting DB linkage.

## Tasks

- [x] **T01: Added VIDEO_CAPABILITIES constant, materialize_video_package, and build_video_job_handoff to store.py, and wired build_video_job_handoff into serialize_generation_job.** `est:1.5h`
  Why: Carousel jobs call materialize_carousel_package on success to create a generated_creative; video jobs need the same pattern so they surface in the Content Library and can be approved.
  - Files: `backend/app/store.py`
  - Verify: python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short

- [x] **T02: Wired materialize_video_package into both _dispatch_job (async) and dispatch_generation_job (sync) succeeded branches so video jobs produce a generated_creative record on success.** `est:45m`
  Why: store.py now has the function but nothing calls it from the dispatch engine; without wiring, no creative is created when a video job succeeds.
  - Files: `backend/app/generation_dispatch.py`
  - Verify: python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short

- [x] **T03: Added MockVideoSuccessAdapter, MockUgcVideoSuccessAdapter, and VideoPackageHandoffTest with 3 tests asserting generated_creative creation, ugc_video format, and video media asset after dispatch** `est:45m`
  Why: T01 and T02 add the store function and dispatch wiring but the existing tests only verify credits and lifecycle; we need tests that assert a generated_creative is created and creativeId appears in the serialized job.
  - Files: `backend/tests/test_generation_dispatch.py`
  - Verify: python3 -m pytest backend/tests/test_generation_dispatch.py -q --tb=short

- [x] **T04: Added openVideoEditor function, video output section in AI Studio, video player in library detail modal, and approval buttons for video creatives.** `est:1.5h`
  Why: The backend now creates generated_creatives for video jobs, but the AI Studio has no output section for video (only carousel), the Creative Editor cannot render video assets, and there are no approval buttons in the library detail modal.
  - Files: `src/main.jsx`, `src/styles.css`
  - Verify: npm run build

## Files Likely Touched

- backend/app/store.py
- backend/app/generation_dispatch.py
- backend/tests/test_generation_dispatch.py
- src/main.jsx
- src/styles.css
