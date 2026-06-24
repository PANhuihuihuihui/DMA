---
phase: 03-local-campaign-draft-workbench
plan: 03-01
status: partial
completed: 2026-06-18
execution_mode: gsd-execute-phase-inline
---

# 03-01 Execution Summary: Predis Replica Demo Surface

## Completed This Pass

- Reframed the post-login app navigation around the nine Phase 3 Predis-parity surfaces:
  - Dashboard
  - Brand Kit
  - AI Generator
  - Creative Editor
  - Content Calendar
  - Approval Queue
  - Connected Accounts
  - Competitor Ideas
  - Proof Loop
- Added a visible Predis-style parity map that distinguishes:
  - Facebook as the live OAuth adapter
  - TikTok, Instagram, and Google Business Profile as assisted outputs
  - LinkedIn/X/Pinterest as parity placeholders, not live integrations
- Added Brand Kit demo surface with local business profile, voice rules, approved/avoid phrases, colors, and example calibration.
- Added Creative Editor demo surface with static post, carousel, reel/script, caption, hashtag, proof hook, and approval actions.
- Added Approval Queue with exact-version approval actions and approve-all-safe flow using the existing backend approval API.
- Added Connected Accounts screen that reinforces clickable OAuth and explicitly rejects user-pasted access tokens.
- Added Competitor Ideas screen with demo idea cards, hooks, timing, and hashtag clusters.
- Reworked Proof Loop screen around lower-bound measurable response evidence, not exact ROI.
- Fixed business type normalization so the Aurora Heating & Cooling backend profile maps to the HVAC demo template.
- Preserved existing backend approval, fake publish, Facebook OAuth, and live Facebook publish boundaries.

## Completed Backend Slice

- Added backend-owned Phase 3 tables for:
  - `brand_kits`
  - `content_batches`
  - `generated_creatives`
  - `calendar_slots`
  - `proof_links`
  - `proof_events`
  - `competitor_sources`
  - `competitor_ideas`
- Added seeded Aurora Heating & Cooling brand kit, generated creatives, calendar slots, proof links, competitor source, competitor ideas, and proof events.
- Added API routes:
  - `GET /api/v1/phase3/workspace`
  - `PATCH /api/v1/phase3/brand-kit`
  - `POST /api/v1/phase3/content-batches`
  - `POST /api/v1/phase3/competitor-sources`
  - `POST /api/v1/phase3/proof-events`
  - `PATCH /api/v1/phase3/creatives/:id`
  - `PATCH /api/v1/phase3/calendar-slots/:id`
- Wired frontend Brand Kit, AI Generator, Creative Editor, Content Calendar, Competitor Ideas, and Proof Loop screens to the Phase 3 API.
- Added backend tests for seeded workspace records, content batch generation, competitor source analysis, proof event persistence, brand-kit updates, creative edits, and calendar rescheduling.
- Added public Predis audit: `.planning/phases/03-local-campaign-draft-workbench/03-PREDIS-PUBLIC-AUDIT.md`.
- Added committed Playwright smoke coverage for all nine Phase 3 screens in `scripts/smoke-phase3-screens.mjs`.
- Added `npm run test:phase3-screens` and included it in `npm test`.
- Made the Vite API proxy configurable through `LOCALPILOT_API_URL` so screen tests can boot isolated temporary API and web servers.
- Replaced the Competitor Ideas toast-only form with backend-owned competitor source analysis:
  - saves a competitor source label and URL
  - validates HTTP/HTTPS URLs
  - generates three deterministic local-business idea cards
  - refreshes usage metering and screen state immediately
- Added backend-owned media/storyboard assets for generated creatives:
  - Facebook static social post asset plans
  - Instagram carousel storyboard assets
  - TikTok vertical video storyboard assets
  - Google Business Profile update image assets
  - generated media asset usage metering
  - Creative Editor media asset panel with prompts, aspect ratios, storage refs, and storyboard highlights
- Added backend-owned media editing and resize variants:
  - `PATCH /api/v1/phase3/media-assets/:id` persists layer-edit notes and edited preview status
  - `POST /api/v1/phase3/media-assets/:id/variants` creates resized media variant records
  - Creative Editor now exposes `Save layer edit` and `Create resize variant`
- Added backend-owned rendered preview outputs:
  - `POST /api/v1/phase3/media-assets/:id/render` creates deterministic SVG preview/export artifacts
  - rendered outputs are serialized under each Creative Editor media asset
  - Creative Editor now exposes `Render preview` and shows inline preview cards with mime type, status, and storage refs
- Added structured Creative Editor layer controls:
  - backend normalizes `editableLayers` into visible `layerControls`
  - `PATCH /api/v1/phase3/media-assets/:id` accepts structured layer-control updates and preserves edit history
  - rendered previews now apply edited headline, CTA/body, and brand-color layer controls where present
  - Creative Editor now exposes per-layer `Apply layer edit` actions
- Added backend-owned template import and asset library parity:
  - new tables: `creative_templates`, `asset_library_items`, `imported_templates`
  - seeded Canva, Figma, and Adobe Express-style template records
  - seeded premium/local asset library records for the Aurora HVAC demo
  - `POST /api/v1/phase3/template-imports` applies a template and asset item to a generated creative
  - Creative Editor now exposes a template import and premium asset library panel
- Added backend-owned performance analytics parity:
  - new tables: `performance_snapshots` and `analytics_insights`
  - seeded deterministic channel performance for Facebook, Instagram, TikTok, and Google Business Profile
  - `GET /api/v1/phase3/workspace` now serializes `performanceSnapshots`, `analyticsInsights`, and `analyticsSummary`
  - Proof Loop now shows a performance analytics dashboard with impressions, engagement, clicks, leads, lower-bound observable value, confidence, and recommendations
- Added backend-owned approval feedback loop parity:
  - new tables: `approval_review_links` and `approval_feedback`
  - seeded deterministic share-review links and feedback comments for the Aurora HVAC demo
  - `GET /api/v1/phase3/workspace` now serializes `approvalReviewLinks`, `approvalFeedback`, `reviewLink`, and nested creative feedback
  - `POST /api/v1/phase3/approval-feedback` appends approval notes, change requests, and internal notes
  - Approval Queue cards now expose share review links, recent feedback, `Add approval note`, and backend-backed `Request changes`
- Added working public review-route parity:
  - review links now point to local `/review/:token` app routes instead of placeholder external URLs
  - `GET /api/v1/reviews/:token` returns a scoped creative review package
  - `POST /api/v1/reviews/:token` submits approval notes or change requests from the public review page
  - React route `/review/:token` renders creative preview, brand colors, schedule/proof hook, feedback history, and review actions
- Added backend-owned review-link notification parity:
  - new table: `review_notifications`
  - seeded deterministic Aurora HVAC review notification history
  - `POST /api/v1/phase3/review-notifications` creates demo-safe `sent_demo` outbox records
  - `GET /api/v1/phase3/workspace` now serializes top-level and per-creative `reviewNotifications`
  - Approval Queue cards now show last-sent status and expose `Send review link`
- Added backend-owned source URL import parity for the AI Generator:
  - new table: `content_sources`
  - seeded deterministic Aurora HVAC offer source
  - `POST /api/v1/phase3/content-sources` imports and validates HTTP/HTTPS source URLs
  - `GET /api/v1/phase3/workspace` now serializes `contentSources`
  - AI Generator now exposes source URL import, saved source cards, extracted demo briefs, and `Generate from source`
- Added backend-owned image source import parity for the AI Generator:
  - `POST /api/v1/phase3/content-sources` also accepts `sourceType: image` with a bounded demo image preview
  - imported image records persist metadata, mime type, preview data URL, storage ref, and a deterministic visual brief
  - AI Generator now exposes image upload, selected image preview, saved image source cards, thumbnails, and `Generate from source`
- Added backend-owned Idea Lab scoring parity for Creative Editor:
  - new table: `creative_idea_variants`
  - `POST /api/v1/phase3/creatives/:id/idea-variants` generates deterministic AI-scored messaging variations
  - `POST /api/v1/phase3/idea-variants/:id/apply` applies a winning variant back to the backend creative
  - generated creatives now serialize nested `ideaVariants`
  - Creative Editor now exposes Idea Labs score cards, rationale, statuses, and `Apply winner`
- Added backend-owned AI Assistant reply parity for AI Generator:
  - new table: `ai_assistant_replies`
  - `POST /api/v1/phase3/ai-assistant/replies` saves assistant replies for post ideas and calendar outlines
  - `POST /api/v1/phase3/ai-assistant/replies/:id/content-batch` creates generated posts from a saved reply
  - `GET /api/v1/phase3/workspace` now serializes `aiAssistantReplies`
  - AI Generator now exposes assistant prompt, saved replies, outline bullets, and `Create posts from reply`
- Added backend-owned multilingual creative variant parity for Creative Editor:
  - new table: `creative_language_variants`
  - `POST /api/v1/phase3/creatives/:id/language-variants` creates localized copy records
  - generated creatives now serialize nested `languageVariants`
  - Creative Editor now exposes `Multilingual variants`, English/Spanish/Chinese cards, localized CTAs, hashtags, and status
- Added backend-owned layer layout controls for closer Creative Editor parity:
  - `POST /api/v1/phase3/media-assets/:id/layer-layout` moves/repositions a selected media layer
  - media asset layer controls now serialize layout metadata including order, x/y, width, height, and rotation
  - Creative Editor now exposes `Move layer`, layer order, and position metadata alongside text/style edits
- Added backend-owned bulk creative variation parity for Creative Editor:
  - new table: `creative_bulk_variants`
  - `POST /api/v1/phase3/creatives/:id/bulk-variations` creates ready-to-test hook/copy/visual-direction cards
  - generated creatives now serialize nested `bulkVariants`
  - Creative Editor now exposes `Bulk variations`, test scores, formats, and visual directions
- Added backend-owned UGC voiceover package parity for Creative Editor:
  - new table: `creative_ugc_packages`
  - `POST /api/v1/phase3/creatives/:id/ugc-voiceover-package` creates storyboard-ready avatar/video-with-voiceover packages
  - generated creatives now serialize nested `ugcVoiceoverPackages`
  - Creative Editor now exposes `UGC voiceover`, avatar guidance, voiceover direction, scene beats, and 9:16 1080x1920 export specs

## Verification

- `npm test`
- `npm run build`
- `npm run test:storage-boundary`
- `npm run test:phase3`
- `npm run test:phase3-screens`
- Browser smoke through Playwright:
  - loaded `/app?module=dashboard`
  - verified 9 navigation items
  - verified Dashboard usage/credits strip
  - generated a backend weekly batch from AI Generator
  - imported a source URL in AI Generator and generated a backend weekly batch from the saved source
  - uploaded a source image in AI Generator and generated a backend weekly batch from the saved image source
  - asked the backend AI Assistant for a content calendar reply and created posts from that reply
  - generated AI-scored Idea Lab variants and applied a winner to a backend creative
  - generated bulk creative variations with hook, copy, visual direction, and format cards
  - generated a storyboard-ready UGC voiceover/avatar package with scene beats and export specs
  - generated multilingual English, Spanish, and Chinese creative variants from a backend creative
  - moved a Creative Editor layer layout and verified `layout_adjusted` status
  - verified Creative Editor template imports, asset library, media/storyboard assets, structured layer controls, resize variants, and rendered previews
  - opened Creative Editor and persisted a backend edit
  - opened Content Calendar and persisted a backend reschedule
  - verified Approval Queue review links, notification outbox, public review route, feedback loop, Connected Accounts, backend Competitor Ideas analysis, and Proof Loop
  - verified Performance analytics dashboard and Proof Loop event recording
  - verified no console errors during smoke

## Browser Smoke Evidence

Observed:

- Navigation: Dashboard, Brand Kit, AI Generator, Creative Editor, Content Calendar, Approval Queue, Connected Accounts, Competitor Ideas, Proof Loop.
- Dashboard usage strip: plan, credits used, brands, social accounts, competitor runs.
- AI Generator: 8 output cards after backend weekly-batch generation; source URL import added an `analyzed_demo` source card; source image import added an `analyzed_demo image` card with thumbnail; `Generate from source` completed for both source types without console/page errors.
- AI Generator: assistant replies saved as backend records, displayed outline bullets, and `Create posts from reply` converted a reply to generated posts.
- Creative Editor: Idea Labs generated scored variants, displayed AI score/rationale cards, and applied a winning variant back to the backend creative.
- Creative Editor: bulk variation generation created ready-to-test hook/copy/visual-direction records.
- Creative Editor: UGC voiceover package generation created a storyboard-ready avatar/video-with-voiceover package with scene beats and 1080x1920 export specs.
- Creative Editor: multilingual variants generated English, Spanish, and Chinese localized copy records with `localized` status.
- Creative Editor: layer layout controls displayed layer order/position and `Move layer` persisted a `layout_adjusted` backend media asset state.
- Creative Editor: template import panel displayed Canva/Figma/Adobe-style templates and premium asset library items; import action applied a backend template and changed the media asset to `template_applied`; generated media/storyboard assets rendered with backend storage refs; structured layer controls displayed editable elements; layer edit changed the asset to `edited_preview`; resize action added a variant card; render action added a `rendered_preview` output with a `localpilot-rendered` storage ref.
- Creative Editor: backend edit saved and reflected in the visible caption.
- Content Calendar: backend reschedule action available and completed without console/page errors.
- Approval Queue: share review links rendered; `Send review link` created a backend `sent_demo` notification; `Add approval note` persisted feedback and reflected it on the card; generated review links opened `/review/:token` and accepted public-page feedback.
- Competitor Ideas: backend analysis added a saved source and increased idea cards from 3 to 6.
- Proof Loop: performance analytics dashboard showed lower-bound value, attribution mode, and top local response insights; demo event recording route exercised.

## Remaining Work

This execution creates the customer-demo surface and adds backend persistence for the core Phase 3 records, but the full Phase 3 plan is not yet production-complete. Remaining hardening:

- Replace deterministic competitor demo generation with real ingestion when an official/social API path is available.
- Add a Predis in-app screenshot audit if the user provides login access.
- Add live Canva/Figma/Adobe import, full drag/drop template editing, and production rendered media/video generation beyond deterministic local SVG preview artifacts.
- Replace deterministic analytics snapshots with official platform analytics ingestion and connect phone/booking/POS evidence before stronger ROI claims.
- Harden public review routes and notifications with signed tokens, expiration, access control, rate limiting, provider delivery, webhooks, and notification audit trails.
- Expand real publishing adapters beyond Facebook OAuth Page publishing.
- Replace the demo-only Facebook token vault with encrypted or secret-managed persistence before production.

## Next Action

Run the next Phase 3 execution slice for closer Predis parity:

1. logged-in Predis screen audit and screenshot checklist
2. true competitor ingestion using official/social APIs
3. production rendered media/video generation path
4. live template imports, asset library provider integrations, and deeper drag/drop creative editor controls
5. production-grade token persistence hardening
