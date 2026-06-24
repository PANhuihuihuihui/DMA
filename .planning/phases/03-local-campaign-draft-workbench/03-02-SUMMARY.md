---
phase: 03-local-campaign-draft-workbench
plan: 03-02
status: partial
subsystem: ui
tags: [react, vite, phase3, predis-reference, brand-kit, publishing-boundary]

requires:
  - phase: 03-local-campaign-draft-workbench
    provides: Phase 3 backend-owned workspace records and broad Predis-style demo surface from 03-01.
provides:
  - Logged-in Predis-reference app shell with LocalPilot-safe navigation labels and aliases.
  - Create New, Ad Inspirations, Content Library, publish modal, Calendar, Brand & Social Accounts, Analytics, and Help parity surfaces.
  - Backend-persisted safe brand metadata fields without browser-readable token material.
  - Updated backend and screen test coverage for the reference-clone hardening slice.
affects: [phase3, phase4-facebook-hardening, sales-demo, ui-smoke]

tech-stack:
  added: []
  patterns:
    - Data-driven React demo surfaces in src/main.jsx.
    - Backend-owned safe brand metadata with additive SQLite migrations.
    - UI-only placeholders for unsupported integrations and assisted publishing paths.

key-files:
  created:
    - .planning/phases/03-local-campaign-draft-workbench/03-02-PREDIS-REFERENCE-CHECKLIST.md
    - .planning/phases/03-local-campaign-draft-workbench/03-02-SUMMARY.md
  modified:
    - .planning/phases/03-local-campaign-draft-workbench/.continue-here.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - backend/app/store.py
    - backend/tests/test_phase3_workspace.py
    - scripts/smoke-phase3-screens.mjs
    - src/main.jsx
    - src/styles.css

key-decisions:
  - "LocalPilot should mirror the logged-in workflow structure, not Predis identity, trademarks, or exact creative assets."
  - "Predis-style auto-posting is reframed as an owner-approved weekly autoplan so explicit merchant approval remains required."
  - "Brand/account parity fields are safe business metadata only; OAuth tokens and credentials remain outside browser storage and committed files."

patterns-established:
  - "Legacy module aliases map old Phase 3 routes to new logged-in product labels so existing links and smoke entrypoints keep working."
  - "Unsupported channels and integrations render as honest assisted/demo placeholders until official credential and API boundaries exist."

requirements-completed: []

duration: ~2h
completed: 2026-06-22
---

# Phase 03 Plan 02: Predis Logged-In Reference Clone Hardening Summary

**Logged-in Predis-reference workflow parity with LocalPilot-safe owner approval, official account boundaries, and proof-loop evidence.**

## Performance

- **Duration:** ~2h active continuation in this session, plus prior implementation work before compaction
- **Started:** 2026-06-22T00:58:34Z
- **Completed:** 2026-06-22T01:26:14Z
- **Tasks:** 12 reference-hardening slices covered
- **Files modified:** 9 primary files plus planning artifacts

## Accomplishments

- Reworked the app shell around visible logged-in product labels: Create New, Auto Posting, Ad Inspirations, Content Library, Content Calendar, Brand & Social Accounts, Competitor Analysis, Analytics, and Need help.
- Added Create New format cards for Image, UGC, Short Ad Video, Carousel, Faceless Video, and Product Photo Shoot, including Image/UGC source methods and Carousel style/aspect configuration.
- Added Ad Inspirations sections with category chips, UGC/Image cards, and Recreate actions that seed LocalPilot campaigns.
- Made Content Library the central generated-card grid with type/search/date/tag/user/source/archive controls, watermark/status affordances, cooking overlay, and Publish entry.
- Added publish/schedule modal gating for platform/post-type compatibility, unsupported media, missing account routes, assisted package path, and owner-approved weekly autoplan confirmation.
- Upgraded Content Calendar with Weekly/Monthly controls, Today, timezone, status legend, scheduled-post detail drawer, locked near-publish copy, Discard, and Reschedule.
- Rebuilt Brand & Social Accounts into Social Platforms, Brand Details, Style, Integrations, and Exports tabs, including a demo Facebook Page picker while preserving OAuth-safe boundaries.
- Extended backend brand kit persistence for safe metadata fields: website, social handle, hashtags, typography, logos, and integrations.
- Added Analytics posting streak, consistency grid, empty-state cards, and retained LocalPilot lower-bound proof-loop evidence.
- Added a local-only Help drawer with non-sending support draft behavior.
- Updated Phase 3 backend tests and screen smoke coverage for the logged-in reference flow.

## Task Commits

No commits were created in this continuation. The repository already had a large pre-existing dirty working tree spanning Phase 02/03 backend, frontend, routes, package files, and planning artifacts before this closeout, so staging an atomic 03-02-only commit would risk absorbing unrelated prior work.

## Files Created/Modified

- `.planning/phases/03-local-campaign-draft-workbench/03-02-PREDIS-REFERENCE-CHECKLIST.md` - Screenshot-derived feature mapping, scope classification, verification map, and guardrails.
- `.planning/phases/03-local-campaign-draft-workbench/03-02-SUMMARY.md` - This execution summary and verification record.
- `.planning/phases/03-local-campaign-draft-workbench/.continue-here.md` - Updated Phase 03 handoff to point at the remaining environment gate.
- `.planning/ROADMAP.md` - Updated Phase 03 plan count and inserted 03-02 as the logged-in reference hardening slice.
- `.planning/STATE.md` - Updated current position and blockers for 03-02 verification.
- `src/main.jsx` - Added logged-in navigation, Create New, Inspirations, Content Library, publish modal, Auto Posting, Calendar, Brand & Social Accounts, Analytics, Help, and supporting state/handlers.
- `src/styles.css` - Added responsive styles for the new logged-in product surfaces.
- `backend/app/store.py` - Added safe brand metadata schema, migrations, seed data, serialization, and update persistence.
- `backend/tests/test_phase3_workspace.py` - Added coverage for safe brand metadata loading and persistence.
- `scripts/smoke-phase3-screens.mjs` - Replaced the old nine-screen smoke with the logged-in reference flow and hardened format-card selectors.

## Decisions Made

- Workflow parity is the goal, not literal clone identity. LocalPilot can use similar product moments while avoiding Predis marks, exact copy, or template assets.
- Auto-posting remains approval-gated. The Predis upsell is represented as LocalPilot's owner-approved weekly autoplan rather than autonomous publishing.
- Account and integration parity stays honest. Facebook keeps the official OAuth path; other integrations are assisted/demo placeholders until production API boundaries are planned.
- Brand metadata can persist backend-side because it is non-secret merchant profile data; token and credential material remains excluded from browser storage and public payloads.

## Deviations from Plan

### Auto-fixed Issues

**1. Seed insert placeholder count**
- **Found during:** `npm run test:phase3`
- **Issue:** Brand kit seed insertion had 16 columns but only 15 placeholders after adding safe metadata fields.
- **Fix:** Updated the seed insert to use 16 placeholders.
- **Files modified:** `backend/app/store.py`
- **Verification:** `npm run test:phase3` passed after the fix.

**2. Smoke-test format-card selector fragility**
- **Found during:** Closeout review
- **Issue:** The Create New smoke used composed accessible names that depended on card text ordering.
- **Fix:** Switched to card text selectors for UGC and Carousel.
- **Files modified:** `scripts/smoke-phase3-screens.mjs`
- **Verification:** Static review completed; full smoke remains blocked by local Rollup runtime issue.

---

**Total deviations:** 2 auto-fixed
**Impact on plan:** Both changes were required for correctness or test stability and did not expand scope.

## Issues Encountered

- `npm run build`, `npm run dev:web`, and `npm run test:phase3-screens` are blocked in this local environment before app code runs. Rollup's native `@rollup/rollup-darwin-arm64/rollup.darwin-arm64.node` binary fails macOS signature validation with: `mapping process and mapped file (non-platform) have different Team IDs`.
- Attempted local repairs did not clear the issue: `npm install`, `npm rebuild @rollup/rollup-darwin-arm64`, `xattr -cr`, and ad-hoc signing with `codesign --force --sign -`.
- Current Node is `v24.14.0`; project stack expects Node `^20.19.0 || >=22.12.0`. A clean Node 22/20 install or Rollup native dependency reinstall outside this corrupted binary state is required before browser smoke/build can be rerun.

## Verification

- Passed: `npm run test:phase3`
- Passed: `python3 -m py_compile backend/app/server.py backend/app/facebook_oauth.py backend/app/facebook_publisher.py backend/app/store.py`
- Passed: Babel parser check for `src/main.jsx`
- Passed: esbuild bundle check for `src/main.jsx`
- Passed: `npm run test:storage-boundary`
- Passed: `npm run test:facebook-oauth`
- Passed: `python3 -m unittest discover backend/tests -v` (43 tests)
- Blocked by local Rollup native binary signature issue: `npm run build`
- Blocked by local Rollup native binary signature issue: `npm run test:phase3-screens`

## User Setup Required

None for the code changes. To complete local verification, repair the Node/Rollup environment and rerun:

```bash
npm run build
npm run test:phase3-screens
```

## Next Phase Readiness

Phase 4 should not start from this checkout until the Rollup runtime issue is fixed and both build and screen-smoke gates pass. Once those gates are green, the next product work is Facebook Page Publishing Hardening with encrypted/secret-managed token persistence, Page capability health, media validation, and app review evidence.

## Self-Check: FAILED

Implementation and backend/storage verification passed, but plan-level acceptance requires `npm run build` and `npm run test:phase3-screens`; both are currently blocked by the local Rollup native binary signature failure.

---
*Phase: 03-local-campaign-draft-workbench*
*Completed: 2026-06-22*
