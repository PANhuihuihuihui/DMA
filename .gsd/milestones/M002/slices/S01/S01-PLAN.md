# S01: Backlog placeholder

**Goal:** Complete the remaining Phase 4 frontend integration gaps: wire the split OAuth page-picker flow to the UI, add a manual-fallback next-step hint in the Approval Queue, attach AI Studio image outputs to Facebook drafts, and produce app-review evidence documentation.
**Demo:** Milestone remains registered in the roadmap while detailed slice planning is deferred.

## Must-Haves

- A merchant who completes Facebook OAuth sees the Page picker and can select their Page. When a publish job reaches manual_fallback_required, a next-step hint (and Reconnect CTA for auth errors) renders in the Approval Queue. AI-generated images have a 'Use for Facebook post' action that wires the image URL into the draft media ref. App review documentation is complete with permissions, test setup, and walkthrough steps.

## Proof Level

- This slice proves: Integration — T01 and T03 exercise real OAuth session state machine and DB paths; T02 is frontend UI; T04 is documentation.

## Integration Closure

Upstream surfaces consumed: facebook_oauth.py split callback (complete), facebook_publisher.py at v25.0 with image validation (complete), generation_outputs table. New wiring introduced: connectSession URL param handling in main.jsx; patch_draft_media_ref store function plus POST /api/v1/drafts/{draftId}/media route; manual-fallback-hint block in PublishTimeline.jsx. Nothing remains after T01-T04 — these four tasks complete the Phase 4 scope described in S01-CONTEXT.

## Verification

- Invalid connectSession or expired session surfaces as StoreError 400 → HTTP error → frontend toast (existing pattern). Token auth failures update facebook_page_tokens.status to reconnect_required (existing). Draft media ref attachment errors surface via standard 500 traceback protection. No new log sinks are needed.

## Tasks

- [x] **T01: Wired connectSession URL param to inline Facebook Page picker — real OAuth redirects now trigger page listing and selection** `est:1h`
  Why: Backend split OAuth (D11) is complete — complete_callback redirects to the UI with connectSession param, and list_pages_for_session + select_page routes exist. But the frontend location-change useEffect only handles facebookConnected=1, ignoring connectSession. Merchants cannot complete Page selection after OAuth.
  - Files: `src/main.jsx`
  - Verify: grep -q "connectSession" src/main.jsx

- [x] **T02: Added manual-fallback-hint block with error-class-aware hint text and Reconnect CTA to PublishTimeline; wired onReconnect to Brand & Social Accounts navigation in both call sites** `est:45m`
  Why: PublishTimeline shows the manual_fallback_required status label but provides no actionable guidance. D14 requires a next-step hint with redacted error class. D11 requires a Reconnect CTA when the error class is authentication (token expiry detected on next publish attempt).
  - Files: `src/components/PublishTimeline.jsx`, `src/main.jsx`
  - Verify: grep -q "manual-fallback-hint" src/components/PublishTimeline.jsx

- [x] **T03: Wired AI Studio image generation outputs to Facebook draft media ref via new store function, POST /drafts/{id}/media endpoint, attachGenerationOutputToDraft client, and "Use for Facebook post" button in AI Studio** `est:1h 30m`
  Why: No backend endpoint or frontend action exists to attach an AI Studio image output to a platform draft's mediaRefs. Without this, the D12 single-image Facebook publish path cannot be exercised with AI-generated content. The approve_draft function requires media assets to already exist in the media_assets table for the draft version.
  - Files: `backend/app/store.py`, `backend/app/server.py`, `src/api/publishingClient.js`, `src/main.jsx`
  - Verify: grep -q "attachGenerationOutputToDraft" src/api/publishingClient.js

- [x] **T04: Authored docs/app-review-evidence.md covering Phase 4 Graph API scopes, test-account setup, Page-switching path, full publish walkthrough, and screencast checklist — resolving all three S01-CONTEXT open questions.** `est:30m`
  Why: S01-CONTEXT scope lists 'app review screencast artifact' as an in-scope deliverable. This document records the required permissions, test account setup, full publish flow walkthrough, and screencast instructions needed to produce Meta App Review evidence. The three open questions from S01-CONTEXT are resolved here.
  - Files: `docs/app-review-evidence.md`
  - Verify: test -f docs/app-review-evidence.md

## Files Likely Touched

- src/main.jsx
- src/components/PublishTimeline.jsx
- backend/app/store.py
- backend/app/server.py
- src/api/publishingClient.js
- docs/app-review-evidence.md
