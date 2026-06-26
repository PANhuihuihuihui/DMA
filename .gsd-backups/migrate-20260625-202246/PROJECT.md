# Project

## What This Is

LocalPilot AI is an AI marketing operator for local small businesses that turns one promotion, service, product, or content idea into platform-native social posts. Business owners connect their official accounts, generate Facebook and TikTok posts, review the output, and publish from one workflow. The product's wedge is local-business growth: strategy-aware content, platform-specific copy, owner approval, and eventually a feedback loop from posts to calls, bookings, DMs, coupons, and walk-ins.

**Current state:** Backend publishing infrastructure is built (Phases 1–2, 5–6 done). Real Facebook OAuth publishing and token persistence are in progress (Phase 4). A generation platform with credit metering is complete (Phase 13). Website-crawl onboarding and Google login are complete (Phases 7–8). Remaining: Predis-style demo surface hardening (Phase 3), carousel generation (Phase 11), and text-to-video / UGC avatar (Phase 12).

## Core Value

A local business owner can go from one marketing idea to approved, platform-native Facebook and TikTok posts published through their own official accounts with minimal effort.

## Project Shape

- **Complexity:** complex
- **Why:** Multi-platform OAuth, async generation jobs, credit metering, approval workflows, and UI parity with commercial products (Predis). Requires backend/frontend co-design and real platform API integration.
- **Web stack:** React/Vite frontend + Python FastAPI-style backend (manual JSON handler routing, SQLite), served via Vite proxy on port 8787. Phase 13 added a generation control plane with async job lifecycle and credit ledger.

## Current State

**Backend:** FastAPI-lite Python server with manual route matching, SQLite persistence, Facebook OAuth + publisher, TikTok publisher, sessions/auth (Google OAuth done), website-crawl onboarding, generation catalog + job dispatch + credit ledger, and Phase 3 Predis-style workspace records.

**Frontend:** React/Vite app with landing page, `/app` demo workspace, 9 Phase 3 screens (Dashboard, Brand Kit, AI Generator, Creative Editor, Content Calendar, Approval Queue, Connected Accounts, Competitor Ideas, Proof Loop), and Phase 13 AI Studio generation workspace.

**Completed:** Phases 1, 2, 5, 6, 7, 8, 13 (fully verified).

**In progress:** Phase 3 (1/2 plans done; 03-02 Predis reference hardening pending), Phase 4 (3/8 plans done; 5 plans remaining).

**Not started:** Phase 11 (Carousel Generation), Phase 12 (Text-to-Video / UGC Avatar).

## Architecture / Key Patterns

- Backend owns all state: sessions, tokens, publish jobs, generation jobs, credit ledger, brand kits. Frontend is a thin client.
- Token boundary: OAuth tokens stored server-side only, never in browser localStorage. `token_boundary.py` provides redacted refs to frontend.
- Publishing: generic async job lifecycle (`publish_jobs` / `publish_attempts` / `publish_events`), normalized by `PublishingProvider` contract. Facebook and TikTok are adapters under this contract.
- Generation: `generation_catalog` → `generation_jobs` → `generation_attempts` → `generation_outputs`, metered through `credit_accounts` / `credit_ledger`. Provider adapters (`OpenAIImageAdapter`, `CCDanceAdapter`) plug under a `GenerationProviderAdapter` contract.
- Approval: immutable snapshots freeze the exact approved payload. Retries re-use the frozen snapshot.
- Error taxonomy: both publishers classify failures into authentication, permission, validation, rate limit, transient, unknown — driving retry vs. fallback vs. manual routing.
- Phase 3 workspace: `GET /api/v1/phase3/workspace` is the canonical backend surface; frontend is `src/main.jsx` module views.
- `src/api/publishingClient.js` is the frontend API client boundary.
- All diagnostics pass through `redact` / `safe_diagnostics` before reaching the client.

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: Phase 3 — Predis-style Demo Surface Hardening — replicate logged-in Predis.ai workflow with LocalPilot's local proof loop and owner-approval wedge
- [ ] M002: Phase 4 — Facebook Page Publishing Hardening — encrypted token persistence, merchant-driven Page selection, media validation, retry/fallback, app review evidence
- [ ] M003: Phase 11 — Carousel Generation — merchant generates branded 5-slide carousels from idea/URL using real image generation and credit metering
- [ ] M004: Phase 12 — Text-to-Video + UGC Avatar — merchant generates short videos and UGC avatar videos with voiceover through video-model providers

*Completed phases (reference only): M001-ref → Phase 1 (backend publishing foundation), M002-ref → Phase 2 (engine reuse decision), M003-ref → Phase 5 (TikTok gates), M004-ref → Phase 6 (manual fallback), M005-ref → Phase 7 (Google login), M006-ref → Phase 8 (website-crawl onboarding), M007-ref → Phase 13 (generation platform + credits)*
