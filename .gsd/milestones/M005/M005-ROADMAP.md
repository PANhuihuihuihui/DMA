# M005: Platform Auth and E2E Connectivity

**Vision:** Every supported platform (Facebook, Instagram, TikTok, Xiaohongshu) has a real, tested OAuth flow modeled on AiToEarn's AuthProvider pattern with token refresh, expiry tracking, and credential-refresh-on-publish. All platform connections verified end-to-end with contract tests. Priority order: Facebook hardening, Instagram, TikTok, Xiaohongshu.

## Success Criteria

- Shared AuthProvider base class with build_auth_url, exchange_code, refresh, revoke, get_profile, list_selectable_accounts
- OAuth sessions persisted in DB with TTL instead of in-memory dicts
- get_valid_credential pattern checks expiry with 60s buffer before every publish
- run_with_credential_refresh wrapper retries once on auth failure with forced refresh
- Facebook: fb_exchange_token long-lived swap, expiry tracking, refresh-before-publish
- Instagram: two-step short-to-long-lived token exchange, Graph API container publishing
- TikTok: PKCE OAuth flow, rotating refresh tokens, real Content Posting API replacing stub
- Xiaohongshu: viable integration path implemented (official API or plugin approach)
- Contract tests for each AuthProvider implementation covering auth URL, code exchange, token refresh, profile fetch
- E2E smoke tests verifying full redirect-callback-store-publish flow per platform

## Slices

- [ ] **S01: AuthProvider Abstraction and Session Persistence** `risk:medium` `depends:[]`
  > After this: Facebook OAuth still works end-to-end but now uses DB sessions and the new base class. Token expiry is tracked and logged.

- [ ] **S02: Facebook Auth Hardening** `risk:low` `depends:[S01]`
  > After this: Facebook OAuth exchanges short-lived token for long-lived, tracks expiry, refreshes proactively before publish.

- [ ] **S03: Instagram OAuth and Container Publishing** `risk:medium` `depends:[S01]`
  > After this: Instagram OAuth connects, token stored as long-lived. Single image and carousel publish via container model with status polling.

- [ ] **S04: TikTok OAuth with PKCE and Real Publishing** `risk:high` `depends:[S01]`
  > After this: TikTok OAuth connects with PKCE, token stored with rotating refresh. Video publish hits real Content Posting API instead of returning mock data.

- [ ] **S05: Xiaohongshu Integration Research and Implementation** `[sketch]` `risk:high` `depends:[S01]`
  > After this: Either working Xiaohongshu OAuth and basic post publish, or a documented decision with evidence on why plugin approach is the viable path.

- [ ] **S06: E2E Auth Test Suite and Cross-Platform Verification** `risk:low` `depends:[S02,S03,S04]`
  > After this: Test suite runs green covering all 4 platforms auth flows. Connectivity matrix shows each platform status.

## Boundary Map

Not provided.
