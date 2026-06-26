---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T03: Created HeyGen avatar adapter and updated catalog seed from ccdance_stub to heygen:ready

Create backend/app/generation_providers/heygen_adapter.py implementing HeyGen v2 UGC avatar adapter. submit calls POST /v2/video/generate with avatar_id, script, voiceover from HEYGEN_API_KEY env. poll calls GET /v1/video_status.get?video_id={id}. Update store.py seed_generation_model_catalog: replace provider_key 'ccdance_stub' with 'heygen' and readiness_status 'preview' with 'ready' for the avatar model entry.

## Inputs

- `backend/app/store.py — seed_generation_model_catalog CCDANCE_AVATAR_MODEL_ID entry`
- `HeyGen API v2: POST /v2/video/generate, GET /v1/video_status.get`

## Expected Output

- `backend/app/generation_providers/heygen_adapter.py`
- `backend/app/store.py`

## Verification

cd /Users/huijie/DMA/.gsd-worktrees/M001 && python -c 'from backend.app.generation_providers import get_adapter; a = get_adapter("heygen"); print(type(a).__name__)'
