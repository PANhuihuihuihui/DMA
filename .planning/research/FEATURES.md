# Feature Landscape

**Project:** LocalPilot AI
**Domain:** Local-business AI marketing operator with real publishing
**Researched:** 2026-06-09
**Scope:** First real publishing MVP, Facebook first and TikTok second. Xiaohongshu is deferred unless a compliant official or partner route is proven.
**Overall confidence:** MEDIUM-HIGH. TikTok requirements are HIGH confidence from official docs. Facebook requirements are MEDIUM because Meta developer docs were partially inaccessible without login or returned rate-limit errors during research; claims should be validated in a Meta developer app before build commitment.

## Recommendation

Build v1 as an owner-approved publishing workbench, not an autonomous scheduler. The first release should let a merchant connect their own Facebook Page and TikTok account, generate platform-native drafts from one offer, validate media and metadata, approve each channel explicitly, submit through an official API path, and track status/errors until the merchant can see whether the post is published, failed, or requires manual completion.

Facebook should ship first because local businesses already use Pages and the content surface can start with simple text/link/image/video Page posts. TikTok should ship second with two modes: Direct Post where app audit, scopes, media, creator settings, and user consent are satisfied; Upload-to-Inbox/Draft as the safer fallback when the owner should finish edits inside TikTok. Xiaohongshu should stay as assisted copy/package export only until a verified official/partner publishing route exists.

## Table Stakes

Missing any of these makes the product feel like a demo rather than a real publishing MVP.

| Feature | Platform | Why Expected | Complexity | Requirement Mapping |
|---------|----------|--------------|------------|---------------------|
| Merchant-owned account connection | Facebook, TikTok | The merchant must publish through their own official Page/account, not a shared LocalPilot identity. | High | `REQ-ACCOUNT-001`: OAuth connection, server-side token storage, page/account selection. |
| Facebook Page selection and eligibility check | Facebook | A merchant may manage multiple Pages; v1 must confirm which Page can publish and why another cannot. | Medium | `REQ-FB-001`: list connected Pages, selected Page ID, Page access token, permission status, publish eligibility. |
| TikTok creator info preflight | TikTok | TikTok Direct Post requires querying latest creator info before export so privacy options and account settings are honored. | Medium | `REQ-TT-001`: fetch creator avatar/name, privacy options, duet/stitch/comment defaults, max video duration. |
| One-offer campaign generator | Both | Core value is one local offer becoming channel-native Facebook and TikTok drafts. | Medium | `REQ-CAMPAIGN-001`: business profile + offer input produce structured platform variants. |
| Platform-native draft editor | Both | Owners need to adjust captions, CTA, hashtags, link, disclosure, and media before approval. | Medium | `REQ-DRAFT-001`: editable per-platform draft with revision history. |
| Explicit owner approval before publish | Both | Trust and compliance require a visible confirmation step before API submission. | Medium | `REQ-APPROVAL-001`: no publish job can start unless a specific variant has `approved_at`, `approved_by`, and frozen payload snapshot. |
| Publishing status timeline | Both | Real posting is asynchronous and can fail after submission; owners need current state and history. | Medium | `REQ-STATUS-001`: draft, needs_review, changes_requested, approved, queued, publishing, upload_processing, moderation_pending, inbox_delivered, published, failed, retry_needed, manually_completed. |
| Error classification and retry | Both | Token expiry, permissions, rate limits, media validation, moderation, and network failures need different owner/admin actions. | High | `REQ-ERROR-001`: normalize platform errors into retryable, user_action_required, media_fix_required, permission_fix_required, and terminal. |
| Media upload and storage | Both | TikTok and video/photo publishing need stable hosted media, not local browser files. | High | `REQ-MEDIA-001`: upload to server/object storage, scan metadata, generate public or signed URLs as required. |
| Media validation before submission | Both | Failed uploads are avoidable if aspect, format, size, duration, URL access, and platform-specific metadata are checked up front. | High | `REQ-MEDIA-002`: per-platform validators block invalid payloads before approval. |
| Post identifier capture | Both | Published content must be linked back to LocalPilot for status, support, and later analytics. | Medium | `REQ-PUBLISH-001`: persist platform post ID, TikTok publish ID, provider response, public URL when available. |
| Account health and reconnect flow | Both | Expired tokens and lost permissions are common; owner needs a clear reconnect path. | Medium | `REQ-ACCOUNT-002`: connection state, last token refresh/check, reconnect CTA, admin diagnostic reason. |
| Assisted/manual fallback package | Both | API access can be blocked by app review, account eligibility, or media constraints; pilot users still need a usable outcome. | Medium | `REQ-FALLBACK-001`: export caption, media, hashtags, CTA, checklist, and manual completion state. |
| Internal admin diagnostics | Both | Early pilots need support visibility without asking merchants to inspect developer consoles. | Medium | `REQ-ADMIN-001`: per-publish job logs, normalized error reason, raw provider log ID/fbtrace ID when available, retry controls. |

## Facebook V1 Features

Prioritize the smallest Page publishing path that proves "idea to published Facebook Page post" works.

| Feature | Include in V1 | Notes |
|---------|---------------|-------|
| Facebook OAuth/account connection | Yes | Request only permissions needed for Page publishing and reading connected Page metadata. Validate in a Business app before final scope names are locked. |
| Page-only publishing | Yes | Do not support personal profile posting. Treat Pages as the production Facebook surface. |
| Text post | Yes | Baseline proof path for a local offer, announcement, event reminder, or service update. |
| Link post | Yes | Needed for booking URLs, menu/order links, coupons, and landing pages. |
| Single image post | Yes | Important for restaurants, salons, clinics, and retail offers. |
| Video post | Maybe in v1.1 | Useful, but should not block text/link/image publishing unless already handled by a reused publishing engine. |
| Scheduled post | Defer unless nearly free | The first proof is approved immediate publishing. Scheduling adds queue and time-zone risk. |
| Reels/Stories | Defer | Higher media/API complexity and less necessary for first Facebook proof. |
| Comments/inbox management | Defer | Valuable later, but publishing foundation comes first. |

Facebook acceptance requirements:

- Owner can connect Facebook and select one Page.
- LocalPilot stores no OAuth secret, user token, or Page token in browser localStorage.
- The connection record shows selected Page name, Page ID, connection state, last checked time, and publish eligibility.
- A draft cannot publish until the owner reviews the exact caption, media, link, and destination Page.
- On success, LocalPilot stores the provider response, platform post ID, public URL when available, and status `published`.
- On failure, LocalPilot stores the normalized reason and the raw provider trace identifier if returned.
- If permissions/app review prevent publishing, the UI falls back to a manual Facebook package with copy, media, link, and checklist.

## TikTok V1 Features

TikTok should follow Facebook, but the data model should be ready from the start because TikTok status and consent requirements are more explicit.

| Feature | Include in V1 | Notes |
|---------|---------------|-------|
| TikTok OAuth/account connection | Yes, after Facebook path is working | Store access/refresh token server-side and track granted scopes. |
| Creator info query | Yes | Required before Direct Post to render current privacy options and creator restrictions. |
| Upload-to-Inbox/Draft mode | Yes | Safer first TikTok mode because the creator completes posting inside TikTok. |
| Direct Post mode | Conditional | Enable only after app audit/scope approval and explicit owner consent UX are complete. |
| Video post | Yes | Core TikTok format; validate format, size, duration, URL access, chunking/public URL transfer requirements. |
| Photo post | Defer or v1.1 | Official docs now indicate photo support, but video should define the first TikTok proof. |
| Privacy, comments, duet, stitch controls | Yes | Must reflect TikTok creator options and account settings; do not hard-code options. |
| Branded/organic/AI-generated disclosures | Yes | Required fields in Direct Post workflows; local businesses frequently promote their own business. |
| Music/sound selection | Defer | TikTok-native editing inside Upload-to-Inbox is safer than trying to solve music rights in v1. |
| Trend ingestion | Defer | Strong differentiator later, but not needed for first real publishing proof. |

TikTok acceptance requirements:

- Before publishing, LocalPilot fetches creator info and stores a per-job snapshot of available privacy options, max video duration, and disabled interaction settings.
- Owner must choose or confirm privacy level, comments, duet, stitch, branded content/organic promotion, and AI-generated disclosure before submission.
- Direct Post can only start after explicit consent to send the video to TikTok.
- Upload mode must clearly track `inbox_delivered` and instruct the owner that they must finish posting from TikTok.
- LocalPilot stores TikTok `publish_id` for every submitted job and polls or receives webhooks for status.
- Status tracking must represent processing, inbox delivery, public availability, failure reason, and moderation delay.
- Retry logic must respect TikTok rate limits and distinguish media-fix failures from retryable server/network failures.

## Differentiators For Local Small Businesses

These are the features that keep LocalPilot from becoming a generic scheduler.

| Feature | Value Proposition | Complexity | Requirement Mapping |
|---------|-------------------|------------|---------------------|
| Local offer-to-post generator | Turns a menu item, service opening, coupon, seasonal promotion, or event into ready Facebook and TikTok variants. | Medium | `REQ-LOCAL-001`: offer schema includes product/service, price, date, neighborhood, CTA, language, and proof point. |
| Local CTA library | Owners need calls, bookings, DMs, map clicks, coupon scans, and walk-ins, not generic engagement CTAs. | Low | `REQ-LOCAL-002`: CTA templates by industry and channel. |
| Platform-specific local angle | Facebook copy should support community/context; TikTok should support hook, visual action, and short-form pacing. | Medium | `REQ-LOCAL-003`: generator outputs distinct strategy fields, not copied captions. |
| Bilingual/local-cultural variants | Many target businesses serve English and Chinese-speaking customers. | Medium | `REQ-LOCAL-004`: generate language variants without requiring Xiaohongshu publishing. |
| Owner-safe brand voice controls | Small businesses are sensitive to exaggerated claims, discounts, medical/beauty promises, and tone mismatch. | Medium | `REQ-BRAND-001`: profile includes claims to avoid, tone, forbidden words, and required disclaimers. |
| Pilot support/admin review mode | Early merchant accounts will need hands-on setup and API troubleshooting. | Medium | `REQ-ADMIN-002`: support staff can inspect jobs and prepare manual packages without impersonating the merchant. |
| Simple local ROI placeholders | Even before deep analytics, every post should carry a business goal and trackable CTA where possible. | Medium | `REQ-ROI-001`: optional UTM, coupon code, QR/link shortener, booking URL attached to draft. |
| "What to do next" failure guidance | Owners should see plain-language instructions, not raw API errors. | Low | `REQ-UX-001`: convert normalized errors into owner-facing next action and admin detail. |

## Anti-Features To Defer

These should be explicitly out of scope for the first real publishing MVP.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Xiaohongshu direct publishing | No proven generally available, compliant official/partner organic note publishing route was confirmed in this research. Public official material surfaced Marketing API/ad/data positioning, not a clear SMB organic publishing API. | Provide Xiaohongshu copy/package export only; create a separate research spike for official partner routes. |
| Cookie-based or browser-automation posting | Fragile, likely non-compliant, risky for merchant accounts. | Use official APIs or manual assisted export. |
| Fully autonomous publishing | Undermines owner trust and increases brand/compliance risk. | Require explicit approval for each platform variant. |
| Paid ads publishing | Different permissions, budgets, compliance, and optimization loop. | Keep v1 organic publishing only. |
| Multi-location franchise/agency workflow | Adds roles, approvals, client switching, billing, and audit complexity. | Support one organization/business profile and one or more connected accounts; add roles later. |
| Instagram, Google Business Profile, LinkedIn, X | Useful but would dilute the Facebook/TikTok proof. | Keep data model extensible; only implement Facebook and TikTok now. |
| Advanced calendar/scheduler | Generic scheduler territory and time-zone/queue complexity. | Start with approved immediate publishing plus manual fallback. |
| Trend-to-action engine | Differentiating later, but requires data sourcing and evaluation. | Use curated prompt guidance in generation; build trend ingestion after publish loop works. |
| Deep analytics dashboards | Publishing status and post IDs must come first. | Store IDs and CTA metadata so analytics can attach later. |
| Music rights and TikTok sound automation | Hard to do safely via API and may be better completed in TikTok. | Use Upload-to-Inbox and owner manual editing for sound. |

## Account Connection Requirements

| Requirement | Details | Later Requirement ID |
|-------------|---------|----------------------|
| Server-side OAuth boundary | All OAuth exchanges, refreshes, and token storage happen in backend or self-hosted publishing engine, never the React browser app. | `REQ-ACCOUNT-001` |
| Connection inventory | Show connected platform, account/Page name, external ID, scopes, status, and last check. | `REQ-ACCOUNT-002` |
| Eligibility checks | Mark whether account can publish now, needs reconnect, needs missing permission, needs app review, or requires manual fallback. | `REQ-ACCOUNT-003` |
| Reconnect flow | User can reconnect without losing drafts or campaign history. | `REQ-ACCOUNT-004` |
| Page/account selection | Facebook requires selecting a Page; TikTok requires selecting/confirming the authorized creator account. | `REQ-ACCOUNT-005` |
| Admin diagnostics | Support view includes raw provider IDs, trace/log IDs, failure category, and last provider response. | `REQ-ADMIN-001` |

## User Approval Requirements

| Requirement | Details | Later Requirement ID |
|-------------|---------|----------------------|
| Approval is per platform variant | Approving Facebook does not approve TikTok. | `REQ-APPROVAL-001` |
| Frozen payload snapshot | Store the exact approved caption, media IDs/URLs, CTA, disclosure settings, destination, and timestamp. | `REQ-APPROVAL-002` |
| Revision loop | Owner can request changes with a note; regenerated/edited content returns to `needs_review`. | `REQ-APPROVAL-003` |
| Consent at publish time | Final publish action must state destination account, platform, visibility, and media. | `REQ-APPROVAL-004` |
| TikTok explicit consent | Direct Post requires explicit consent to send the video to TikTok after metadata is set. | `REQ-TT-APPROVAL-001` |
| Audit trail | Store approver, approval time, submitter, submission time, and manual/admin overrides. | `REQ-APPROVAL-005` |

## Media Validation Requirements

| Requirement | Facebook | TikTok | Later Requirement ID |
|-------------|----------|--------|----------------------|
| File type validation | Validate image/video MIME and extension before publish. | Validate supported video format first; photo support can come later. | `REQ-MEDIA-001` |
| Size and duration validation | Block files too large for chosen endpoint/engine. | Respect max duration from creator info and platform video restrictions. | `REQ-MEDIA-002` |
| URL accessibility | Needed if a publishing engine or platform pulls media by URL. | Required for Pull-from-URL; URL must be HTTPS, non-redirecting, and under verified ownership/prefix. | `REQ-MEDIA-003` |
| Object storage | Store uploaded assets in server-side media storage. | Store assets with public/temporary access compatible with TikTok transfer mode. | `REQ-MEDIA-004` |
| Thumbnail/cover metadata | Optional for basic Facebook. | Capture cover timestamp when Direct Post supports it. | `REQ-MEDIA-005` |
| AI/disclosure metadata | Optional in Facebook v1 unless generated-media policy requires it. | Required field if video is AI-generated. | `REQ-MEDIA-006` |
| Revalidation before submission | Validate after edits and immediately before publish job starts. | Validate after creator info is refreshed. | `REQ-MEDIA-007` |

## Error, Retry, And Status Requirements

| Requirement | Details | Later Requirement ID |
|-------------|---------|----------------------|
| Unified status model | Use LocalPilot statuses independent of provider-specific names, while storing raw provider status. | `REQ-STATUS-001` |
| Provider job table | Persist one publishing task per platform variant, with attempts and immutable payload snapshot. | `REQ-PUBLISH-001` |
| Retry policy | Automatic retry only for safe transient failures such as network/server errors; require user action for token, permission, media, moderation, or account restrictions. | `REQ-ERROR-001` |
| Backoff/rate-limit handling | Respect provider limits; do not retry in tight loops. | `REQ-ERROR-002` |
| User-action states | Show `reconnect account`, `fix media`, `change privacy setting`, `finish in TikTok`, or `use manual package`. | `REQ-UX-001` |
| Raw diagnostic capture | Store provider error code/message/log ID/fbtrace ID where available. | `REQ-ADMIN-001` |
| Webhook-ready design | TikTok supports webhooks for final posting outcomes; design status updates so polling and webhooks can coexist. | `REQ-STATUS-002` |
| Manual completion | Owner or support can mark a manual fallback as completed with URL/screenshot/post ID if API publishing is unavailable. | `REQ-FALLBACK-002` |

Suggested status vocabulary:

```text
draft -> needs_review -> changes_requested -> approved -> queued -> publishing

publishing -> upload_processing -> moderation_pending -> published
publishing -> inbox_delivered -> manually_completed
publishing -> failed -> retry_needed
retry_needed -> queued
failed -> manual_fallback_ready
```

## Implementation Shape For Requirements Later

The roadmap should split requirements into thin vertical slices rather than platform silos.

1. **Persistence foundation**
   - Requirements: `REQ-ACCOUNT-*`, `REQ-CAMPAIGN-001`, `REQ-DRAFT-001`, `REQ-STATUS-001`
   - Outcome: business profile, connected accounts, drafts, approvals, media, and publishing tasks are stored outside localStorage.

2. **Facebook publishing proof**
   - Requirements: `REQ-FB-001`, `REQ-APPROVAL-*`, `REQ-MEDIA-*`, `REQ-PUBLISH-001`, `REQ-ERROR-*`
   - Outcome: one approved Facebook Page text/link/image post can be published or fall back to manual package with traceable status.

3. **TikTok upload proof**
   - Requirements: `REQ-TT-001`, `REQ-TT-APPROVAL-001`, `REQ-MEDIA-*`, `REQ-STATUS-002`
   - Outcome: one approved TikTok video can be uploaded to inbox/draft and tracked until owner completion or failure.

4. **TikTok Direct Post hardening**
   - Requirements: app audit/scopes validation, explicit consent UX, creator-info refresh, moderation/status handling
   - Outcome: Direct Post is enabled only for eligible accounts and content.

5. **Local-business differentiation layer**
   - Requirements: `REQ-LOCAL-*`, `REQ-BRAND-001`, `REQ-ROI-001`
   - Outcome: posts are not generic scheduler payloads; they carry local CTA, business context, and owner-safe brand controls.

6. **Pilot support and fallbacks**
   - Requirements: `REQ-ADMIN-*`, `REQ-FALLBACK-*`, `REQ-UX-001`
   - Outcome: early customers can be supported through platform approval delays and API failures without abandoning the workflow.

## MVP Recommendation

Prioritize:

1. Persisted campaign, account, approval, media, and publishing-task models.
2. Facebook Page account connection and immediate Page post publishing for text/link/image.
3. Owner approval and frozen payload snapshots.
4. Error/status timeline with manual fallback package.
5. TikTok account connection, creator-info preflight, and Upload-to-Inbox for video.
6. TikTok Direct Post after audit/scopes/consent/status handling are validated.
7. Local-business CTA and bilingual/channel-native generation rules.

Defer:

- Xiaohongshu direct publishing until a compliant official or partner route is proven.
- Paid ads, comments/DM inbox, deep analytics, scheduler-heavy calendar, agency roles, franchise/multi-location controls, and non-Facebook/TikTok channels.

## Sources

- Local project context: `.planning/PROJECT.md`, `docs/feature_gap_priority_review.md`, `docs/ceo_cto_plan_for_local_marketing_agent.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md` (HIGH for local product intent and codebase constraints).
- TikTok official Content Posting API Direct Post: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post (HIGH).
- TikTok official Content Posting API Get Started: https://developers.tiktok.com/doc/content-posting-api-get-started (HIGH).
- TikTok official Content Posting API Upload: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video (HIGH).
- TikTok official Content Posting API Media Transfer Guide: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide (HIGH).
- TikTok official Get Post Status/webhooks: https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status (HIGH).
- Meta official Pages API docs attempted: https://developers.facebook.com/docs/pages-api/posts/ returned a login requirement; Graph API reference URLs intermittently returned rate-limit errors during research (LOW direct-access confidence for this run).
- Facebook Page publishing cross-check: https://postproxy.dev/blog/facebook-graph-api-posting-guide/ (MEDIUM; current third-party implementation guide, not official).
- Postiz Public API overview and provider schemas: https://docs.postiz.com/public-api/introduction, https://docs.postiz.com/public-api/providers/facebook, https://docs.postiz.com/public-api/providers/tiktok (MEDIUM-HIGH for workflow/engine inspiration, not platform policy authority).
- Postiz CLI/MCP docs: https://docs.postiz.com/cli/introduction, https://docs.postiz.com/mcp/introduction (MEDIUM-HIGH for reusable workflow ideas).
- Xiaohongshu official Marketing API landing page discovered via search: https://ad-market.xiaohongshu.com/ (LOW for organic publishing; did not prove SMB organic note publishing).
