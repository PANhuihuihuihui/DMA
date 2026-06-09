# Domain Pitfalls

**Domain:** LocalPilot AI real publishing for local-business Facebook/TikTok, with Xiaohongshu deferred-risk assessment
**Researched:** 2026-06-09
**Overall confidence:** HIGH for TikTok and Xiaohongshu official-surface assessment; MEDIUM for Meta details because several official Meta developer pages required login during research and were corroborated with recent developer references.

## Decision Summary

Ship Facebook first and TikTok second. Defer Xiaohongshu direct publishing until LocalPilot has a confirmed official, partner, or service-provider route that explicitly permits merchant-owned organic publishing or an approved assisted publishing workflow.

The most likely product failure is treating "publishing" as a frontend button instead of a regulated integration system. Real publishing needs OAuth, permissions review, account eligibility checks, media validation, explicit owner approval, server-side jobs, retry discipline, webhook/status handling, and audit trails. The current prototype is frontend-only and stores demo state in `localStorage`, so any roadmap that jumps straight from demo approval buttons to live API calls will create security and compliance risk.

## Critical Pitfalls

### Pitfall 1: Underestimating Meta App Review and Page Permission Complexity

**What goes wrong:** LocalPilot builds a Facebook publish UI that works only for developers/test Pages, then fails for real merchants because the production app lacks approved permissions, Business Verification, Page grants, or review evidence.

**Why it happens:** Meta Page publishing is not just `POST /{page-id}/feed`. The app needs a valid Facebook Login flow, a Page access token for the selected Page, sufficient Page task permissions from the merchant, and reviewed permissions such as `pages_manage_posts` and related Page read/list scopes. App Review often requires a live testable app and a screencast that visibly demonstrates each requested permission being used inside the product.

**Consequences:**
- Pilot merchants cannot connect Pages outside developer/test roles.
- Publishing returns authorization errors such as missing `pages_manage_posts`, missing `pages_read_engagement`, insufficient Page admin/task permission, expired/revoked token, or wrong token type.
- Review gets rejected because the reviewer cannot see page selection, token grant, post creation, or rendered Page identity.
- Engineering adds workarounds that drift toward unsafe token copy/paste or manual Graph API Explorer flows.

**Prevention:**
- Build a dedicated Facebook connection phase before promising production publishing.
- Request the minimum permission set for the first supported use case: Page listing/selection plus Page post creation. Keep comments, inbox, insights, ads, groups, and Instagram out of the first review unless they are actually implemented.
- Require an explicit Page selection screen in-app, not implicit backend matching.
- Store Page ID, Page name, permission grants, token status, and connected-by user separately from campaign drafts.
- Prepare App Review artifacts as a deliverable: reviewer credentials, test Page, recorded flow, permission-by-permission explanation, and an example post created through LocalPilot.
- Treat Page tokens as server-side secrets. Never ask merchants to paste tokens from Graph API Explorer.

**Detection:**
- App works for admins/testers but fails for ordinary merchant accounts.
- `(#200)` or `(#10)` permission errors when calling Page endpoints.
- Merchant can log in but no eligible Page appears.
- Review feedback says the permission use case could not be verified.

### Pitfall 2: Using the Wrong Facebook Token or Account Model

**What goes wrong:** LocalPilot posts with a user token, tries to publish to personal profiles/groups, assumes one merchant has one Page, or stores long-lived tokens in browser state.

**Why it happens:** The product language says "connect Facebook" while the actual supported target for organic API publishing is a Facebook Page controlled by the merchant. Page access tokens are derived from an authorized user/Page connection and can be invalidated by revocation, password/security changes, Page role changes, Business settings, or expired permissions.

**Consequences:**
- Posts fail after initial setup.
- The product cannot explain whether failure is token expiration, missing Page task, revoked consent, or unsupported target.
- Security exposure if a browser compromise reveals merchant Page tokens.
- Support burden from merchants with multiple Pages, classic/new Page transitions, Business Portfolio permissions, or 2FA requirements.

**Prevention:**
- Model `ConnectedAccount`, `ConnectedPage`, `OAuthGrant`, and `PublishCredential` separately.
- Validate every token server-side before enabling publish.
- Add a reconnect flow with clear failure reasons.
- Encrypt tokens at rest, rotate secrets, and log token metadata only, never token values.
- Support only Facebook Pages in v1; label groups, profiles, events, ads, Instagram, and Messenger as unsupported or later-stage.

**Detection:**
- Access token debug output lacks the required scopes.
- The target Page ID is not associated with the token.
- Repeated publish failures cluster after merchant password changes, Page admin changes, or app permission revocation.

### Pitfall 3: Treating TikTok Direct Post as Immediate Public Posting

**What goes wrong:** LocalPilot assumes Direct Post can publish public videos immediately for all merchants once OAuth is connected.

**Why it happens:** TikTok's Content Posting API has official Direct Post and Upload-to-Draft paths, but public visibility depends on app audit, approved scopes, creator authorization, creator privacy settings, per-user capabilities, moderation, quota, and media restrictions. TikTok official docs state unaudited clients are restricted to private visibility; Direct Post requires querying creator information and rendering the latest privacy/interaction options before the user posts.

**Consequences:**
- Pilot posts land as private or fail moderation/status checks.
- Product says "published" before TikTok moderation makes a post publicly available.
- User sees LocalPilot privacy controls that do not match TikTok's current creator options.
- Commercial/promotional content is submitted without required disclosure toggles.

**Prevention:**
- Treat TikTok as a staged integration: Upload-to-Draft first if audit/visibility is not ready; Direct Post only after `video.publish` approval and audit.
- Query `/creator_info/query/` before each publish screen and render returned privacy, duet, stitch, comment, and max-duration constraints.
- Require explicit user consent immediately before the publish action, including TikTok-required music/commercial-content declarations.
- Track lifecycle states separately: `uploaded`, `sent_to_inbox`, `processing`, `moderating`, `publicly_available`, `failed`, and `not_public`.
- Do not mark a post as successful until status/webhook confirms the appropriate endpoint outcome.

**Detection:**
- Status remains private, inbox-delivered, or processing while LocalPilot UI says published.
- `reached_active_user_cap`, `spam_risk_too_many_posts`, `scope_not_authorized`, `access_token_invalid`, or media validation failures appear.
- Public `post_id` is missing because moderation has not completed or the post is not public.

### Pitfall 4: Missing TikTok Quota, Privacy, and Media Constraints

**What goes wrong:** The generator creates media or copy TikTok refuses, retries aggressively, or presents unavailable privacy settings.

**Why it happens:** TikTok enforces request limits per access token, active-user/posting caps, media format requirements, chunking rules, URL ownership checks for pull-from-URL transfers, creator-specific duration limits, moderation, spam/risk checks, and commercial content disclosure rules.

**Consequences:**
- Bulk pilot posting trips active-creator caps or creator daily caps.
- Media uploads fail because format, frame rate, picture size, duration, chunk size, or source URL rules were not validated before upload.
- Retries amplify rate limits and can look like spam.
- Local businesses lose trust because the product cannot explain why a TikTok post did not publish.

**Prevention:**
- Add a preflight validator for video/photo dimensions, duration, codec/container, size, chunking, URL ownership, HTTPS/no-redirect access, and caption length.
- Rate-limit per merchant, per creator, per access token, and per app.
- Use exponential backoff only for retryable platform/server failures; do not retry `auth_removed`, spam/risk, banned, scope, or validation failures.
- Keep generated caption limits platform-specific: TikTok video captions are capped differently from photo post titles/descriptions.
- Store raw platform error code, safe merchant-facing summary, retryability, and next action.

**Detection:**
- High volume of deterministic media validation failures.
- Retries on non-retryable spam/auth/policy failures.
- Merchant support tickets say "TikTok says nothing happened" while LocalPilot status only has a generic failed flag.

### Pitfall 5: Shipping Xiaohongshu Direct Publishing Without an Official Route

**What goes wrong:** LocalPilot promises Xiaohongshu "publish" using cookie/browser automation, unofficial APIs, or scraped private endpoints because official organic note publishing for third-party SaaS is not confirmed.

**Why it happens:** Xiaohongshu has official open/commercial surfaces, but the confirmed public surfaces found in this research are oriented around Marketing API/ad operations, account/fund management, data insights, ad campaign/creative management, Pugongying creator collaboration, private-message/business services, mini-app/merchant operations, and partner/sandbox workflows. This does not equal a general third-party organic note publishing API for arbitrary local merchants.

**Consequences:**
- Merchant accounts can be rate-limited, challenged, banned, or locked.
- LocalPilot handles cookies/session data it should never possess.
- Browser automation breaks whenever Xiaohongshu changes UI, anti-bot checks, login flows, captcha, upload widgets, or review flows.
- Sales claims become misleading: the product cannot guarantee compliant publishing.

**Prevention:**
- Mark Xiaohongshu as `assisted` or `deferred` in the roadmap until an official/partner publishing route is confirmed in writing.
- Build Xiaohongshu value as content-package generation first: RED-native title, note body, cover text, image/video checklist, hashtag/keyword plan, geo hints, disclosure/compliance reminders, and KOL/KOC brief.
- If pursuing official access, run a separate partner-discovery phase: identify required entity type, account type, minimum spend/revenue, service-provider eligibility, sandbox access, app review, and permitted write actions.
- Do not call third-party "XHS API" vendors production-ready unless they can prove authorization from Xiaohongshu for the exact merchant-owned publishing action.

**Detection:**
- The API vendor asks for cookies, QR-login sessions, browser profile reuse, or manual account credentials.
- The claimed API only reads notes, search, comments, creator analytics, ads, or mini-app data but does not document permitted organic note creation.
- Documentation uses terms like reverse engineering, app protocol, crawler, browser mode, session reuse, or no official authorization.

### Pitfall 6: Accepting Scraping, Cookies, or Browser Automation for Production Merchant Publishing

**What goes wrong:** The team treats browser-session tools such as AutoCLI-style adapters as a shortcut to support Xiaohongshu, TikTok, Instagram, or Facebook publishing.

**Why it happens:** Browser automation can appear to work in a demo. AutoCLI's GitHub README advertises browser-session reuse, Chrome extension support, and browser-mode commands including `xiaohongshu publish`, plus browser-mode actions for major social platforms. That is useful as a research or personal automation signal, but it is not a compliant production publishing integration for merchant accounts.

**Consequences:**
- LocalPilot would need to collect or reuse logged-in browser sessions, cookies, or credentials.
- Posting behavior can violate platform terms, trigger anti-abuse systems, and create merchant account liability.
- There is no stable API contract, permission grant, platform audit, platform webhook, SLA, or supported error taxonomy.
- Audit logs become unreliable because the platform sees a human browser session, not an authorized API client acting under explicit scoped consent.

**Prevention:**
- Ban cookie/session/browser automation from production publishing in the architecture decision record.
- Allow browser automation only for internal research against owned test accounts, never for customer credentials or live merchant accounts.
- For restricted platforms, ship assisted publishing: downloadable package, QR/deep-link handoff, mobile checklist, and owner-confirmed manual post completion.
- Require a platform-approved API, official partner program, or documented service-provider contract before any "direct publish" claim.

**Detection:**
- Integration asks the merchant to keep a browser open, install an extension, scan QR login for LocalPilot's server, upload cookies, or share a password.
- Failures manifest as CAPTCHA, UI selector errors, "not logged in", invisible publish button, or unexplained account challenge.

### Pitfall 7: Keeping OAuth Tokens, Campaign Inputs, or PII in localStorage

**What goes wrong:** The frontend prototype evolves into production while continuing to persist sensitive data in browser storage.

**Why it happens:** Current codebase concerns show the app is frontend-only and stores demo session, pilot request, and campaign state in `localStorage`. That is acceptable for a demo, but not for OAuth tokens, refresh tokens, Page IDs tied to merchants, approval trails, generated offers, customer audience notes, or personal contact data.

**Consequences:**
- XSS or browser compromise can expose Page/TikTok tokens and merchant data.
- Logout/reset does not reliably clear all persisted keys.
- There is no server-side audit trail for who approved a post.
- Tokens cannot be rotated, revoked, encrypted, or monitored centrally.

**Prevention:**
- Introduce a backend before any live OAuth integration.
- Store only non-sensitive UI preferences in `localStorage`.
- Put OAuth state, PKCE verifier/session binding, token exchange, refresh, encryption, and revocation on the server.
- Add central storage key management and migration for remaining browser state.
- Add Content Security Policy and avoid any HTML injection path when rendering generated copy.

**Detection:**
- Any key named like `access_token`, `refresh_token`, `page_token`, `oauth`, `session`, or merchant PII appears in browser storage.
- Support/debug screenshots reveal token-bearing URLs or localStorage payloads.

### Pitfall 8: Retrying Publish Jobs Without Idempotency or Audit Discipline

**What goes wrong:** A transient platform error or worker restart causes duplicate posts, missing status updates, or repeated policy-triggering attempts.

**Why it happens:** Publishing is asynchronous and platform-dependent. TikTok has statuses and webhooks; Facebook posting can succeed even if the LocalPilot worker times out before recording the platform post ID. Naive retries are dangerous because "timeout" does not mean "not published."

**Consequences:**
- Duplicate merchant posts go live.
- A failed moderation/policy result is retried until the account looks spammy.
- LocalPilot cannot prove which owner approved which final text/media.
- Audit logs leak content, tokens, or platform error payloads.

**Prevention:**
- Use a server-side publish job table with idempotency keys, platform request IDs, platform post IDs, publish attempt numbers, and terminal states.
- Record immutable approval snapshots: final caption, media asset IDs/checksums, selected account/Page, selected privacy/disclosure settings, approver, timestamp, and platform target.
- Redact tokens, authorization headers, signed upload URLs, cookies, and PII from logs.
- Store platform raw error codes with redacted payloads; expose safe summaries to merchants.
- Build retry policy per error class: retry only transient network/5xx/platform-internal errors with backoff and max attempts.

**Detection:**
- Same approved draft creates multiple platform posts.
- Job table has `publishing` rows with no timeout policy or recovery path.
- Logs include bearer tokens, upload URLs, cookies, or full OAuth redirects.

## Moderate Pitfalls

### Pitfall 1: Over-Scoping the First Facebook Review

**What goes wrong:** The app asks Meta for ads, inbox, insights, engagement management, Instagram, or business-management permissions before the product has visible implementations.

**Prevention:** Submit the smallest reviewable Page publishing use case first. Add later scopes in later phases with separate screencasts and working UI.

### Pitfall 2: Confusing Organic Publishing With Paid Ads

**What goes wrong:** Xiaohongshu Marketing API or Meta Marketing API capabilities are interpreted as proof that organic content publishing is available.

**Prevention:** Keep organic Page/feed publishing, ad campaign management, creator marketplace workflows, and merchant mini-app/e-commerce workflows as separate integration categories.

### Pitfall 3: Ignoring Platform-Native Disclosure Rules

**What goes wrong:** LocalPilot generates promotional content but does not force the owner to set commercial, branded, AI-generated, or paid partnership disclosure controls where required.

**Prevention:** Make disclosure fields first-class draft metadata. The publish screen must show platform-specific required toggles before final approval.

### Pitfall 4: Treating "Published" as a Single State

**What goes wrong:** Product reports success even when content is uploaded, pending, private, inbox-delivered, failed moderation, or no longer public.

**Prevention:** Use platform-specific lifecycle states and map them to clear merchant-facing states only after webhook/status reconciliation.

## Minor Pitfalls

### Pitfall 1: Caption and Media Limits Hidden Until Publish

**What goes wrong:** Owners approve copy or media that fails only at publish time.

**Prevention:** Add client and server validators before approval. Prevent approval of invalid media/caption combinations for each platform.

### Pitfall 2: No Reconnect UX

**What goes wrong:** Token revocation or Page permission changes show up as unexplained failures.

**Prevention:** Add connected-channel health checks, reconnect prompts, and admin-only account settings.

### Pitfall 3: No Test Account/Test Page Discipline

**What goes wrong:** Developers test with personal assets and cannot reproduce review conditions.

**Prevention:** Maintain dedicated Meta test Page, TikTok creator test account, sample merchant workspace, and fixture media that satisfy platform constraints.

## Xiaohongshu Publishing Feasibility Assessment

**Verdict:** MAYBE later, but not ready for v1 direct publishing.

**Reasoning:** Official Xiaohongshu surfaces found during this research support commercial ecosystem workflows: Marketing API/open platform functions for account management, data insights, ad placement/campaign/creative management, Pugongying creator collaboration data, private-message/business services, mini-app capabilities, merchant/sandbox workflows, professional account/store operations, and business promotion products. These are legitimate official or partner-adjacent routes, but they do not confirm a general third-party SaaS API that can publish organic Xiaohongshu notes on behalf of arbitrary local merchant accounts.

**Product implication:** Xiaohongshu should remain in the product as a differentiated strategy/content package module, not as a direct publishing promise. The roadmap should require a Xiaohongshu partner-access spike before engineering any account connection or publish job. Until then, the compliant workflow is assisted publishing: generate final RED-native materials and have the merchant post manually through their own Xiaohongshu app/account.

**What would change the decision:**
- Written documentation or partner confirmation that LocalPilot may create organic notes for merchant-owned accounts through an official API.
- Clear eligibility requirements for LocalPilot as a service provider or the merchant as a professional/enterprise account.
- Sandbox and production approval process.
- Documented scopes/actions, rate limits, content review behavior, token model, and compliance terms.
- Confirmation that the API route is not limited to ads, mini-app content, creator marketplace, store/product management, analytics, or private messages.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Phase 1: Backend foundation | OAuth/token data gets modeled as generic user preferences | Create server-side auth, connected accounts, encrypted token storage, publish jobs, approval snapshots, and audit tables before any platform integration |
| Phase 2: Facebook connection | App Review blocks production merchant Pages | Implement Page selection, minimum permissions, test Page, review screencast, permission explanations, token validation, and reconnect UX |
| Phase 3: Facebook publishing | Wrong token/permission/target causes publish failures | Support Pages only; verify Page access token and Page task permissions; preflight post type; record platform post ID and idempotency key |
| Phase 4: TikTok upload/draft | Product overpromises public Direct Post before audit | Start with Upload-to-Draft or private test mode; only enable Direct Post after scope approval/audit; expose actual platform state |
| Phase 5: TikTok Direct Post | Privacy/disclosure/media constraints are not enforced | Query creator info for every publish; validate media; render privacy/comment/duet/stitch/commercial/AI controls; use webhooks/status polling |
| Phase 6: Assisted Xiaohongshu | "Assisted" becomes hidden automation | Build export/checklist/QR/deep-link handoff only; no cookies, no browser session reuse, no password capture, no unofficial write APIs |
| Phase 7: Xiaohongshu partner spike | Ads/analytics API is mistaken for organic note publishing | Require proof of permitted organic note creation; document eligibility, scopes, review, token model, and legal/compliance obligations before roadmap promotion |
| Cross-phase: AI generation | Generated copy creates compliance or platform-risk issues | Add platform-specific policy/disclosure checks, prohibited claims, regulated-industry warnings, and owner approval before publishing |
| Cross-phase: Observability | Logs leak secrets or cannot reconstruct approvals | Redact secrets; store immutable approval snapshots and safe platform error metadata; keep retention policy for audit logs |

## Production Requirements Before "Real Publishing" Launch

1. Backend API and database exist; no live platform token is stored in browser `localStorage`.
2. OAuth callback, state/PKCE, token exchange, token refresh/revocation, and reconnect flows are server-owned.
3. Merchant explicitly approves final text, media, target account/Page, privacy/disclosure settings, and platform before any publish job is queued.
4. Publish jobs are idempotent, asynchronous, status-driven, and retry-aware.
5. Platform-specific preflight validation runs before approval and again before publish.
6. Audit logs capture who approved what and when, without storing bearer tokens, cookies, or signed upload URLs.
7. Merchant-facing status distinguishes draft, approved, queued, publishing, inbox/draft delivered, moderation pending, public, private/not public, failed retryable, failed terminal, and reconnect required.
8. Xiaohongshu direct publishing is hidden or labeled "deferred" until official/partner feasibility is confirmed.

## Source Notes

**Source confidence note:** The `gsd-tools` research-plan/classify-confidence seam was unavailable in this workspace (`gsd-tools: command not found`), so confidence is assigned from source type and cross-checking: official platform documentation is HIGH; recent third-party developer summaries used only where official Meta pages were login-gated are MEDIUM.

### Official / High-Confidence Sources

- TikTok Content Posting API - Direct Post: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- TikTok Content Posting API - Query Creator Info: https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info
- TikTok Content Posting API - Media Transfer Guide: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
- TikTok Content Posting API - Get Post Status and webhooks: https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status
- TikTok Content Sharing Guidelines: https://developers.tiktok.com/doc/content-sharing-guidelines/
- Xiaohongshu commercial/open platform Marketing API landing page: https://ad-market.xiaohongshu.com/
- Xiaohongshu mini-app open platform: https://redopen.xiaohongshu.com/
- Xiaohongshu Ark/open platform integration guide: https://school.xiaohongshu.com/en/open/quick-start/workflow.html
- Xiaohongshu Ark/open platform basic parameters: https://school.xiaohongshu.com/en/open/quick-start/system-parameter.html
- Xiaohongshu Ark/open platform contact/sandbox support: https://school.xiaohongshu.com/en/open/contact.html
- Xiaohongshu professional account/store rules: https://school.xiaohongshu.com/helper/detail/1935?jumpFrom=cn
- Xiaohongshu Pugongying help center and compliance/rule categories: https://pgy.xiaohongshu.com/help/home

### Medium-Confidence / Corroborating Sources

- Meta Pages API posts official page checked but login-gated during research: https://developers.facebook.com/docs/pages-api/posts/
- Meta App Review official page checked but login-gated during research: https://developers.facebook.com/docs/app-review/
- Meta `pages_manage_posts` permission official page checked but login-gated during research: https://developers.facebook.com/docs/permissions/reference/pages_manage_posts/
- Current Facebook Graph API posting guide summarizing Page endpoints, Page tokens, Business Verification, and App Review: https://postproxy.dev/blog/facebook-graph-api-posting-guide/
- Stack Overflow answer quoting Meta Pages API permission requirements for Page posts and Page tasks: https://stackoverflow.com/questions/77875862/for-graph-api-what-are-the-permissions-reqd-for-creating-a-post-on-a-facebook/77876312
- AutoCLI GitHub README showing browser-session reuse and browser-mode Xiaohongshu `publish` capability: https://github.com/nashsu/AutoCLI

