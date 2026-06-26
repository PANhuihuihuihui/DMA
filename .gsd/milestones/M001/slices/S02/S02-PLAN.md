# S02: Frontend Generation Client and Job Status UI

**Goal:** npm run build succeeds and the AI Studio generation flow works end-to-end in the browser: model catalog loads, a video job can be submitted, async status polls until resolved, and the job result is visible in the job list.
**Demo:** npm run build succeeds without import errors. AI Studio → Create New → Short Ad Video submits a job and shows async status (queued/running with spinner). Polling advances to succeeded or failed with appropriate UI feedback.

## Must-Haves

- npm run build exits 0. GET /api/v1/generation/models returns Sora 2 and HeyGen models in the browser. A Short Ad Video job can be submitted and its status transitions from queued → running → succeeded/failed are reflected in the UI without page reload.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Created src/api/generationClient.js with all required generation API client functions** `est:30m`
  Create the generation API client module. Exports: loadGenerationModels(), loadGenerationCredits(), loadGenerationJobs(), launchGenerationJob(payload), retryGenerationJob(jobId). Mirror the requestJson/parseJson pattern from publishingClient.js. All endpoints are under /api/v1/generation/.
  - Files: `src/api/generationClient.js`
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && node --input-type=module < src/api/generationClient.js && echo ok

- [x] **T02: Created src/models/generation.js with defensive normalizers for generation models, jobs, and credit summaries.** `est:30m`
  Create the generation model normalizer. Exports: normalizeGenerationCatalog(payload), normalizeCreditSummary(credits), normalizeGenerationJob(job), normalizeGenerationJobsList(payload). Mirror the defensive text()/number()/asArray()/asObject() pattern from models/publishing.js. normalizeGenerationJob must carry capability, workflowType, carouselStage, completedSlides, and outputs fields used by main.jsx derived state.
  - Files: `src/models/generation.js`
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && node --input-type=module < src/models/generation.js && echo ok

- [x] **T03: Added async job polling useEffect with exponential backoff to track long-running generation jobs** `est:45m`
  Add a useEffect in AppDemo that polls GET /api/v1/generation/jobs while genActiveJobs.length > 0. Use exponential backoff: start at 3s, double each tick up to 30s cap, reset to 3s when a new job becomes active. On each tick call reloadGenerationWorkspace(). Clean up the interval/timeout on unmount and when genActiveJobs drops to zero. This is the only place long-running video jobs surface their status in the UI.
  - Files: `src/main.jsx`
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && grep -n 'genActiveJobs' src/main.jsx | grep -q useEffect && echo polling-wired

- [x] **T04: Vite build passes clean with all three new S02 modules integrated (57 modules, no errors)** `est:20m`
  Run npm run build to confirm the build passes with all three new modules in place. Then run the dev server and use curl/node to hit the generation endpoints to confirm the frontend bundle loads correctly and the API routes are reachable.
  - Verify: cd /Users/huijie/DMA/.gsd-worktrees/M001 && npm run build 2>&1 | tail -5

## Files Likely Touched

- src/api/generationClient.js
- src/models/generation.js
- src/main.jsx
