---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T04: Dispatch loop fully wired: submit→exponential-poll→settle/release with adapter registry

Implement the _run_dispatch worker in generation_dispatch.py. Load job from store, read model catalog for provider_key and credit_cost, call get_adapter(provider_key).submit(), poll at exponential backoff (2s→4s→8s→30s cap, max 60 attempts). On succeeded: settle_generation_credits + update job status. On failed/timeout: release_generation_credits + update job status to failed with normalized error. Log each state transition. retry_generation_job creates a new generation_attempt row and conditionally re-dispatches.

## Inputs

- `backend/app/store.py — settle_generation_credits, release_generation_credits, get_generation_job`
- `backend/app/generation_providers/__init__.py — get_adapter contract`
- `backend/app/server.py line 193 — retry_generation_job signature`

## Expected Output

- `backend/app/generation_dispatch.py`

## Verification

cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -c 'from backend.app import generation_dispatch; import inspect; print(inspect.signature(generation_dispatch.retry_generation_job))'
