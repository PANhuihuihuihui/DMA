---
id: T04
parent: S02
milestone: M002
key_files:
  - backend/app/store.py
  - backend/app/server.py
  - backend/tests/test_evidence_export.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T16:32:28.286Z
blocker_discovered: false
---

# T04: R006 verified: 4 existing tests prove build_publish_job_evidence returns redacted bundle with required fields, admin endpoint works, and non-operator access rejected

**R006 verified: 4 existing tests prove build_publish_job_evidence returns redacted bundle with required fields, admin endpoint works, and non-operator access rejected**

## What Happened

Ran existing test_evidence_export.py (4 tests across EvidenceExportStoreTest and EvidenceExportApiTest). Tests cover: build_publish_job_evidence returns bundle with job, appReview, exportedAt, route, deliveryMode, directPost eligibility, tiktokConfirmations — all redacted (assert_no_forbidden_terms). Missing job returns 404. Admin HTTP endpoint returns redacted bundle. Non-operator session gets 403 — role-based access control works. AiToEarn reference: no equivalent evidence export feature — this is our differentiator for Meta app review compliance.

## Verification

python3 -m pytest backend/tests/test_evidence_export.py -v — 4 passed

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_evidence_export.py -v` | 0 | pass | 400ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/app/store.py`
- `backend/app/server.py`
- `backend/tests/test_evidence_export.py`
