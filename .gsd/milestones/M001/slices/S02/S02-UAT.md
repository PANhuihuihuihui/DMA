# S02: Frontend Generation Client and Job Status UI — UAT

**Milestone:** M001
**Written:** 2026-06-26T02:58:05.756Z

# S02: Frontend Generation Client and Job Status UI — UAT

## UAT Type

- UAT mode: browser-executable
- Why this mode is sufficient: Generation job submission and status polling are browser-observable workflows; Playwright end-to-end tests or live browser steps are the canonical way to verify async UI updates and user interactions match the spec

## Preconditions

- `npm run dev` running on http://localhost:5173 (or configured dev port)
- Backend `/api/v1/generation/` endpoints responding correctly with mock or real models/jobs
- AI Studio Create New workflow accessible from the app UI

## Smoke Test

Navigate to AI Studio → Create New → Short Ad Video. Verify the model selector displays "Sora 2" and "HeyGen" options without console errors. Submit a job. Verify the job list shows the new job with status "queued". Within 10 seconds, verify status transitions to "running" with a spinner.

## Test Cases

### 1. Model Catalog Loads Without Errors

1. Open http://localhost:5173
2. Click "AI Studio" or navigate to /app
3. Click "Create New"
4. Select "Short Ad Video"
5. **Expected:** Model selector dropdown shows "Sora 2 - Text to Video" and "HeyGen - UGC Avatar" without console errors

### 2. Job Submission Queues Correctly

1. In Short Ad Video form, enter a video prompt (e.g., "30-second ad for a coffee shop")
2. Select "Sora 2" from model dropdown
3. Click "Generate"
4. **Expected:** UI shows "Generating..." or loading state. Job appears in job list with status "queued". No console errors.

### 3. Status Polling Updates UI Without Reload

1. After submitting a job (or using a mocked job from backend)
2. Observe the job list every 3-5 seconds
3. **Expected:** Status transitions from "queued" → "running" (with spinner) → "succeeded" or "failed" without requiring page reload. Polling backoff increases smoothly from 3s to 30s as job completes.

### 4. Failed Job Shows Error State

1. Submit a job or mock a job failure from backend
2. Observe job list as status transitions to "failed"
3. **Expected:** Job shows error state, error message is visible, user can retry or delete the job

### 5. Multiple Concurrent Jobs Poll Independently

1. Submit two generation jobs in rapid succession
2. Observe job list
3. **Expected:** Both jobs appear. Polling updates both independently. Each shows its own status and progress.

## Edge Cases

### Job Takes Longer Than Expected

1. Submit a job. Stop the backend before job completes.
2. Observe polling behavior for 2+ minutes
3. **Expected:** Polling continues up to 30s intervals. No console errors. Backoff does not exceed 30s.

### Network Error During Polling

1. Submit a job. Simulate network failure (browser devtools Network tab, disable internet briefly, or mock 500 error)
2. Observe job list
3. **Expected:** Polling continues/retries. Job status is either stale or shows a transient error indicator. No infinite error loops or console crashes.

### Rapid Job Submission Resets Backoff

1. Submit job A. Wait 20 seconds (backoff is ~12s).
2. Submit job B.
3. **Expected:** Polling interval resets to 3s for the new job. No skipped polls.

## Failure Signals

- Console shows `TypeError` or `SyntaxError` when loading the page
- Model dropdown is empty or shows undefined values
- Job submitted but does not appear in job list within 5 seconds
- Status never transitions from "queued" after 60 seconds
- Polling generates infinite network requests (more than one per 3-30s range)
- Job list UI locks or becomes unresponsive

## Not Proven By This UAT

- Integration with Creative Editor (S03 scope)
- Owner approval workflow
- Credit cost validation or balance checks
- Real Sora 2 or HeyGen provider responses (integration smoke is S04)
- Retry job functionality (deferred to S03)
- Persistent job state across page reloads (state management scope)
