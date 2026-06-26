# M001: Text-to-Video And UGC Avatar Generation

**Gathered:** 2026-06-25
**Status:** Ready for planning
**Origin:** Migrated from `.planning/phases/12-text-to-video-and-ugc-avatar/` (not previously context-gathered). Continues the .planning/ phase sequence as Phase 12.

## Project Description

Merchant can generate short text-to-video clips and UGC avatar videos through provider-backed video models, with voiceover, gated by the existing Phase 13 credit ledger. Output lands in the existing Creative Editor and follows the standard owner-approval flow before publishing.

## Why This Milestone

Phases 7, 8, 11, 13 delivered Google login, smart onboarding, carousel generation, and the AiToEarn-inspired credits + multi-provider generation platform. Phase 11 closed the image/carousel content type. Phase 12 closes the **video** content type — the remaining v2.0 generative-engine gap (`GENV-01`, `GENV-02`) — by promoting the Phase 13 `CCDanceAdapter` / `OpenAIVideoAdapter` stubs into production adapters and adding a UGC-avatar selection + voiceover path.

## User-Visible Outcome

### When this milestone is complete, the merchant can:

- Enter a text prompt and generate a short branded video (script + scenes + captions + voiceover) that opens in the Creative Editor.
- Select an avatar (by attributes), provide a script, and generate a UGC avatar video with voiceover.
- See per-model credit cost before launching, watch async job status, and have credits reserved/settled correctly through the existing ledger.
- Approve the generated video through the standard owner-approval flow before any downstream publishing.

### Entry point / environment

- Entry point: `/app` AI Studio → Create New → Short Ad Video / UGC, then Creative Editor handoff.
- Environment: browser + backend; runs against real video provider APIs in production.
- Live dependencies: video model provider (TBD during planning — Sora 2 via `OpenAIVideoAdapter`, CCDance-style provider, or alternative), MiniMax or chosen voiceover provider, existing credit ledger.

## Completion Class

- Contract complete: provider adapter contract, async job lifecycle, credit reserve/settle/release covered by tests.
- Integration complete: real video provider returns a real artifact through the normal generation job path; output opens in the Creative Editor as one editable package.
- Operational complete: failed jobs surface normalized errors; credits are released on failure; retry path is safe and idempotent.

## Final Integrated Acceptance

- One real text-to-video generation runs end-to-end against the live provider with real credit subtraction, lands in the Creative Editor, and is approvable.
- One real UGC avatar video generation runs end-to-end against the live provider with voiceover, lands in the Creative Editor, and is approvable.
- A pre-release manual smoke (mirroring Phase 11's Nike/MiniMax/real-ledger gate) is captured.

## Architectural Decisions

> Decisions will be added during the discuss phase. Phase 13 patterns are binding (backend-owned credits, provider-agnostic adapter contract, async job lifecycle, server-side secrets only).

### Inherited from Phase 13
- Backend is source of truth for credentials, routing, ledger, job state, output refs, retries.
- All generation is async; no long blocking requests.
- Frontend renders normalized records, not provider-native payloads.

### Inherited from Phase 11
- Output handoff is into the existing Creative Editor as one editable package.
- Owner approval remains in the flow; no auto-publish.
- Pre-release real-provider + real-ledger smoke is mandatory.

## Error Handling Strategy

Reuse Phase 13's normalized job lifecycle (queued/running/succeeded/failed) and credit reserve/settle/release. Provider-specific errors map to the existing taxonomy. Voiceover provider failure should fail the parent video job cleanly with credit release. To be detailed during planning.

## Risks and Unknowns

- **Video provider selection** — Sora 2 (real adapter from `OpenAIVideoAdapter` stub), CCDance-style provider (Phase 13 stub), or alternative; choice affects cost, latency, and UGC-avatar feasibility. Resolved in discuss phase.
- **Avatar selection model** — attribute-based picker vs. uploaded reference; UGC avatar provider availability is the gating fact.
- **Voiceover pipeline** — separate TTS provider or bundled with video model; affects job composition.
- **Latency** — video jobs are minutes-long; status polling cadence and UI affordance need design.
- **Credit cost calibration** — video is the most expensive content type so far; per-model cost catalog needs real numbers before launch.

## Existing Codebase / Prior Art

- `backend/app/generation_dispatch.py` — Phase 13 async job lifecycle; Phase 12 extends, does not replace.
- `backend/app/generation_catalog.py` — provider/model catalog; add video + UGC-avatar models with real `credit_cost`.
- `backend/app/generation_providers/openai_adapter.py` — `OpenAIVideoAdapter` (Sora 2 submit/poll stub) to promote.
- `backend/app/generation_providers/ccdance_adapter.py` — CCDance stub to promote (or replace with chosen provider).
- `backend/app/store.py` — `generation_jobs`, `generation_attempts`, `generation_outputs`, `credit_ledger`, `creative_media_assets`.
- `src/api/generationClient.js` — extend for video job submit/poll.
- `src/main.jsx` — AI Studio Create New chooser already has "Short Ad Video" and "UGC" cards (Phase 3.2 work); wire them to real generation.
- `.planning/phases/11-carousel-generation/` — pattern blueprint for "extend Phase 13 with a new content type".
- `.planning/phases/13-aitoearn-inspired-credits-and-multi-provider-generation-plat/` — full prior context on the generation platform.
- AiToEarn reference: `/tmp/AiToEarn/project/aitoearn-backend/apps/aitoearn-ai/src/core/ai/video/` (grok/volcengine/dashscope video services + task-status scheduler) and `draft-generation` v2 video pipeline for submit-poll-callback patterns and voiceover handling.

## Relevant Requirements

- `GENV-01` — Merchant can generate a short video from a text prompt (script, scenes, captions, voiceover).
- `GENV-02` — Merchant can generate a UGC avatar video by selecting an avatar and providing a script, producing a video with voiceover.

## Scope

### In Scope

- Text-to-video generation through one real provider.
- UGC avatar video generation through one real provider with voiceover.
- Per-model credit cost surfacing + ledger gating + release-on-failure.
- Creative Editor handoff as one editable package per video output.
- Owner-approval flow continuity.
- Pre-release manual smoke against real provider + real ledger.

### Out of Scope / Non-Goals

- Long-form video, multi-clip editing, timeline scrubbing.
- Live avatar customization (custom avatar training from user uploads).
- Multiple video providers in this milestone (catalog supports it, but one is enough to ship GENV-01/02).
- Publishing path changes (existing Facebook/TikTok publish flows consume the output unchanged).

## Technical Constraints

- Provider secrets server-side only.
- Async lifecycle reuses Phase 13 contract; no long blocking requests.
- Credits metered via existing `credit_ledger`; no bypass path.
- Output stored as `creative_media_assets` linked to a `generated_creative` (Phase 11 pattern).

## Integration Points

- Phase 13 generation platform (job lifecycle, catalog, ledger).
- Phase 11 Creative Editor packaging pattern.
- Phase 3 owner-approval flow.
- AI Studio Create New chooser (Phase 3.2 UI surface already exists).

## Testing Requirements

- Backend: provider adapter contract tests, async lifecycle state transitions, credit reserve/settle/release on success and failure, ledger correctness.
- Frontend: AI Studio → Create New → Short Ad Video / UGC → job submit → status poll → Creative Editor handoff → approval.
- Manual smoke: real provider + real ledger end-to-end pre-release, capturing video artifact + credit delta + diagnostics.

## Acceptance Criteria

> Per-slice criteria to be finalized during planning. Anchors:
> 1. Text-to-video generates a real video from a text prompt and opens in Creative Editor.
> 2. UGC avatar video generates with voiceover and opens in Creative Editor.
> 3. Credit cost is visible before launch; insufficient balance blocks launch; failed jobs release reservations.
> 4. Generated video is approvable through the existing owner-approval flow.
> 5. Pre-release smoke against real provider + real ledger is captured.

## Open Questions

- Which video provider for text-to-video (Sora 2 / CCDance / volcengine / dashscope / other)?
- Which provider for UGC avatar — same as text-to-video, or separate?
- Voiceover: bundled with video model, or separate TTS step (e.g. MiniMax)?
- Status-poll cadence and UI for minutes-long jobs?
- Real credit cost per model for the catalog?

## Migration Note

This milestone is the first written natively into `.gsd/`. Phases 1–11 and 13 from `.planning/phases/` are preserved as historical reference and treated as validated; their requirements are recorded in `.gsd/REQUIREMENTS.md` with status reflecting actual completion. `.planning/` remains untouched for full audit history.
