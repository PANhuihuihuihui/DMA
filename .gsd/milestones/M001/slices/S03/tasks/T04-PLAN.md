---
estimated_steps: 8
estimated_files: 2
skills_used: []
---

# T04: Added openVideoEditor function, video output section in AI Studio, video player in library detail modal, and approval buttons for video creatives.

Why: The backend now creates generated_creatives for video jobs, but the AI Studio has no output section for video (only carousel), the Creative Editor cannot render video assets, and there are no approval buttons in the library detail modal.

Do:
1. In AppDemo in src/main.jsx, add openVideoEditor(creativeId) function mirroring openCarouselEditor: reload phase3 workspace, find creative index by creativeId, setSelectedPost(creativeIndex), setLibraryDetailCreativeId(creativeId), selectModule("Content Library"), showAppToast("Video opened in Creative Editor.").
2. After the carousel outputs section (starting around line 8700 where carouselJobs.filter(...succeeded...) is rendered), add a video outputs section: const genVideoJobs = genSucceededJobs.filter(j => j.workflowType === "video"); if genVideoJobs.length > 0 render a section with heading "Generated videos" and one article card per job showing a video thumbnail (job.outputs[0]?.previewRef as <img> with alt), model name, prompt preview, and a "Open in Creative Editor" button disabled when !job.creativeId that calls openVideoEditor(job.creativeId).
3. In the job detail drawer (around line 8775), extend the carousel check: add a similar block for video jobs using detailJob.workflowType === "video" && detailJob.creativeId.
4. In the library-detail-modal (around line 9492): check const isVideoCreative = libraryDetailMediaAsset?.assetType === "video"; if isVideoCreative render <video className="library-detail-video" src={libraryDetailMediaAsset.storageRef} controls poster={libraryDetailMediaAsset.storageRef !== libraryDetailPreviewImage ? libraryDetailPreviewImage || undefined : undefined} /> inside the preview container instead of relying solely on the background-image style; in library-detail-actions, add two buttons: "Approve video" (disabled when approvalFeedbackPending includes libraryDetailCreative.id, calls addApprovalFeedback(libraryDetailIndex, "approval_note")) and "Request changes" (calls addApprovalFeedback(libraryDetailIndex, "change_request")).
5. In src/styles.css, add .library-detail-video { width: 100%; height: 100%; object-fit: cover; border-radius: inherit; } and .gen-video-output-card { display: flex; flex-direction: column; gap: var(--gap, 0.75rem); } and .gen-video-thumb { width: 100%; aspect-ratio: 9/16; object-fit: cover; border-radius: 6px; background: var(--wash); }.

Done when: npm run build exits 0 with no errors; openVideoEditor, the video output section, video player in library detail modal, and approval buttons are all present in the built output.

## Inputs

- `src/main.jsx`
- `src/styles.css`
- `src/api/generationClient.js`
- `src/models/generation.js`

## Expected Output

- `src/main.jsx`
- `src/styles.css`

## Verification

npm run build
