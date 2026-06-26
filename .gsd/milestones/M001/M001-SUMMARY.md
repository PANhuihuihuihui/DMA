---
id: M001
title: "Text-to-Video and UGC Avatar Generation"
status: complete
completed_at: 2026-06-26T05:35:53.505Z
key_decisions:
  - Use live browser-triggered FE→BE validation as required proof for cross-surface features.
  - Treat MiniMax carousel generation as a real image-provider integration, with 3:4 aspect ratio and async carousel materialization matching video handoff patterns.
  - Preserve creativeId metadata as the authoritative bridge from generation outputs into phase-3 workspace visibility and editor handoff.
key_files:
  - backend/app/generation_dispatch.py
  - backend/app/generation_providers/minimax_adapter.py
  - backend/app/store.py
  - backend/tests/test_generation_dispatch.py
  - backend/tests/test_minimax_adapter.py
  - backend/tests/test_phase3_workspace.py
  - src/main.jsx
  - .gsd/milestones/M001/M001-VALIDATION.md
lessons_learned:
  - Cross-surface milestone claims are weak without a real browser-triggered API round-trip; backend-only or UI-only evidence misses integration failures.
  - MiniMax response shapes and supported aspect ratios must be normalized explicitly; provider assumptions caused both submit-time and preview-time failures.
  - Auto-mode milestone close can be blocked by generated runtime files unless they are ignored or cleaned within the worktree.
---

# M001: Text-to-Video and UGC Avatar Generation

**Delivered AI Studio generation flows for Sora video, HeyGen avatar video, and MiniMax carousel images with approval-ready Creative Editor handoff and validated live frontend-backend browser proof.**

## What Happened

M001 established a real generation control plane across the React frontend and Python backend, including cataloged models, credit metering, async job dispatch, output materialization, and phase-3 workspace handoff into review/edit flows. The final pass closed the browser UAT gap by verifying that live UI actions trigger backend API requests and produce visible outputs, then fixed MiniMax carousel generation end to end by aligning the supported aspect ratio, materializing async carousel jobs, handling MiniMax response variants, and confirming Creative Editor handoff from the browser-triggered run.

## Success Criteria Results

- SC-01 PASS: AI Studio renders the catalog with HeyGen UGC Avatar, GPT Image 2, MiniMax Carousel Image, and Sora 2 visible in the live browser flow.
- SC-02 PASS: Browser-triggered generation requests return 201 and create trackable jobs in backend/API state.
- SC-03 PASS: Succeeded video jobs surface in generated outputs with Creative Editor handoff.
- SC-04 PASS: Backend materializes generation outputs into phase-3 creatives/media assets with creativeId linkage preserved.
- SC-05 PASS: MiniMax carousel flow now runs with supported 3:4 settings, succeeds through the live FE→BE path, and surfaces a valid Creative Editor handoff.
- SC-06 PASS: Milestone validation persisted a final PASS verdict in `.gsd/milestones/M001/M001-VALIDATION.md`.

## Definition of Done Results

- Code changes are committed and the milestone worktree is clean.
- Focused backend verification passed via `python3 -m unittest backend.tests.test_generation_dispatch backend.tests.test_phase3_workspace backend.tests.test_minimax_adapter`.
- Production build passed via `npm run build`.
- Live browser verification passed against a running frontend and backend with dev login enabled, including job submission and observable UI results.
- Validation artifacts and UAT evidence were recorded before milestone close.

## Requirement Outcomes

- Frontend/backend integrated generation and approval flows were validated with live browser-triggered API round-trips, reinforcing the new integration requirement added during this milestone.
- Existing M001 slice requirements for generation catalog, async dispatch, output materialization, and workspace handoff were advanced to delivered behavior with browser and backend evidence.
- No requirement was invalidated during close; remaining production-provider credential setup is operational follow-up rather than a blocker to milestone completion.

## Deviations

Milestone close was briefly blocked by untracked GSD runtime files in the worktree; this was resolved by adding ignore rules and committing the cleanup before reattempting completion.

## Follow-ups

Optional follow-up work includes production credential setup and real-provider smoke coverage beyond dev-mode validation, but these are not blockers for M001 closure.
