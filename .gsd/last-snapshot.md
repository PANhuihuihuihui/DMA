# GSD context snapshot (2026-06-26T03:19:04.101Z)

## Top project memories
- [MEM003] (pattern) Frontend generation job polling uses exponential backoff (3s→30s cap) with dependency on genActiveJobs.length to reset on new job activation. This pattern efficiently tracks long-running async operations without hammering the API while remaining responsive to user actions.
- [MEM001] (architecture) Which provider to use for UGC avatar video generation (replacing the CCDance stub) Chose: HeyGen API v2 — replace CCDance stub with HeyGen; update catalog seed provider_key from "ccdance_stub" to "heygen" and readiness_status from "preview" to "ready". Rationale: CCDance has no real implementation path. HeyGen v2 supports avatar selection by ID, script-based async video generation, and native voiceover in one call — mapping cleanly onto the existing adapter i….
- [MEM002] (architecture) Which provider to use for text-to-video generation Chose: Sora 2 via OpenAI Responses API (POST /v1/video/generations) — existing catalog entry genmodel_openai_video_primary with readiness_status "ready" is promoted to production adapter. Rationale: Catalog seed already exists with correct model ID and 180-credit cost. OpenAIVideoAdapter stub exists in the codebase. If the endpoint is inaccessible at S01 implementation time, fallback to RunwayML….

## Recent gsd_exec runs
- [1496bd5d-7f78-473b-9976-6a52687d35c8] bash exit:0 — UAT M001/S02/verify-no-syntax-errors (uat-runtime-check)
- [1ce66f8b-630c-4087-af90-42294f27de04] bash exit:0 — UAT M001/S02/test-final-comprehensive (uat-artifact-check)
- [2e42c721-37aa-45ae-9659-d9cc441c7fa3] bash exit:1 — UAT M001/S02/test-6-error-handling (uat-artifact-check)
- [ddd62e57-27ba-47e1-804e-1109983b7086] bash exit:0 — UAT M001/S02/test-5-concurrent-jobs (uat-artifact-check)
- [5ed791f0-efdc-44bf-ba15-9deaae5d06d2] bash exit:0 — UAT M001/S02/test-4-job-status-ui (uat-artifact-check)
