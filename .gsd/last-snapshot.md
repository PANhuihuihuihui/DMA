# GSD context snapshot (2026-06-26T00:38:13.741Z)

## Top project memories
- [MEM001] (architecture) Which provider to use for UGC avatar video generation (replacing the CCDance stub) Chose: HeyGen API v2 — replace CCDance stub with HeyGen; update catalog seed provider_key from "ccdance_stub" to "heygen" and readiness_status from "preview" to "ready". Rationale: CCDance has no real implementation path. HeyGen v2 supports avatar selection by ID, script-based async video generation, and native voiceover in one call — mapping cleanly onto the existing adapter i….
- [MEM002] (architecture) Which provider to use for text-to-video generation Chose: Sora 2 via OpenAI Responses API (POST /v1/video/generations) — existing catalog entry genmodel_openai_video_primary with readiness_status "ready" is promoted to production adapter. Rationale: Catalog seed already exists with correct model ID and 180-credit cost. OpenAIVideoAdapter stub exists in the codebase. If the endpoint is inaccessible at S01 implementation time, fallback to RunwayML….

## Recent gsd_exec runs
- [e938a7e2-d86e-45f1-b25c-bd1d1993bfbe] bash exit:0 — list frontend source directories
- [45cc400e-55b9-4f9a-ae9f-7adbd66aec38] bash exit:0 — find video/UGC generation surfaces in frontend
- [ebfb8150-bd74-4cd9-85ea-382360b1c35f] bash exit:0 — find generation store functions
- [4f171f83-d826-4982-b058-cfab17176ace] bash exit:0 — find all generation_dispatch references in server.py
- [19cc54ca-da44-410c-b0fc-d37b752a4bc6] bash exit:0 — check what's in main vs this worktree
