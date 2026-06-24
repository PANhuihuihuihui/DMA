# Phase 2: Publishing Engine Reuse Decision - Pattern Map

**Mapped:** 2026-06-10  
**Files analyzed:** 8  
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---:|---|---|
| `backend/app/contracts.py` | model | transform | `backend/app/contracts.py` | exact |
| `backend/app/store.py` | model | CRUD | `backend/app/store.py` | exact |
| `backend/app/server.py` | route | request-response | `backend/app/server.py` | exact |
| `backend/app/fake_publisher.py` | service | workflow/event-driven | `backend/app/fake_publisher.py` | exact |
| `src/api/publishingClient.js` | api | request-response | `src/api/publishingClient.js` | exact |
| `src/models/publishing.js` | model | transform | `src/models/publishing.js` | exact |
| `src/publishing/workflow.js` | utility | transform | `src/publishing/workflow.js` | exact |
| `src/routes/AppRoutes.jsx` / `src/routes/DebugRoute.jsx` / `src/components/*` | route/component | request-response | respective files | exact |

## Pattern Assignments

### Provider contract layer

**Closest analogs:** `backend/app/contracts.py` and `src/models/publishing.js`

- `backend/app/contracts.py:42-58, 132-165, 168-213` centralizes redaction, snapshot building, and safe serialization.
- `src/models/publishing.js:23-221` normalizes mixed payload shapes into stable app contracts for drafts, approvals, attempts, events, and jobs.
- Use these as the contract boundary for any `PublishingProvider`-style comparison scaffold. Keep provider payloads summarized/redacted at the contract edge, not in UI or route code.

### Store / backend-owned workflow

**Closest analog:** `backend/app/store.py`

- `backend/app/store.py:523-589` builds the backend workflow graph from merchants, channels, drafts, approvals, and jobs.
- `backend/app/store.py:677-750` freezes exact-version approval and idempotency behavior.
- `backend/app/store.py:782-912` shows the publish-job / attempt / outcome split and the duplicate-outcome guard.
- `backend/app/store.py:957-1071` serializes jobs for both product UI and support/debug views.

### Route/API boundary to preserve

**Closest analogs:** `backend/app/server.py`, `src/api/publishingClient.js`, `src/routes/AppRoutes.jsx`

- `backend/app/server.py:30-87` is a thin path router that delegates to store/service functions and returns JSON errors consistently.
- `src/api/publishingClient.js:16-55` keeps all client fetch logic behind a single request helper plus narrow endpoint functions.
- `src/routes/AppRoutes.jsx:7-15` keeps route composition separate from page content and debug support paths.
- Preserve this split so Phase 2 can add provider-comparison endpoints or screens without embedding provider logic in UI components.

### Workflow / debug scaffolding

**Closest analogs:** `backend/app/fake_publisher.py`, `src/publishing/workflow.js`, `src/components/PublishTimeline.jsx`, `src/components/ApprovalSnapshot.jsx`, `src/components/RetryPublishControl.jsx`, `src/routes/DebugRoute.jsx`

- `backend/app/fake_publisher.py:8-217` is the current seam for provider-like behavior, retry classification, and deterministic outcomes.
- `src/publishing/workflow.js:127-237` is the frontend normalization layer for approval snapshots and publish-job summaries.
- `src/components/PublishTimeline.jsx:19-199` and `src/routes/DebugRoute.jsx:41-320` are the best places to hang future comparison scaffolding because they already render attempts, diagnostics, and redacted support data.
- `src/components/RetryPublishControl.jsx:20-33` is the existing retry action boundary if Phase 2 needs to compare engine behavior against retry semantics.

## Shared Patterns

- Keep provider secrets and raw diagnostics out of browser storage; the current boundary uses redacted snapshots plus `tokenBoundaryRef` serialization.
- Keep approvals exact-version and idempotent; `backend/app/store.py` rejects alternate draft versions and duplicate outcomes.
- Keep support/debug views read-only and redacted; do not let comparison scaffolding bypass the same redaction path used by job serialization.
- Keep API calls thin and endpoint-specific; do not fold provider comparison logic into `src/api/publishingClient.js`.

## Anti-Patterns / Seams

- `backend/app/server.py` is still hand-routed and string-path based; Phase 2 should mention this as a seam, not a place to bury provider logic.
- `backend/app/fake_publisher.py` is intentionally fake and platform-string switched (`facebook` / `tiktok`); it is a scaffold, not the provider abstraction.
- `src/main.jsx` still acts as a broad composition root in this app, so any new provider comparison UI should stay in the dedicated route/component files.
- `src/models/publishing.js` currently normalizes the backend shape, but it does not define provider behavior; keep behavior in backend/service boundaries.

## No Analog Gaps

None. The current codebase already has direct analogs for contract, store, route, client, workflow, and debug scaffolding.

## Metadata

**Pattern extraction date:** 2026-06-10
