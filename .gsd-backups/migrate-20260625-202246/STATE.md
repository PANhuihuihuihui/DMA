# GSD State

**Active Milestone:** M001: Text-to-Video and UGC Avatar Generation
**Active Slice:** S01: Dispatch Engine and Provider Adapters
**Phase:** evaluating-gates
**Requirements Status:** 0 active · 0 validated · 0 deferred · 0 out of scope

## Milestone Registry
- 🔄 **M001:** Text-to-Video and UGC Avatar Generation
- ⬜ **M002:** Phase 4
- ⬜ **M003:** Phase 11
- ⬜ **M004:** Phase 12

## Recent Decisions
- D001 (M001 planning; S01 adapter implementation is the enforcement point): Which provider to use for UGC avatar video generation (replacing the CCDance stub) -> HeyGen API v2 — replace CCDance stub with HeyGen; update catalog seed provider_key from "ccdance_stub" to "heygen" and readiness_status from "preview" to "ready"
- D002 (M001 planning; verified at start of S01 before adapter implementation): Which provider to use for text-to-video generation -> Sora 2 via OpenAI Responses API (POST /v1/video/generations) — existing catalog entry genmodel_openai_video_primary with readiness_status "ready" is promoted to production adapter

## Blockers
- None

## Next Action
Evaluate 2 quality gate(s) for S01 before execution.
