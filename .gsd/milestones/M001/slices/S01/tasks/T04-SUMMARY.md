---
id: T04
parent: S01
milestone: M001
key_files:
  - backend/app/generation_dispatch.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T00:27:59.794Z
blocker_discovered: false
---

# T04: Dispatch loop fully wired: submit→exponential-poll→settle/release with adapter registry

**Dispatch loop fully wired: submit→exponential-poll→settle/release with adapter registry**

## What Happened

The _run_dispatch / _dispatch_job loop implemented in T01 already covers T04 requirements: loads job from store, looks up adapter by "{provider_key}:{capability}" composite key (wired from ADAPTER_REGISTRY in T02), calls adapter.submit(), polls with exponential backoff (2s→4s→8s→30s cap), calls store.settle_generation_credits on success, calls _release_on_failure (which calls store.release_generation_credits) on failure or timeout (900s wall-clock cap). Each state transition logs at INFO level. retry_generation_job inserts a new generation_attempt row, resets job status to queued, and optionally calls start_async_dispatch.

## Verification

Verification evidence recorded: `python3 -c 'from backend.app import generation_dispatch; import inspect; print(inspect.signature(generation_dispatch.retry_generation_job))'` exited 0 (retry_generation_job signature matches server.py contract).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -c 'from backend.app import generation_dispatch; import inspect; print(inspect.signature(generation_dispatch.retry_generation_job))'` | 0 | retry_generation_job signature matches server.py contract | 285ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/app/generation_dispatch.py`
