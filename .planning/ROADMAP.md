# Roadmap: LocalPilot AI

## Overview

LocalPilot AI moves from a frontend-only React/Vite demo into a real merchant-owned publishing MVP. The work starts by adding backend-owned publishing records, approval snapshots, status tracking, and a fake adapter while preserving the current demo. A Postiz-style publishing engine spike happens before deep custom provider wrappers. The MVP then delivers local campaign drafting, Facebook Page publishing first, TikTok upload/draft publishing second, and manual support workflows for blocked jobs. Xiaohongshu remains deferred to v2 until a compliant official or partner publishing route is proven.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Backend Publishing Foundation** - Adds API-backed workflow state, fake publishing, approval snapshots, status tracking, and preserves the current demo.
- [ ] **Phase 2: Publishing Engine Reuse Decision** - Spikes Postiz-style engine reuse and rejects AutoCLI-style production publishing before custom provider wrappers.
- [ ] **Phase 3: Local Campaign Draft Workbench** - Turns one local offer into editable, platform-native Facebook and TikTok drafts with media and local CTA context.
- [ ] **Phase 4: Facebook Page Publishing** - Connects merchant-owned Facebook Pages and publishes approved Facebook drafts first.
- [ ] **Phase 5: TikTok Upload And Direct-Post Gates** - Connects TikTok second and delivers approved TikTok drafts through official upload/draft paths while gating Direct Post.
- [ ] **Phase 6: Manual Fallback And Pilot Support** - Gives merchants and operators safe paths for blocked jobs, manual packages, retries, and diagnostics.

## Phase Details

### Phase 1: Backend Publishing Foundation

**Goal**: LocalPilot has API-backed publishing records, a fake publish lifecycle, approval snapshots, retry-safe status tracking, and preserved current demo/marketing routes.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, SEC-01, SEC-02, SEC-03, SEC-04, SEC-06, APPR-04, APPR-05, APPR-06, STATUS-01, STATUS-02
**Success Criteria** (what must be TRUE):

  1. Merchant can keep using the existing marketing page and demo workspace while publish-critical records are persisted through backend APIs instead of browser localStorage.
  2. Merchant can approve a specific platform draft version and see the frozen payload snapshot that will be used for publishing.
  3. Merchant can run a fake publish job through draft, approved, queued, publishing, published, failed, and retry-needed states with a visible per-platform timeline.
  4. Retrying an approved fake publish job records a new immutable attempt without duplicating the approved external outcome.
  5. Support-visible diagnostics and events show approver, draft version, timestamps, and redacted provider details without exposing tokens or secrets.

**Plans**: TBD
**UI hint**: yes

### Phase 2: Publishing Engine Reuse Decision

**Goal**: The team can decide whether to wrap Postiz-style publishing infrastructure or build native adapters before deep provider-specific request wrappers.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: ENGINE-01, ENGINE-02, ENGINE-03, ENGINE-04, ENGINE-05, SEC-05
**Success Criteria** (what must be TRUE):

  1. Team can run a focused Postiz-style self-hosted/API/MCP spike against the PublishingProvider contract without changing LocalPilot workflow records.
  2. Spike evidence shows whether Postiz-style tooling can connect Facebook Pages, handle TikTok upload or posting flows, submit media, return status, expose errors, and fit licensing/deployment needs.
  3. A documented go/no-go decision selects Postiz-style wrapping or native provider adapters before deep Facebook or TikTok custom request wrappers are built.
  4. Production publishing paths reject scraping, cookie-based posting, and AutoCLI/browser-session automation, with AutoCLI allowed only for internal research if needed.

**Plans**: TBD

### Phase 3: Local Campaign Draft Workbench

**Goal**: Merchant can enter one local business offer and produce editable, platform-native Facebook and TikTok draft records with local CTAs, risk checks, and media references.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: CAMP-01, CAMP-02, CAMP-03, CAMP-04, CAMP-05, CAMP-06, LOCAL-01, LOCAL-02, LOCAL-03, LOCAL-04, LOCAL-05, LOCAL-06, APPR-01, APPR-02, APPR-03, MEDIA-01, MEDIA-02, MEDIA-05
**Success Criteria** (what must be TRUE):

  1. Merchant can enter one local offer, service, product, event, or promotion plus business context such as industry, location, audience, tone, languages, services, and goals.
  2. Merchant can view separate editable Facebook and TikTok draft records side by side, each with platform-native copy, CTA context, and local ROI metadata.
  3. Merchant can regenerate or request revision of a platform draft while prior versions remain available for audit and comparison.
  4. Merchant can attach or reference media stored server-side and see actionable media validation errors before approval.
  5. Drafts can include English, Chinese, or bilingual variants and flag risky claims, unsupported guarantees, regulated phrasing, or missing disclaimers without requiring Xiaohongshu direct publishing.

**Plans**: TBD
**UI hint**: yes

### Phase 4: Facebook Page Publishing

**Goal**: Merchant can connect an official Facebook Page and publish approved Facebook drafts first through the selected Page, with retry/fallback and support diagnostics.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: ACCT-01, ACCT-02, ACCT-03, FB-01, FB-02, FB-03, FB-04, FB-05, FB-06, MEDIA-03
**Success Criteria** (what must be TRUE):

  1. Merchant can start official Facebook connection, select a managed Page, and see whether that Page has required publishing capability before jobs are allowed.
  2. Approved text-only Facebook Page drafts publish through the merchant-selected Page when required permissions are available.
  3. Approved Facebook Page drafts with links or media publish when Facebook media validation passes, and validation errors are shown before job creation.
  4. Merchant can see stored Facebook post IDs, public URLs or provider references, normalized failure classes, and Page-specific retry, reconnect, or manual fallback actions.
  5. The Meta app, permissions, app review, test Page, and screencast evidence needed for Facebook Page publishing are documented for production readiness.

**Plans**: TBD
**UI hint**: yes

### Phase 5: TikTok Upload And Direct-Post Gates

**Goal**: Merchant can connect TikTok second, use creator-info driven settings, and deliver approved TikTok drafts through official upload/draft paths, with Direct Post gated.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: ACCT-04, ACCT-05, ACCT-06, ACCT-07, TT-01, TT-02, TT-03, TT-04, TT-05, TT-06, TT-07, MEDIA-04
**Success Criteria** (what must be TRUE):

  1. Merchant can start official TikTok connection and see connected-channel health for Facebook and TikTok, including reconnect-required, missing-permission, expired-token, or review-blocked states.
  2. Merchant can disconnect Facebook or TikTok accounts and new publish jobs stop using that connection.
  3. Merchant can choose TikTok privacy and interaction options returned by creator-info APIs and explicitly confirm disclosure settings before approval or publishing.
  4. Approved TikTok drafts can be delivered through official Upload-to-Inbox or draft-style flow after TikTok media validation, with publish IDs, status responses, and provider diagnostics stored.
  5. TikTok failures are classified by authentication, scope, creator setting mismatch, media validation, rate limit, audit/visibility block, platform transient, or unknown error, and Direct Post only becomes available when all official gates are satisfied.

**Plans**: TBD
**UI hint**: yes

### Phase 6: Manual Fallback And Pilot Support

**Goal**: Merchant and internal operator can resolve blocked publish jobs safely through manual packages, completion tracking, redacted diagnostics, and support actions.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: STATUS-03, STATUS-04, STATUS-05, ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04
**Success Criteria** (what must be TRUE):

  1. Merchant can see when direct publishing is blocked by official API access, review status, account eligibility, or media constraints and is marked manual fallback required.
  2. Merchant can download or copy a platform manual publishing package with caption, hashtags, CTA, media checklist, disclosure notes, and instructions.
  3. Merchant can mark a manual fallback package as completed and see the platform draft timeline reflect manual completion.
  4. Internal operator can inspect merchant, channel, job, attempt, and error status with redacted provider IDs, trace IDs, error classes, next recommended action, and app-review evidence.
  5. Internal operator can trigger safe retry or mark a manual support path without viewing tokens or secrets.

**Plans**: TBD
**UI hint**: yes

## Coverage

All 69 v1 requirements are mapped to exactly one phase. Facebook production integration is sequenced before TikTok. Xiaohongshu direct publishing remains deferred to v2.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Publishing Foundation | 6/9 | In Progress|  |
| 2. Publishing Engine Reuse Decision | 0/TBD | Not started | - |
| 3. Local Campaign Draft Workbench | 0/TBD | Not started | - |
| 4. Facebook Page Publishing | 0/TBD | Not started | - |
| 5. TikTok Upload And Direct-Post Gates | 0/TBD | Not started | - |
| 6. Manual Fallback And Pilot Support | 0/TBD | Not started | - |

---
*Roadmap created: 2026-06-09*
