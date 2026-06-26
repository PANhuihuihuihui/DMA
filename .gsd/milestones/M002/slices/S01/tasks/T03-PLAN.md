---
estimated_steps: 14
estimated_files: 4
skills_used: []
---

# T03: Wired AI Studio image generation outputs to Facebook draft media ref via new store function, POST /drafts/{id}/media endpoint, attachGenerationOutputToDraft client, and "Use for Facebook post" button in AI Studio

Why: No backend endpoint or frontend action exists to attach an AI Studio image output to a platform draft's mediaRefs. Without this, the D12 single-image Facebook publish path cannot be exercised with AI-generated content. The approve_draft function requires media assets to already exist in the media_assets table for the draft version.

Do:
1. In store.py, add patch_draft_media_ref(conn, draft_id, generation_output_id) that:
   a. Looks up generation_outputs row by ID; raises StoreError(404) if missing.
   b. Validates output.storage_ref starts with http:// or https:// (rejects base64 data URIs with StoreError 400 'Image URL must be publicly accessible for Facebook publishing').
   c. Gets the current draft version ID from platform_drafts.current_version_id.
   d. Calls get_media_assets_for_version(conn, version_id).
   e. If a media asset row exists (UPDATE): set storage_ref=output.storage_ref, kind='image', storage_mode='url', updated_at=utc_now() where id=existing_row['id'].
   f. If no media asset row exists (INSERT): insert into media_assets with new_id('media'), DEMO_MERCHANT_ID, version_id, storage_mode='url', storage_ref=output.storage_ref, kind='image', mime_type deduced from URL extension, alt_text='', checksum='', created_at and updated_at.
   g. Returns get_serialized_draft(conn, draft_id).
2. In server.py, in route_request after the existing approve action, add: if draft_action and method == 'POST' and draft_action['action'] == 'media': call store.patch_draft_media_ref(conn, draft_action['draft_id'], body.get('generationOutputId')), send_json status 201.
3. In publishingClient.js, add: export const attachGenerationOutputToDraft = (draftId, generationOutputId) => requestJson(`/drafts/${encodeURIComponent(draftId)}/media`, {method:'POST', body: JSON.stringify({generationOutputId})}).
4. In main.jsx, in the AI Studio generation outputs section (search for 'gen-output-grid'), find where image outputs are rendered. Add a 'Use for Facebook post' button for outputs where output.outputKind === 'image' or output.kind === 'image'. On click: call attachGenerationOutputToDraft(facebookDraftId, output.id) where facebookDraftId is the ID of the Facebook platform draft from the workflow; on success reload the workflow; on error show toast.

Done when: POST /api/v1/drafts/{draftId}/media endpoint exists; 'Use for Facebook post' button appears on image generation outputs; clicking it updates the draft's media asset storage_ref.

## Inputs

- `backend/app/store.py`
- `backend/app/server.py`
- `src/api/publishingClient.js`
- `src/main.jsx`

## Expected Output

- `backend/app/store.py`
- `backend/app/server.py`
- `src/api/publishingClient.js`
- `src/main.jsx`

## Verification

grep -q "attachGenerationOutputToDraft" src/api/publishingClient.js
