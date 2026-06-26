# M001: Text-to-Video and UGC Avatar Generation

**Vision:** Merchant can generate short branded videos (text-to-video via Sora 2) and UGC avatar videos (via HeyGen) through the AI Studio, with credit gating, async job status, Creative Editor handoff, and owner-approval continuity — closing the video content-type gap in the generation platform.

## Success Criteria

- One real text-to-video generation runs end-to-end against Sora 2 with real credit subtraction and lands in the Creative Editor.
- One real UGC avatar video generates via HeyGen with voiceover, lands in the Creative Editor, and is approvable.
- Credit cost is visible before launch; insufficient balance blocks launch; failed jobs release reservations.
- Pre-release smoke against real provider + real ledger is captured with diagnostics.

## Slices

- [x] **S01: Dispatch Engine and Provider Adapters** `risk:high` `depends:[]`
  > After this: Backend server starts without ImportError. `pytest tests/ -x -q` passes adapter contract tests and job lifecycle state transition tests. A POST /api/v1/generation/jobs with dispatch:false returns a job record with status=queued and credits reserved. A manual dispatch call drives a simulated job to succeeded and confirms credits settled; a simulated failure confirms credits released.

- [x] **S02: Frontend Generation Client and Job Status UI** `risk:medium` `depends:[S01]`
  > After this: npm run build succeeds without import errors. AI Studio → Create New → Short Ad Video submits a job and shows async status (queued/running with spinner). Polling advances to succeeded or failed with appropriate UI feedback.

- [ ] **S03: Creative Editor Handoff and Owner Approval** `risk:medium` `depends:[S02]`
  > After this: A succeeded video job opens in the Creative Editor as an approvable package. Merchant can approve or request changes. The approval state persists through page refresh.

- [ ] **S04: Pre-release Smoke and Credit Cost Validation** `[sketch]` `risk:low` `depends:[S03]`
  > After this: One real Sora 2 generation and one real HeyGen generation each complete end-to-end with correct credit delta recorded. Credit cost is visible in the model selector before launch. A job submitted with insufficient balance is blocked at the API with a clear error. Smoke diagnostics file captured.

## Boundary Map

Not provided.
