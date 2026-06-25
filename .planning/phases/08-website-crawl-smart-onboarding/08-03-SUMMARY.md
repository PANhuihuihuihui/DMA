---
phase: 08-website-crawl-smart-onboarding
plan: 03
subsystem: onboarding
tags: [react, sqlite, minimax, onboarding, brand-kit, unittest]
requires:
  - phase: 08-website-crawl-smart-onboarding
    provides: backend crawl/profile endpoints and the authenticated onboarding card flow
provides:
  - full ONBOARD-03 coverage for onboarding voiceover and avatar defaults
  - confirmed brand-kit seeding for onboarding content defaults
  - MVP-valid Phase 08 roadmap goal wording for verification
affects: [smart-onboarding, brand-kits, app-demo, phase-verification]
tech-stack:
  added: []
  patterns: [shared draft defaults in store upsert, confirm-to-brand-kit voice settings seeding]
key-files:
  created: []
  modified:
    - backend/app/website_crawl.py
    - backend/app/store.py
    - backend/tests/test_website_crawl.py
    - src/main.jsx
    - src/styles.css
    - .planning/ROADMAP.md
key-decisions:
  - "Kept voiceover and avatar in the existing onboarding/profile flow instead of adding a separate client or confirm subsystem."
  - "Mapped confirmed voiceover and avatar defaults into the existing brand-kit voice JSON seam so downstream consumers can read them without a schema split."
patterns-established:
  - "Onboarding fallback defaults that must survive crawl failure belong in shared store upsert logic, not only in extraction or UI defaults."
  - "Website onboarding option labels should reuse the existing brand-content settings vocabulary."
requirements-completed: [ONBOARD-03]
duration: 9min
completed: 2026-06-25
---

# Phase 8 Plan 03: Website Crawl Smart Onboarding Summary

**End-to-end onboarding content defaults now cover tonality, language, timezone, voiceover, and avatar, with confirm seeding the existing brand-kit voice settings and the roadmap goal rewritten into MVP user-story form**

## Performance

- **Duration:** 9 min
- **Started:** 2026-06-25T16:30:00Z
- **Completed:** 2026-06-25T16:39:06Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Extended the crawl/profile schema, draft storage, serialization, and confirm flow to carry `voiceover` and `avatar` through the full onboarding lifecycle.
- Extended the existing `OnboardingCard` with editable voiceover and avatar selects using the existing content-setting labels and defaults.
- Rewrote the Phase 08 roadmap goal into `As a / I want / so that` form and reran the focused backend and frontend checks.

## Task Commits

1. **Task 1: Extend onboarding backend schema with voiceover and avatar** - `888db1c` (`feat`)
2. **Task 2: Extend OnboardingCard with editable voiceover and avatar fields** - `b8b214e` (`feat`)
3. **Task 3: Fix MVP roadmap wording and rerun focused checks** - `f81589d` (`docs`)

## Files Created/Modified

- `backend/app/website_crawl.py` - adds `voiceover` and `avatar` to the MiniMax extraction contract and backend defaults.
- `backend/app/store.py` - persists the new onboarding fields, exposes them in profile serialization, and seeds them into `brand_kits.voice_json` on confirm.
- `backend/tests/test_website_crawl.py` - covers the full ONBOARD-03 contract, including crawl-failure defaults and confirm-to-brand-kit mapping.
- `src/main.jsx` - adds editable onboarding voiceover and avatar fields plus default selections using the existing option copy.
- `src/styles.css` - adds scoped onboarding helper-text styling only.
- `.planning/ROADMAP.md` - rewrites the Phase 08 goal into user-story form for MVP verification.

## Decisions Made

- Reused the existing onboarding field registry and confirm path instead of adding special-case handlers for the two missing defaults.
- Stored confirmed voiceover and avatar values inside the existing brand-kit voice payload so later consumers stay on one brand-kit seam.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Applied onboarding defaults in shared draft persistence**
- **Found during:** Task 1 (Extend onboarding backend schema with voiceover and avatar)
- **Issue:** Crawl-failure drafts only carried `crawlUrl`, so `voiceover` and `avatar` stayed blank even after the extraction/schema patch.
- **Fix:** Applied the new onboarding defaults in `upsert_merchant_profile`, the shared draft persistence path used by both successful and partial crawls.
- **Files modified:** `backend/app/store.py`, `backend/tests/test_website_crawl.py`
- **Verification:** `python3 -m unittest backend.tests.test_website_crawl -v`
- **Committed in:** `888db1c`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Required for correctness. The fix stayed inside the planned onboarding persistence path and did not add scope.

## Issues Encountered

- `src/styles.css` already had unrelated local drift. Resolved by staging only the onboarding helper-text hunk for the UI task commit.

## Verification

- `python3 -m unittest backend.tests.test_website_crawl -v` - PASS
- `npm run build` - PASS
- `rg -n "^\\*\\*Goal\\*\\*: As a merchant, I want to enter my website URL" .planning/ROADMAP.md` - PASS

## User Setup Required

None - no external service configuration required for this gap-closure slice.

## Next Phase Readiness

- ONBOARD-03 is now satisfied end to end for onboarding defaults before confirm.
- Confirmed onboarding profiles now map `voiceover` and `avatar` into `brand_kits.voice_json` alongside tone, audience, language, and description for downstream reads.
- Residual risk: `npm run build` still reports the pre-existing Vite chunk-size warning for the main app bundle; the build passes and this plan did not change bundling strategy.

## Self-Check: PASSED

- Verified `.planning/phases/08-website-crawl-smart-onboarding/08-03-SUMMARY.md` exists on disk.
- Verified task commits `888db1c`, `b8b214e`, and `f81589d` exist in git history.

---
*Phase: 08-website-crawl-smart-onboarding*
*Completed: 2026-06-25*
