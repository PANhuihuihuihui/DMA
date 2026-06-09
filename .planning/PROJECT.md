# LocalPilot AI

## What This Is

LocalPilot AI is an AI marketing operator for local small businesses that turns one promotion, service, product, or content idea into platform-native social posts. The next stage focuses on making publishing real: business owners connect their official accounts, generate Facebook and TikTok posts, review the output, and publish from one workflow.

The product is not trying to become a generic scheduler. Its wedge is local-business growth: strategy-aware content, platform-specific copy, owner approval, and eventually a feedback loop from posts to calls, bookings, DMs, coupons, and walk-ins.

## Core Value

A local business owner can go from one marketing idea to approved, platform-native Facebook and TikTok posts published through their own official accounts with minimal effort.

## Requirements

### Validated

- [done] Public marketing landing page exists with a local-business AI marketing operator story - existing
- [done] Post-login demo workspace exists for reviewing campaign modules and generated plans - existing
- [done] Demo campaign planner can shape one business input into platform-specific channel plans, including Facebook, TikTok, and Xiaohongshu concepts - existing
- [done] Owner approval and request-change interactions exist as prototype behavior - existing
- [done] Local ROI concepts such as calls, bookings, DMs, coupon scans, saves, and map clicks are represented in product docs and demo surfaces - existing
- [done] Static deployment package flow exists for the current React/Vite demo - existing

### Active

- [ ] Ship a real publishing foundation that can persist business accounts, connected channels, campaign drafts, publishing status, and errors outside browser localStorage.
- [ ] Support official Facebook Page publishing as the first production integration.
- [ ] Support official TikTok publishing or upload-to-draft as the second production integration.
- [ ] Let a merchant connect their own official Facebook and TikTok accounts rather than publishing through a shared LocalPilot account.
- [ ] Let a merchant enter one offer/service/promotion and generate platform-native Facebook and TikTok post drafts.
- [ ] Let a merchant review generated posts, edit or request regeneration, and publish only after explicit approval.
- [ ] Track publishing lifecycle states: draft, needs review, approved, publishing, published, failed, and retry needed.
- [ ] Evaluate open CLI, MCP, or self-hosted publishing engines, especially Postiz-style tools, before building a custom publishing request layer.
- [ ] Keep Xiaohongshu as a later-stage integration unless a compliant official or partner publishing path is confirmed.

### Out of Scope

- Direct Xiaohongshu publishing in the first implementation phase - official/general SaaS publishing access is uncertain, so it should not block Facebook and TikTok.
- Paid ads / ad campaign publishing - the current goal is organic post publishing, not ad buying.
- Instagram and Google Business Profile publishing in v1 - valuable later, but Facebook and TikTok define the first real publishing milestone.
- Scraping, reverse engineering, or cookie-based posting for restricted platforms - too fragile and risky for a product used by local merchants.
- Fully autonomous publishing without merchant approval - local businesses need trust, brand control, and a visible approval step.
- Enterprise agency workflow, white-label reporting, and multi-location franchise controls - defer until the core merchant publishing loop works.

## Context

The existing repository is a frontend-only React/Vite prototype. `src/main.jsx` contains the landing page, fake login, app demo, deterministic campaign generation, localStorage persistence, and module views. `src/styles.css` contains the global visual system. There is no backend API, database, external auth provider, live AI provider, or live social publishing integration.

The current demo already communicates the right wedge: local-business marketing, not generic social scheduling. `README.md` describes LocalPilot AI as an AI marketing operator for local small businesses, and the existing feature review highlights publishing/export workflows, platform integrations, approval queues, and local ROI as the missing systems that make the demo real.

The prior roadmap documents recommended assisted publishing before API publishing because platform integrations are hard. The current product decision intentionally changes the next-stage priority: real publishing should be explored now, with Facebook first and TikTok second, because both have official API paths and because working publishing is the clearest proof point for local merchant field sales.

The integration strategy should be CLI-first where practical. Rather than immediately rebuilding every social platform request flow in a custom backend, the project should evaluate reusable open publishing infrastructure such as Postiz-style CLI/Public API/MCP tooling. If a tool already handles account integrations, media upload rules, platform-specific schemas, scheduling, and publishing status well enough, LocalPilot should wrap or self-host that capability and focus its own code on merchant onboarding, local-business campaign generation, approval UX, and ROI feedback.

Xiaohongshu remains strategically important for cross-cultural/local Chinese consumer reach, but it is no longer part of the first publishing scope. It should be represented as a deferred integration and research risk until a compliant official, partner, or semi-automated route is validated.

## Constraints

- **Tech stack**: Current app is React/Vite with JavaScript and CSS in `src/main.jsx` and `src/styles.css` - near-term work must either extend this carefully or introduce a backend boundary deliberately.
- **Existing architecture**: The app is frontend-only and stores demo state in localStorage - real publishing requires server-side persistence, token handling, or a self-hosted publishing engine boundary.
- **Security**: OAuth secrets, refresh tokens, API keys, and merchant account credentials must never live in browser localStorage or committed files.
- **Platform priority**: Facebook is first, TikTok second, Xiaohongshu third/deferred - roadmap and requirements should reflect this ordering.
- **Integration reuse**: Evaluate CLI/MCP/self-hosted publishing tools before writing custom platform-specific request code.
- **Compliance**: Use official API paths for Facebook and TikTok; do not rely on scraping, browser automation, or cookie posting for production publishing.
- **Sales readiness**: The output must support local field sales: a merchant should understand the value quickly and see a credible path from offer to published post.
- **Owner control**: Publishing must require explicit user approval before posts are sent.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Prioritize Facebook first | Facebook Page publishing is important for local merchants and has an official API path. | - Pending |
| Prioritize TikTok second | TikTok is core to local discovery and has official publishing/upload paths worth validating after Facebook. | - Pending |
| Defer Xiaohongshu direct publishing | API availability and compliance are uncertain, so it should not block the first real publishing milestone. | - Pending |
| Build toward merchant-owned official accounts | Field-sales customers should connect their own business accounts rather than relying on a shared agency account. | - Pending |
| Use explicit approval before publishing | Local businesses need brand safety and trust before automation posts publicly. | - Pending |
| Investigate CLI/MCP publishing engines before custom API wrappers | Reusing Postiz-style infrastructure may avoid duplicating platform request logic and reduce integration risk. | - Pending |
| Keep paid ads out of v1 | The immediate goal is organic post publishing, not ad buying or ad optimization. | - Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-09 after initialization*
