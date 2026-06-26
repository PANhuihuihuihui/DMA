# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R001 — Predis-Style Demo Surface (Phase 3)
- Class: primary-user-loop
- Status: active
- Description: Merchant's logged-in workspace matches Predis.ai's logged-in product structure: left nav with Create New, Inspirations, Content Library, Calendar, Brand & Social Accounts, Analytics, Help; format chooser (Image/UGC/Carousel/Video); source-method pickers; publish/schedule modal with account gating; calendar drawer with locked-state behavior.
- Why it matters: Field sales credibility depends on a visually and behaviorally comparable demo surface that earns merchant trust on first impression.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S01–S10
- Validation: unmapped

### R002 — Merchant-Driven Facebook OAuth + Page Selection
- Class: core-capability
- Status: active
- Description: Merchant connects Facebook via official OAuth, views managed Pages, and actively selects which Page to publish to — no silent auto-pick, no pasted tokens.
- Why it matters: Owner trust requires explicit account and Page selection; auto-pick breaks multi-location merchants and obscures what's being published.
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: M002/S01
- Validation: unmapped

### R003 — Encrypted Facebook Token Persistence
- Class: security
- Status: active
- Description: Facebook page access tokens are encrypted at rest in SQLite using Fernet (AES-128-CBC + HMAC-SHA256) keyed from LOCALPILOT_TOKEN_KEY env var. Tokens survive server restart. Production fails closed if the key is absent.
- Why it matters: Current in-memory token vault loses all credentials on restart — not viable for any real merchant session.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: unmapped

### R004 — Facebook Media Pre-Validation
- Class: core-capability
- Status: active
- Description: Facebook publish jobs validate media (link URL accessibility, single image type/size) before the job is created, surfacing actionable errors to the merchant rather than letting the job fail at the platform API.
- Why it matters: Platform API errors are confusing to merchants. Validation errors with plain-language guidance prevent wasted retries and support tickets.
- Source: user
- Primary owning slice: M002/S03
- Supporting slices: none
- Validation: unmapped

### R005 — Facebook Publish Failure Routing
- Class: failure-visibility
- Status: active
- Description: Facebook publish failures are classified (authentication / permission / Page capability / validation / rate limit / platform transient / unknown) and routed to reconnect, retry, or manual fallback appropriately. Retryable failures retry; non-retryable (auth, permission, capability, audit/visibility block) mark the job manual_fallback_required.
- Why it matters: A merchant who sees "failed" with no guidance is stranded. The taxonomy drives the right remediation action.
- Source: user
- Primary owning slice: M002/S04
- Supporting slices: none
- Validation: unmapped

### R006 — Facebook App Review Evidence Bundle
- Class: compliance
- Status: active
- Description: System can export a per-job redacted evidence bundle (scopes granted, chosen publish route, gate results, confirmation timestamps) for Meta app review and pilot support without exposing tokens or secrets.
- Why it matters: App review requires documented evidence of every permission used and every publish path. Manual screenshotting is not scalable.
- Source: user
- Primary owning slice: M002/S05
- Supporting slices: none
- Validation: unmapped

### R007 — Carousel Generation (Phase 11)
- Class: core-capability
- Status: active
- Description: Merchant can generate a 5-slide branded carousel from an idea or a public URL, using real image generation (MiniMax default) and brand kit styling, opening in the Creative Editor for review and approval.
- Why it matters: Carousels are a high-engagement local business format (service showcases, step-by-step offers, before/after). Without this, the content library is incomplete.
- Source: user
- Primary owning slice: M003/S01
- Supporting slices: M003/S02, M003/S03
- Validation: unmapped

### R008 — Slide-Locked Editor + Approval Continuity
- Class: primary-user-loop
- Status: active
- Description: Completed carousel generation opens in the Creative Editor as a locked 5-slide package. Merchant can edit slides and approve the full package before it enters the normal approval → publish flow. Editing a locked carousel creates a new version.
- Why it matters: Carousels are a single publishable unit. Editing individual slides mid-campaign breaks the narrative. Approval must cover the whole carousel, not individual slides.
- Source: user
- Primary owning slice: M003/S03
- Supporting slices: M003/S01
- Validation: unmapped

### R009 — Text-to-Video Generation (Phase 12)
- Class: core-capability
- Status: active
- Description: Merchant can generate a short video from a text prompt (script, scene beats, captions, voiceover direction) through a video-model provider adapter, metered by credits.
- Why it matters: Video is the highest-engagement local content format for TikTok and Instagram. Without it, the product can't compete with Predis on TikTok reach.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: M004/S02, M004/S03
- Validation: unmapped

### R010 — UGC Avatar Video (Phase 12)
- Class: differentiator
- Status: active
- Description: Merchant can generate a UGC avatar video by selecting an avatar (by attributes) and providing a script, producing a video with voiceover, metered by credits.
- Why it matters: UGC-style videos using a business avatar are a Predis hallmark feature. It differentiates local business video from generic stock footage.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S01, M004/S03
- Validation: unmapped

## Validated

### R020 — Backend Publishing Foundation
- Class: core-capability
- Status: validated
- Description: System stores merchants, users, business profiles, connected channels, campaigns, drafts, approvals, media assets, publish jobs, publish attempts, and publish events outside browser localStorage. Exposes versioned API endpoints for all publishing workflow records.
- Why it matters: Browser-only state disappears on refresh and can't survive server restarts. Backend persistence enables real multi-session, multi-merchant operation.
- Source: user
- Primary owning slice: M001-ref (Phase 1)
- Supporting slices: none
- Validation: validated
- Notes: Phases 1–2; 9 plans, all complete and verified.

### R021 — Facebook OAuth + TikTok OAuth
- Class: core-capability
- Status: validated
- Description: System supports official Facebook and TikTok OAuth flows with tokens stored server-side. TikTok supports Upload-to-Inbox and creator-info privacy settings.
- Why it matters: Merchant-owned accounts are the product's core promise. OAuth is the only compliant path for Page publishing.
- Source: user
- Primary owning slice: M001-ref (Phase 1), M003-ref (Phase 5)
- Supporting slices: none
- Validation: validated
- Notes: Phase 1 (Facebook OAuth foundation), Phase 5 (TikTok gates). Live Facebook text+scheduled posting works; media + hardening is Phase 4.

### R022 — TikTok Publish Failure Taxonomy
- Class: failure-visibility
- Status: validated
- Description: TikTok failures are classified into authentication, scope, creator setting mismatch, media validation, rate limit, audit/visibility block, platform transient, or unknown, with appropriate routing.
- Why it matters: Same taxonomy applies to Facebook in Phase 4; the pattern is already proven.
- Source: user
- Primary owning slice: M003-ref (Phase 5)
- Supporting slices: none
- Validation: validated

### R023 — Approval Snapshots + Immutable Publish Payload
- Class: core-capability
- Status: validated
- Description: Merchant can approve a specific draft version and the system freezes an immutable snapshot. Retries re-use the snapshot. Both Facebook and TikTok paths respect this.
- Why it matters: Without frozen snapshots, edits after approval silently change what gets published. Unacceptable for merchant-owned public posts.
- Source: user
- Primary owning slice: M001-ref (Phase 1)
- Supporting slices: none
- Validation: validated

### R024 — Google OAuth Sign-In
- Class: core-capability
- Status: validated
- Description: User can sign in with Google, backend verifies ID token (signature, aud, exp, iss), uses Google sub as stable user key, links/creates user + merchant, issues LocalPilot session cookie.
- Why it matters: Replaces fake browser-identity demo state. Required for any real merchant onboarding.
- Source: user
- Primary owning slice: M005-ref (Phase 7)
- Supporting slices: none
- Validation: validated

### R025 — Website-Crawl Smart Onboarding
- Class: core-capability
- Status: validated
- Description: Merchant enters website URL → backend crawls public info → auto-generates business profile (name, description, digital presence), brand style (logo, colors, fonts), and content settings (tonality, language, timezone, voiceover, avatar) that the merchant reviews and edits before confirming. Fetches public info only; stores no credentials; sanitizes untrusted content.
- Why it matters: Reduces onboarding friction from "empty form" to "one URL". Mirrors Predis "Fetch details from website".
- Source: user
- Primary owning slice: M006-ref (Phase 8)
- Supporting slices: none
- Validation: validated

### R026 — Generation Platform + Credit Metering
- Class: core-capability
- Status: validated
- Description: Backend exposes provider-agnostic generation contract routing to {provider, model} with server-side API keys. Generation runs as async jobs with normalized status lifecycle (queued, running, succeeded, failed) and result references. Credit usage is metered per job via credit_accounts + credit_ledger with reserve/settle/release. Insufficient balance blocks launches.
- Why it matters: Foundation for all Phase 11+ content generation. Credits prevent runaway spend. Provider abstraction avoids lock-in.
- Source: user
- Primary owning slice: M007-ref (Phase 13)
- Supporting slices: none
- Validation: validated

### R027 — Phase 3 Demo Workspace (Phase 3, Plan 1)
- Class: primary-user-loop
- Status: validated
- Description: Backend-owned workspace with 9 screens: Dashboard, Brand Kit, AI Generator, Creative Editor, Content Calendar, Approval Queue, Connected Accounts, Competitor Ideas, Proof Loop. All screens backed by Phase 3 API routes. Full Playwright smoke coverage. All tests green.
- Why it matters: The merchant-facing demo surface that makes the product credible in a sales conversation.
- Source: user
- Primary owning slice: M001-ref (Phase 3, 03-01)
- Supporting slices: none
- Validation: validated
- Notes: 03-02 (Predis reference hardening) still pending.

## Deferred

### R040 — Xiaohongshu (RED) Publishing
- Class: core-capability
- Status: deferred
- Description: System validates official or partner route for merchant-owned organic Xiaohongshu note publishing; generates RED-native title, body, cover, hashtags as assisted export package; tracks manual completion status.
- Why it matters: Xiaohongshu is strategically important for cross-cultural/local Chinese consumer reach. Not part of v1.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred until a compliant official/partner route is confirmed.

### R041 — Production Analytics + ROI Dashboard
- Class: failure-visibility
- Status: deferred
- Description: Track post-level calls, booking clicks, DMs, coupon scans, QR scans, saves, map clicks, walk-in signals. Generate weekly plain-language ROI reports. Compare platform outcomes and recommend next-week adjustments.
- Why it matters: The proof loop needs real signal, not just demo data. Deferred until publishing proof is stable.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: LOCAL-05 (flag risky claims) and LOCAL-06 (ROI metadata attachment) also deferred.

### R042 — Instagram + Google Business Profile Publishing
- Class: core-capability
- Status: deferred
- Description: System supports Instagram publishing and Google Business Profile posting after Facebook/TikTok proof is stable.
- Why it matters: Platform expansion is planned but Facebook and TikTok must work first.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Instagram deferred to v2. Google Business Profile deferred.

### R043 — Merchant Manual Publishing Package (STATUS-04/05)
- Class: failure-visibility
- Status: deferred
- Description: Merchant can download/copy a manual publishing package (caption, hashtags, CTA, media checklist, disclosure notes, instructions) and mark it as manually completed.
- Why it matters: Manual fallback is needed for blocked jobs. Descoped from Phase 6 to keep scope tight.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred to post-v1.0.

## Out of Scope

### R050 — Scraping / Cookie-Based Posting
- Class: anti-feature
- Status: out-of-scope
- Description: System does not use scraping, reverse engineering, or cookie-based posting for any restricted platform.
- Why it matters: Fragile and risky for merchant-owned production publishing; violates Meta/TikTok terms.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

### R051 — Autonomous Publishing Without Approval
- Class: anti-feature
- Status: out-of-scope
- Description: System requires explicit merchant approval before any live platform publish request is submitted.
- Why it matters: Local businesses need brand safety and trust. Fully autonomous publishing is not the product.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

### R052 — Shared LocalPilot Account Publishing
- Class: anti-feature
- Status: out-of-scope
- Description: System does not publish through a shared LocalPilot account. All publishing is through merchant-owned official accounts.
- Why it matters: The product wedge is merchant-owned accounts, not agency-managed accounts.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

### R053 — Paid Ad Campaign Publishing
- Class: anti-feature
- Status: out-of-scope
- Description: System does not support ad buying, ad campaign creation, or ad performance reporting.
- Why it matters: First milestone is organic post publishing. Ads require different permissions, budgets, and compliance.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | primary-user-loop | active | M001/S01 | M001/S01–S10 | unmapped |
| R002 | core-capability | active | M002/S02 | M002/S01 | unmapped |
| R003 | security | active | M002/S01 | none | unmapped |
| R004 | core-capability | active | M002/S03 | none | unmapped |
| R005 | failure-visibility | active | M002/S04 | none | unmapped |
| R006 | compliance | active | M002/S05 | none | unmapped |
| R007 | core-capability | active | M003/S01 | M003/S02, S03 | unmapped |
| R008 | primary-user-loop | active | M003/S03 | M003/S01 | unmapped |
| R009 | core-capability | active | M004/S01 | M004/S02, S03 | unmapped |
| R010 | differentiator | active | M004/S02 | M004/S01, S03 | unmapped |
| R020 | core-capability | validated | M001-ref (P1) | none | validated |
| R021 | core-capability | validated | M001-ref (P1), M003-ref (P5) | none | validated |
| R022 | failure-visibility | validated | M003-ref (P5) | none | validated |
| R023 | core-capability | validated | M001-ref (P1) | none | validated |
| R024 | core-capability | validated | M005-ref (P7) | none | validated |
| R025 | core-capability | validated | M006-ref (P8) | none | validated |
| R026 | core-capability | validated | M007-ref (P13) | none | validated |
| R027 | primary-user-loop | validated | M001-ref (P3, 03-01) | none | validated |
| R040 | core-capability | deferred | none | none | unmapped |
| R041 | failure-visibility | deferred | none | none | unmapped |
| R042 | core-capability | deferred | none | none | unmapped |
| R043 | failure-visibility | deferred | none | none | unmapped |
| R050 | anti-feature | out-of-scope | none | none | n/a |
| R051 | anti-feature | out-of-scope | none | none | n/a |
| R052 | anti-feature | out-of-scope | none | none | n/a |
| R053 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 10
- Mapped to slices: 0 (pending M001–M004 planning)
- Validated: 8
- Deferred: 4
- Out of scope: 4
- Unmapped active requirements: 10
