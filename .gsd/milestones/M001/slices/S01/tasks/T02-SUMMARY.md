---
id: T02
parent: S01
milestone: M001
key_files:
  - backend/app/generation_providers/__init__.py
  - backend/app/generation_providers/openai_adapter.py
  - backend/app/generation_dispatch.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T06:03:23.027Z
blocker_discovered: false
---

# T02: Created generation_providers package with OpenAI Sora 2 video adapter and adapter registry

**Created generation_providers package with OpenAI Sora 2 video adapter and adapter registry**

## What Happened

Created backend/app/generation_providers/__init__.py with ADAPTER_REGISTRY dict keyed by "{provider_key}:{capability}" composite keys and a get_adapter() factory. Created backend/app/generation_providers/openai_adapter.py implementing OpenAIVideoAdapter with submit() calling POST /v1/video/generations and poll() calling GET /v1/video/generations/{id}. The adapter normalizes provider statuses (queued/in_progress/processing → running, completed → succeeded, anything else → failed) into the dispatch engine's standard shape. OPENAI_API_KEY is read from env at call time; missing key raises EnvironmentError before any network call. Also noted the provider_key for Sora 2 in the catalog is "openai" (not "openai_video"), so the registry key is "openai:video" — updated generation_dispatch.py to use composite "{provider_key}:{capability}" key and wired the ADAPTER_REGISTRY import.

## Verification

Verification evidence recorded: `python3 -c 'from backend.app.generation_providers import get_adapter; a = get_adapter("openai:video"); print(type(a).__name__)'` exited 0 (OpenAIVideoAdapter instantiated correctly).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -c 'from backend.app.generation_providers import get_adapter; a = get_adapter("openai:video"); print(type(a).__name__)'` | 0 | OpenAIVideoAdapter instantiated correctly | 310ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/app/generation_providers/__init__.py`
- `backend/app/generation_providers/openai_adapter.py`
- `backend/app/generation_dispatch.py`
