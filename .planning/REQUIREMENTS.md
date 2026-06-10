# Requirements: LocalPilot AI

**Defined:** 2026-06-09
**Core Value:** A local business owner can go from one marketing idea to approved, platform-native Facebook and TikTok posts published through their own official accounts with minimal effort.

## v1 Requirements

Requirements for the first real publishing milestone. Each requirement should map to exactly one roadmap phase.

### Publishing Foundation

- [ ] **FOUND-01**: System stores merchants, users, business profiles, connected channels, campaigns, drafts, approvals, media assets, publish jobs, publish attempts, and publish events outside browser localStorage.
- [x] **FOUND-02**: System exposes versioned backend API endpoints for publishing workflow records consumed by the React app.
- [ ] **FOUND-03**: System supports a fake publishing adapter that exercises the full publish lifecycle without live platform credentials.
- [ ] **FOUND-04**: System records immutable publish job attempts with request metadata, normalized status, redacted provider diagnostics, and timestamps.
- [ ] **FOUND-05**: System uses idempotency keys so retrying an approved publish job cannot create duplicate external posts for the same approved draft version.
- [ ] **FOUND-06**: System keeps current demo/marketing routes usable while replacing publish-critical localStorage state with API-backed records.

### Account Connections

- [ ] **ACCT-01**: Merchant can start an official Facebook account connection flow from the LocalPilot app.
- [ ] **ACCT-02**: Merchant can select one Facebook Page they manage for publishing.
- [ ] **ACCT-03**: System verifies the selected Facebook Page has the required publishing capability before allowing publish jobs.
- [ ] **ACCT-04**: Merchant can start an official TikTok account connection flow from the LocalPilot app.
- [ ] **ACCT-05**: System queries TikTok creator information before TikTok publishing so the UI reflects the creator account's actual privacy and interaction options.
- [ ] **ACCT-06**: Merchant can view connected-channel health, including connected, missing permission, expired token, review blocked, or reconnect required.
- [ ] **ACCT-07**: Merchant can disconnect a Facebook or TikTok account and stop new publish jobs from using that connection.

### Security And Compliance

- [ ] **SEC-01**: OAuth access tokens, refresh tokens, app secrets, and provider credentials are never stored in browser localStorage or committed files.
- [ ] **SEC-02**: Backend stores provider tokens in a server-side encrypted or secret-managed token boundary.
- [x] **SEC-03**: System redacts secrets and provider tokens from logs, publish events, error messages, and admin diagnostics.
- [ ] **SEC-04**: System requires explicit merchant approval before any live platform publish request is submitted.
- [ ] **SEC-05**: System rejects scraping, cookie-based posting, and browser-session automation for production merchant publishing.
- [x] **SEC-06**: System preserves a reviewable audit trail showing who approved a draft, which draft version was approved, and when publishing was attempted.

### Campaign Generation

- [ ] **CAMP-01**: Merchant can enter one local offer, service, product, event, or promotion as the source input for a campaign.
- [ ] **CAMP-02**: System generates a Facebook-specific post draft with local-business copy, CTA, link or offer context, and optional media guidance.
- [ ] **CAMP-03**: System generates a TikTok-specific post draft with hook, caption, hashtags, CTA, video direction, and required disclosure fields.
- [ ] **CAMP-04**: System creates separate editable draft records for each platform instead of treating Facebook and TikTok as copied captions.
- [ ] **CAMP-05**: Merchant can regenerate platform drafts while preserving prior versions for audit and comparison.
- [ ] **CAMP-06**: Generated drafts can include local CTA metadata such as call, booking, DM, coupon, map-click, or walk-in intent.

### Draft Review And Approval

- [ ] **APPR-01**: Merchant can review Facebook and TikTok drafts side by side before publishing.
- [ ] **APPR-02**: Merchant can edit generated captions, hashtags, CTAs, links, disclosure settings, and media notes before approval.
- [ ] **APPR-03**: Merchant can request regeneration or revision instead of approving a draft.
- [ ] **APPR-04**: Merchant can approve a specific draft version for a specific platform.
- [ ] **APPR-05**: System freezes the approved payload snapshot so later edits cannot silently change an already-approved publish job.
- [x] **APPR-06**: Merchant can see whether each platform draft is draft, needs review, approved, queued, publishing, published, failed, retry needed, or manually completed.

### Media Handling

- [ ] **MEDIA-01**: Merchant can attach or reference media assets for Facebook and TikTok drafts.
- [ ] **MEDIA-02**: System stores media assets in a server-side storage location suitable for platform publishing or upload.
- [ ] **MEDIA-03**: System validates Facebook media requirements before creating a Facebook publish job.
- [ ] **MEDIA-04**: System validates TikTok media requirements such as file type, file size, duration, and accessible upload source before creating a TikTok publish job.
- [ ] **MEDIA-05**: System surfaces actionable media validation errors to the merchant before publishing.

### Publishing Engine Reuse

- [ ] **ENGINE-01**: Team can run a focused spike comparing Postiz-style self-hosted/API/MCP publishing reuse against native provider adapters.
- [ ] **ENGINE-02**: System defines a `PublishingProvider` contract that can wrap Postiz-style APIs, native Meta adapters, native TikTok adapters, or the fake adapter without changing product workflow records.
- [ ] **ENGINE-03**: Spike records whether Postiz-style tooling can connect Facebook Pages, handle TikTok posting/upload flows, submit media, return status, expose errors, and meet deployment/licensing needs.
- [ ] **ENGINE-04**: Spike explicitly rejects AutoCLI/browser-session automation for production publishing, while allowing it only as internal research tooling if needed.
- [ ] **ENGINE-05**: Team makes a documented go/no-go decision before building deep custom Facebook or TikTok request wrappers.

### Facebook Publishing

- [ ] **FB-01**: System documents the current Meta developer app, permissions, app review, test Page, and screencast requirements needed for Facebook Page publishing.
- [ ] **FB-02**: System can publish an approved text-only Facebook Page post through the merchant-selected Page when required permissions are available.
- [ ] **FB-03**: System can publish an approved Facebook Page post with link or media when required permissions and media validation pass.
- [ ] **FB-04**: System stores the external Facebook post ID and public URL or provider reference when available.
- [ ] **FB-05**: System classifies Facebook publish failures by authentication, missing permission, Page capability, validation, rate limit, platform transient, or unknown error.
- [ ] **FB-06**: System supports reconnect, retry, or manual fallback actions after Facebook publish failures.

### TikTok Publishing

- [ ] **TT-01**: System documents the current TikTok Content Posting API scopes, audit requirements, upload modes, creator-info requirements, and visibility constraints.
- [ ] **TT-02**: System supports TikTok Upload-to-Inbox or draft-style delivery as the first compliant TikTok publishing outcome.
- [ ] **TT-03**: System only enables TikTok Direct Post when app audit, required scopes, creator-info UX, privacy settings, and disclosure requirements are satisfied.
- [ ] **TT-04**: Merchant can choose TikTok privacy and interaction settings from options returned by TikTok creator-info APIs.
- [ ] **TT-05**: Merchant can explicitly confirm TikTok disclosure settings such as organic business promotion, paid partnership, or AI-generated content where applicable.
- [ ] **TT-06**: System stores TikTok publish IDs, status responses, and provider diagnostics for support and reconciliation.
- [ ] **TT-07**: System classifies TikTok failures by authentication, scope, creator setting mismatch, media validation, rate limit, audit/visibility block, platform transient, or unknown error.

### Publishing Status And Fallback

- [x] **STATUS-01**: Merchant can see a timeline for each platform publish job from approval through terminal status.
- [x] **STATUS-02**: System can retry transient publish failures without duplicating successful posts.
- [ ] **STATUS-03**: System can mark a platform draft as manual fallback required when official API access, review status, account eligibility, or media constraints block direct publishing.
- [ ] **STATUS-04**: Merchant can download or copy a manual publishing package containing caption, hashtags, CTA, media checklist, disclosure notes, and platform instructions.
- [ ] **STATUS-05**: Merchant can mark a manual fallback package as manually completed.

### Local-Business Differentiation

- [ ] **LOCAL-01**: System captures local business context such as industry, location, audience, tone, offer type, languages, services, and goals.
- [ ] **LOCAL-02**: System uses local business context to generate platform-native Facebook copy rather than generic social captions.
- [ ] **LOCAL-03**: System uses local business context to generate platform-native TikTok hooks, captions, and video directions.
- [ ] **LOCAL-04**: System supports English/Chinese or bilingual draft variants without requiring Xiaohongshu direct publishing.
- [ ] **LOCAL-05**: System flags risky claims, unsupported guarantees, regulated-industry phrasing, or missing disclaimers before approval.
- [ ] **LOCAL-06**: System attaches simple ROI metadata such as coupon code, booking URL, phone CTA, DM CTA, or QR/link placeholder to published drafts.

### Admin And Pilot Support

- [ ] **ADMIN-01**: Internal operator can inspect merchant, connected-channel, publish-job, attempt, and error status for pilot support.
- [ ] **ADMIN-02**: Internal operator can see redacted provider IDs, trace IDs, error classes, and next recommended action without viewing tokens or secrets.
- [ ] **ADMIN-03**: Internal operator can trigger safe retry or mark a manual support path for blocked publish jobs.
- [ ] **ADMIN-04**: System records enough diagnostics to prepare Meta/TikTok app review evidence and troubleshoot pilot merchant failures.

## v2 Requirements

Deferred requirements tracked for later releases.

### Xiaohongshu

- **XHS-01**: Team validates whether an official or partner route supports merchant-owned organic Xiaohongshu note publishing.
- **XHS-02**: System can generate RED-native title, note body, cover text, hashtags, and checklist as an assisted export package.
- **XHS-03**: System can track Xiaohongshu manual completion status.
- **XHS-04**: System can publish Xiaohongshu notes only after official/partner access, compliance requirements, scopes, sandbox behavior, and merchant authorization are proven.

### Analytics And ROI

- **ROI-01**: System tracks post-level calls, booking clicks, DMs, coupon scans, QR scans, saves, map clicks, and walk-in signals.
- **ROI-02**: System generates weekly plain-language ROI reports for local merchants.
- **ROI-03**: System compares platform outcomes and recommends next-week campaign adjustments.

### Additional Channels

- **CHAN-01**: System supports Instagram publishing after Facebook/TikTok proof is stable.
- **CHAN-02**: System supports Google Business Profile posting if local SEO becomes a priority.
- **CHAN-03**: System supports additional social channels through the publishing provider contract when they do not dilute Facebook/TikTok reliability.

### Agency And Scale

- **AGENCY-01**: Agency user can manage multiple merchant workspaces.
- **AGENCY-02**: Team members can have roles and permissions for draft review, approval, publishing, and support.
- **AGENCY-03**: System supports white-label or client-facing reporting for agencies.

## Out of Scope

Explicitly excluded from the v1 roadmap.

| Feature | Reason |
|---------|--------|
| Direct Xiaohongshu publishing | No confirmed general official/partner path for merchant-owned organic note publishing. |
| Paid ad campaign publishing | Ads require different account permissions, budgets, review flows, reporting, and compliance. |
| Browser automation or cookie-based posting | Too fragile and risky for merchant-owned production publishing. |
| Fully autonomous publishing | Merchants need trust, brand control, and explicit approval before public posts. |
| Shared LocalPilot account publishing | The product goal is merchant-owned official accounts. |
| Instagram and Google Business Profile v1 publishing | Useful later, but Facebook and TikTok must prove the real publishing loop first. |
| Full enterprise agency workflow | Defer until the one-business merchant workflow works reliably. |
| Deep analytics dashboard | Store ROI metadata now; build analytics after publishing proof. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 - Backend Publishing Foundation | Pending |
| FOUND-02 | Phase 1 - Backend Publishing Foundation | Complete |
| FOUND-03 | Phase 1 - Backend Publishing Foundation | Pending |
| FOUND-04 | Phase 1 - Backend Publishing Foundation | Pending |
| FOUND-05 | Phase 1 - Backend Publishing Foundation | Pending |
| FOUND-06 | Phase 1 - Backend Publishing Foundation | Pending |
| ACCT-01 | Phase 4 - Facebook Page Publishing | Pending |
| ACCT-02 | Phase 4 - Facebook Page Publishing | Pending |
| ACCT-03 | Phase 4 - Facebook Page Publishing | Pending |
| ACCT-04 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| ACCT-05 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| ACCT-06 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| ACCT-07 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| SEC-01 | Phase 1 - Backend Publishing Foundation | Pending |
| SEC-02 | Phase 1 - Backend Publishing Foundation | Pending |
| SEC-03 | Phase 1 - Backend Publishing Foundation | Complete |
| SEC-04 | Phase 1 - Backend Publishing Foundation | Pending |
| SEC-05 | Phase 2 - Publishing Engine Reuse Decision | Pending |
| SEC-06 | Phase 1 - Backend Publishing Foundation | Complete |
| CAMP-01 | Phase 3 - Local Campaign Draft Workbench | Pending |
| CAMP-02 | Phase 3 - Local Campaign Draft Workbench | Pending |
| CAMP-03 | Phase 3 - Local Campaign Draft Workbench | Pending |
| CAMP-04 | Phase 3 - Local Campaign Draft Workbench | Pending |
| CAMP-05 | Phase 3 - Local Campaign Draft Workbench | Pending |
| CAMP-06 | Phase 3 - Local Campaign Draft Workbench | Pending |
| APPR-01 | Phase 3 - Local Campaign Draft Workbench | Pending |
| APPR-02 | Phase 3 - Local Campaign Draft Workbench | Pending |
| APPR-03 | Phase 3 - Local Campaign Draft Workbench | Pending |
| APPR-04 | Phase 1 - Backend Publishing Foundation | Pending |
| APPR-05 | Phase 1 - Backend Publishing Foundation | Pending |
| APPR-06 | Phase 1 - Backend Publishing Foundation | Complete |
| MEDIA-01 | Phase 3 - Local Campaign Draft Workbench | Pending |
| MEDIA-02 | Phase 3 - Local Campaign Draft Workbench | Pending |
| MEDIA-03 | Phase 4 - Facebook Page Publishing | Pending |
| MEDIA-04 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| MEDIA-05 | Phase 3 - Local Campaign Draft Workbench | Pending |
| ENGINE-01 | Phase 2 - Publishing Engine Reuse Decision | Pending |
| ENGINE-02 | Phase 2 - Publishing Engine Reuse Decision | Pending |
| ENGINE-03 | Phase 2 - Publishing Engine Reuse Decision | Pending |
| ENGINE-04 | Phase 2 - Publishing Engine Reuse Decision | Pending |
| ENGINE-05 | Phase 2 - Publishing Engine Reuse Decision | Pending |
| FB-01 | Phase 4 - Facebook Page Publishing | Pending |
| FB-02 | Phase 4 - Facebook Page Publishing | Pending |
| FB-03 | Phase 4 - Facebook Page Publishing | Pending |
| FB-04 | Phase 4 - Facebook Page Publishing | Pending |
| FB-05 | Phase 4 - Facebook Page Publishing | Pending |
| FB-06 | Phase 4 - Facebook Page Publishing | Pending |
| TT-01 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| TT-02 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| TT-03 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| TT-04 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| TT-05 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| TT-06 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| TT-07 | Phase 5 - TikTok Upload And Direct-Post Gates | Pending |
| STATUS-01 | Phase 1 - Backend Publishing Foundation | Complete |
| STATUS-02 | Phase 1 - Backend Publishing Foundation | Complete |
| STATUS-03 | Phase 6 - Manual Fallback And Pilot Support | Pending |
| STATUS-04 | Phase 6 - Manual Fallback And Pilot Support | Pending |
| STATUS-05 | Phase 6 - Manual Fallback And Pilot Support | Pending |
| LOCAL-01 | Phase 3 - Local Campaign Draft Workbench | Pending |
| LOCAL-02 | Phase 3 - Local Campaign Draft Workbench | Pending |
| LOCAL-03 | Phase 3 - Local Campaign Draft Workbench | Pending |
| LOCAL-04 | Phase 3 - Local Campaign Draft Workbench | Pending |
| LOCAL-05 | Phase 3 - Local Campaign Draft Workbench | Pending |
| LOCAL-06 | Phase 3 - Local Campaign Draft Workbench | Pending |
| ADMIN-01 | Phase 6 - Manual Fallback And Pilot Support | Pending |
| ADMIN-02 | Phase 6 - Manual Fallback And Pilot Support | Pending |
| ADMIN-03 | Phase 6 - Manual Fallback And Pilot Support | Pending |
| ADMIN-04 | Phase 6 - Manual Fallback And Pilot Support | Pending |

**Coverage:**

- v1 requirements: 69 total
- Mapped to phases: 69
- Unmapped: 0
- Duplicate mappings: 0
- Coverage status: Complete

---
*Requirements defined: 2026-06-09*
*Last updated: 2026-06-09 after roadmap creation*
