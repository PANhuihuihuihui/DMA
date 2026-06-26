---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T05: 15 contract tests pass; full 168-test suite green

Write backend/tests/test_generation_dispatch.py. (1) Adapter contract: get_adapter raises for unknown provider_key; adapters instantiate without API keys at import time. (2) Job lifecycle: POST /api/v1/generation/jobs dispatch:false returns 201 status=queued with credit reservation; GET job returns it. (3) Credit correctness: mock adapter success path settles credits; failure path releases credits; balance correct after each. Use ApiCase pattern from test_fake_publish_lifecycle.py. Mock adapter via monkeypatching get_adapter.

## Inputs

- `backend/tests/test_fake_publish_lifecycle.py — ApiCase setup pattern`
- `backend/app/store.py — get_credit_summary`
- `backend/app/generation_dispatch.py`

## Expected Output

- `backend/tests/test_generation_dispatch.py`

## Verification

cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -m pytest backend/tests/test_generation_dispatch.py -v 2>&1 | tail -20
