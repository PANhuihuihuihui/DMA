---
phase: 08-website-crawl-smart-onboarding
plan: 01
subsystem: api
tags: [onboarding, minimax, sqlite, urllib, unittest]
requires:
  - phase: 07-google-login-and-auth
    provides: authenticated merchant session resolution for backend routes
provides:
  - homepage crawl and HTML cleaning pipeline for onboarding
  - draft merchant profile storage and confirmation flow
  - authenticated onboarding crawl/profile REST endpoints
  - mocked backend coverage for fetch, extraction, and onboarding routes
affects: [smart-onboarding, brand-kits, backend-api]
tech-stack:
  added: []
  patterns: [stdlib urllib HTTP integration, draft-to-confirmed onboarding persistence]
key-files:
  created:
    - backend/app/website_crawl.py
    - backend/tests/test_website_crawl.py
  modified:
    - backend/app/store.py
    - backend/app/server.py
key-decisions:
  - "Used stdlib urllib for both homepage fetch and MiniMax chat completions to satisfy the no-new-dependencies constraint."
  - "Kept onboarding routes fully authenticated by adding a session-required merchant resolver instead of reusing the demo fallback path."
patterns-established:
  - "Merchant onboarding state lives in merchant_profiles as a draft until explicit confirm."
  - "Crawl and LLM failures degrade to saved blank/partial profiles instead of blocking the onboarding route."
requirements-completed: [ONBOARD-01, ONBOARD-02, ONBOARD-03, ONBOARD-05]
duration: 6min
completed: 2026-06-25
---

# Phase 8 Plan 01: Website Crawl Smart Onboarding Summary

**Single-page website crawl onboarding with MiniMax-backed brand extraction, draft merchant profiles, and authenticated confirm-to-brand-kit flow**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-25T16:04:28Z
- **Completed:** 2026-06-25T16:10:28Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- Added `merchant_profiles` persistence with draft, patch, and confirm helpers plus a confirmed demo seed.
- Added `website_crawl.py` for guarded public URL fetch, HTML reduction, MiniMax extraction, and output sanitization.
- Added authenticated onboarding crawl/profile endpoints and backend tests covering happy path, failure path, recrawl, confirm, and sanitization.

## Task Commits

1. **Task 1: Create merchant_profiles table and store helpers** - `ae8adef` (`feat`)
2. **Task 2: Create website_crawl module — fetch, clean HTML, LLM extraction** - `9eb07f0` (`feat`)
3. **Task 3: Add onboarding API routes to server.py** - `fd4df6d` (`feat`)
4. **Task 4: Add unit tests with mock HTTP and mock LLM** - `b95f1de` (`test`)

## Files Created/Modified

- `backend/app/store.py` - adds `merchant_profiles`, draft/confirm helpers, and the Phase 8 demo profile seed.
- `backend/app/website_crawl.py` - implements guarded homepage fetch, HTML cleanup, MiniMax extraction, and field sanitization.
- `backend/app/server.py` - adds authenticated onboarding crawl/profile/confirm routes.
- `backend/tests/test_website_crawl.py` - covers fetch, clean, extract, sanitization, and onboarding route flows with mocks.

## Decisions Made

- Used the existing backend/store/session seams and kept the crawl to a single merchant-supplied homepage only.
- Stored raw extraction JSON in the table for backend debugging while excluding it from API serialization.
- Confirm updates the merchant brand kit in place when one exists and creates one when missing.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

- `python3 -c "from backend.app import store; print('merchant_profiles store helpers imported OK')"` - PASS
- Task 1 acceptance script against temp SQLite DB - PASS
- `python3 -c "from backend.app.website_crawl import fetch_homepage, clean_html_for_llm, extract_brand_profile; print('website_crawl module imported OK')"` - PASS
- Task 2 mocked fetch/extract acceptance script - PASS
- `python3 -c "from backend.app.server import JsonHandler; print('server routes OK')"` - PASS
- Task 3 authenticated temp-server route flow script - PASS
- `python3 -m unittest backend.tests.test_website_crawl -v` - PASS
- `python3 -m unittest discover backend/tests` - PASS
- Manual curl verification was not run separately; the same route flow was exercised with a temp HTTP server in automated tests.

## Known Stubs

- `backend/app/store.py:2206` - pre-existing demo provider summary still uses `upload_to_inbox_placeholder`; unrelated to this onboarding backend slice.

## User Setup Required

- Set `MINIMAX_API_KEY` in the backend runtime for live extraction. Tests use mocked LLM responses and do not require the key.

## Next Phase Readiness

- Backend onboarding contracts are ready for the frontend onboarding card in `08-02`.
- Confirmed profiles now seed `brand_kits`, so later generation flows can read onboarding output without changing this backend slice.

## Self-Check: PASSED

- Verified `backend/app/website_crawl.py`, `backend/tests/test_website_crawl.py`, and `.planning/phases/08-website-crawl-smart-onboarding/08-01-SUMMARY.md` exist on disk.
- Verified task commits `ae8adef`, `9eb07f0`, `fd4df6d`, and `b95f1de` exist in git history.

---
*Phase: 08-website-crawl-smart-onboarding*
*Completed: 2026-06-25*
