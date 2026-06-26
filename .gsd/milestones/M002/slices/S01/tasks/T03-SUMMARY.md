---
id: T03
parent: S01
milestone: M002
key_files:
  - backend/app/store.py
  - backend/app/server.py
  - src/api/publishingClient.js
  - src/main.jsx
key_decisions:
  - Omit updated_at from UPDATE media_assets — the table schema has no updated_at column; the plan incorrectly mentioned it
  - Derive genImageOutputs by flatMapping job.outputs filtered by outputKind==='image' across all succeeded jobs (not workflowType filter) to catch any image output regardless of whether workflowType was set
  - Guard 'Use for Facebook post' button on facebookDraft presence — button renders only when a facebook platform draft exists in workflow.platformDrafts
duration: 
verification_result: passed
completed_at: 2026-06-26T06:42:18.771Z
blocker_discovered: false
---

# T03: Wired AI Studio image generation outputs to Facebook draft media ref via new store function, POST /drafts/{id}/media endpoint, attachGenerationOutputToDraft client, and "Use for Facebook post" button in AI Studio

**Wired AI Studio image generation outputs to Facebook draft media ref via new store function, POST /drafts/{id}/media endpoint, attachGenerationOutputToDraft client, and "Use for Facebook post" button in AI Studio**

## What Happened

Added the full vertical slice connecting AI Studio image outputs to platform draft media assets:

1. **store.py** — Added `_mime_type_from_url(url)` helper that deduces image MIME type from URL extension (PNG/GIF/WebP/JPEG fallback), and `patch_draft_media_ref(conn, draft_id, generation_output_id)` that: looks up the generation_outputs row by ID (StoreError 404 if missing), validates storage_ref starts with http/https (StoreError 400 with 'Image URL must be publicly accessible for Facebook publishing' if not), fetches the current draft version, calls `get_media_assets_for_version`, then either UPDATEs the first existing media asset row's storage_ref/kind/storage_mode or INSERTs a new media_assets row with the image URL. Returns `get_serialized_draft`.

2. **server.py** — Added a `draft_action['action'] == 'media'` branch after the existing approve branch in `route_request`. Calls `store.patch_draft_media_ref` with `generationOutputId` from the POST body, responds 201.

3. **publishingClient.js** — Exported `attachGenerationOutputToDraft(draftId, generationOutputId)` that POSTs to `/drafts/{draftId}/media` with `{generationOutputId}`.

4. **main.jsx** — Imported `attachGenerationOutputToDraft`; added `genAttachPending` state; added `handleAttachToDraft(draftId, outputId)` handler that calls the client, reloads the workflow silently, and shows a toast; added `facebookDraft` and `genImageOutputs` derived values; added a "Generated images" section in AI Studio that renders each image output (with thumbnail and prompt snippet) and a "Use for Facebook post" button that fires when `facebookDraft` is present.

Deviation from plan: The `media_assets` table has no `updated_at` column (plan mentioned setting it on UPDATE) — adapted the UPDATE statement to omit it.

## Verification

grep -q 'attachGenerationOutputToDraft' src/api/publishingClient.js (exit 0); grep -q 'def patch_draft_media_ref' backend/app/store.py (exit 0); grep -q 'draft_action\\[\"action\"\\] == \"media\"' backend/app/server.py (exit 0); grep -q 'Use for Facebook post' src/main.jsx (exit 0); npm run build (exit 0, built in 1.08s)

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -q 'attachGenerationOutputToDraft' src/api/publishingClient.js` | 0 | PASS | 10ms |
| 2 | `grep -q 'def patch_draft_media_ref' backend/app/store.py` | 0 | PASS | 8ms |
| 3 | `grep -q 'Image URL must be publicly accessible' backend/app/store.py` | 0 | PASS | 8ms |
| 4 | `grep -q 'draft_action.*action.*media' backend/app/server.py` | 0 | PASS | 8ms |
| 5 | `grep -q 'Use for Facebook post' src/main.jsx` | 0 | PASS | 8ms |
| 6 | `npm run build` | 0 | PASS - built in 1.08s, no errors | 1440ms |

## Deviations

media_assets table has no updated_at column — adapted UPDATE to omit it (plan incorrectly mentioned setting updated_at=utc_now())

## Known Issues

None.

## Files Created/Modified

- `backend/app/store.py`
- `backend/app/server.py`
- `src/api/publishingClient.js`
- `src/main.jsx`
