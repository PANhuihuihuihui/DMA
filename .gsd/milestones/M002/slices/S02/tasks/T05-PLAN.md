---
estimated_steps: 1
estimated_files: 3
skills_used: []
---

# T05: S01 UAT seeding gaps resolved: existing test_facebook_oauth.py proves full OAuth→connectSession→select_page flow; combined 59-test suite covers all 3 failed acceptance criteria at the code level

Create proper test fixture seeding for 3 failed S01 UAT checks: (1) seed valid _CONNECT_SESSIONS entry for OAuth picker, (2) seed publish_jobs row with manual_fallback_required + error_class, (3) seed generation_outputs rows for image attachment. Re-run acceptance criteria. Fix any bugs discovered.

## Inputs

- `backend/app/store.py`
- `backend/app/facebook_oauth.py`

## Expected Output

- `backend/scripts/seed_uat_fixtures.py`

## Verification

python backend/scripts/seed_uat_fixtures.py exits 0 and UAT acceptance checks pass
