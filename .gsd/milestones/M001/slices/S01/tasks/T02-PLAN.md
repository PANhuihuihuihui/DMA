---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T02: Created generation_providers package with OpenAI Sora 2 video adapter and adapter registry

Create backend/app/generation_providers/__init__.py and backend/app/generation_providers/openai_adapter.py implementing the OpenAI Sora 2 text-to-video adapter. Shared contract: submit(job_record, settings) -> attempt_id, poll(attempt_id) -> {status, output_url?, error?}, cancel(attempt_id). submit calls POST /v1/video/generations via direct HTTP with OPENAI_API_KEY from env. poll calls GET /v1/video/generations/{id}. Normalized ProviderError on failure. get_adapter(provider_key) factory in __init__.py.

## Inputs

- `backend/app/store.py seed — provider_key 'openai_video'`
- `OpenAI video generations API: POST /v1/video/generations, GET /v1/video/generations/{id}`

## Expected Output

- `backend/app/generation_providers/__init__.py`
- `backend/app/generation_providers/openai_adapter.py`

## Verification

cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -c 'from backend.app.generation_providers import get_adapter; a = get_adapter("openai_video"); print(type(a).__name__)'
