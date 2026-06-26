---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T04: R006 verified: 4 existing tests prove build_publish_job_evidence returns redacted bundle with required fields, admin endpoint works, and non-operator access rejected

Run automated checks against build_publish_job_evidence() in store.py and admin endpoint in server.py to prove: (1) evidence includes required fields (scopes, publish route, gate results, timestamps), (2) secrets redacted, (3) endpoint returns valid JSON. AiToEarn reference: no equivalent — our differentiator for Meta app review compliance.

## Inputs

- `backend/app/store.py`
- `backend/app/server.py`

## Expected Output

- `backend/tests/test_evidence_bundle.py`

## Verification

python -m pytest backend/tests/test_evidence_bundle.py -v exits 0
