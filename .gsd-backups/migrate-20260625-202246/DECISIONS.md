# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? | Made By |
|---|------|-------|----------|--------|-----------|------------|---------|
| D001 | M001 planning; S01 adapter implementation is the enforcement point | provider | Which provider to use for UGC avatar video generation (replacing the CCDance stub) | HeyGen API v2 — replace CCDance stub with HeyGen; update catalog seed provider_key from "ccdance_stub" to "heygen" and readiness_status from "preview" to "ready" | CCDance has no real implementation path. HeyGen v2 supports avatar selection by ID, script-based async video generation, and native voiceover in one call — mapping cleanly onto the existing adapter interface. Volcengine/dashscope require Chinese cloud accounts; Synthesia is enterprise-only. HeyGen is the most accessible provider with a compatible async job pattern. | yes — if HeyGen access is unavailable, fallback to volcengine dashscope or D-ID before S01 completes | agent |
| D002 | M001 planning; verified at start of S01 before adapter implementation | provider | Which provider to use for text-to-video generation | Sora 2 via OpenAI Responses API (POST /v1/video/generations) — existing catalog entry genmodel_openai_video_primary with readiness_status "ready" is promoted to production adapter | Catalog seed already exists with correct model ID and 180-credit cost. OpenAIVideoAdapter stub exists in the codebase. If the endpoint is inaccessible at S01 implementation time, fallback to RunwayML, Kling, or Luma Labs — the adapter contract is provider-agnostic so swapping is a one-file change. | yes — fallback to RunwayML/Kling/Luma Labs if Sora 2 endpoint is not generally available | agent |
