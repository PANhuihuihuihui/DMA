---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T03: R005 verified: 16 new tests prove classify_error_class maps all 7 error classes correctly and routing taxonomy covers retryable vs manual_fallback

Run automated checks against classify_error_class() and routing logic in facebook_publisher.py to prove: (1) all 7 error classes recognized, (2) retryable classes route to retry, (3) non-retryable route to manual_fallback_required. AiToEarn reference: their FacebookPlatformException maps to 6 categories; our 7-class taxonomy is more granular.

## Inputs

- `backend/app/facebook_publisher.py`

## Expected Output

- `backend/tests/test_error_classification.py`

## Verification

python -m pytest backend/tests/test_error_classification.py -v exits 0
