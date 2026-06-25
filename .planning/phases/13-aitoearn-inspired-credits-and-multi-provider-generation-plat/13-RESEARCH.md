# Phase 13: AiToEarn-Inspired Credits And Multi-Provider Generation Platform - Research

**Researched:** 2026-06-25
**Domain:** Backend-owned generation control plane on LocalPilot's current Python/SQLite + React seams [VERIFIED: LocalPilot codebase]
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Product Direction
- **D-01:** Replace the current near-term planning focus with an AiToEarn-informed generation platform phase. Do not spend planning effort on the previously active Phase 7 as the next execution target.
- **D-02:** Borrow architecture and UX ideas from AiToEarn, but do not adopt its backend wholesale. Reuse patterns, not runtime coupling.
- **D-03:** Treat this as one coordinated phase with two explicit tracks: backend implementation plus tests, and frontend interaction surface.

### Backend Ownership
- **D-04:** Backend is the source of truth for provider credentials, provider routing, credits or balance, job state, output references, and retries.
- **D-05:** Generation must run through a provider-agnostic contract with adapters underneath it, not through provider-specific logic leaking into the UI or route layer.
- **D-06:** Credits or balance logic must be ledger-backed and auditable. Reservation, settlement, release, and failure paths must be deterministic and testable.
- **D-07:** The first provider targets must explicitly cover GPT-backed generation flows and CCDance-style video or avatar flows, even if one starts behind a bounded stub seam that preserves the final adapter contract.
- **D-08:** Generation jobs are asynchronous and normalized. Do not use long blocking requests as the core runtime path.

### Frontend Contract
- **D-09:** The frontend must expose one coherent generation workspace, not scattered debug panels.
- **D-10:** The workspace must show model catalog, provider identity, credit cost, prompt and settings entry, job status, history, and output retrieval.
- **D-11:** Cost visibility must happen before job launch, and insufficient-balance states must be understandable in the UI.

### Architecture and Safety
- **D-12:** Reuse current LocalPilot seams where practical: backend persistence patterns, status models, frontend API clients, and current React shell. Do not rewrite unrelated publishing flows.
- **D-13:** Secrets, provider keys, and refresh tokens remain server-side only.
- **D-14:** The phase must include automated verification for credit correctness, adapter contract behavior, lifecycle transitions, and the critical frontend interaction flow.

### the agent's Discretion
- Exact data model names for credits, ledger entries, provider models, and generation jobs.
- Exact queue runtime choice, as long as the lifecycle is normalized and testable.
- Exact frontend information architecture within the generation workspace, as long as model choice, cost, launch, status, and result retrieval remain first-class.

### Deferred Ideas (OUT OF SCOPE)
- Full billing plans, subscriptions, or payment-provider integration beyond an internal credit or balance model.
- Broad provider expansion beyond the first GPT and CCDance-style targets.
- Full carousel-specific flow if it does not help the first generation control-plane slice.
- Non-generation roadmap items like Google login and website crawl, unless a later dependency proves unavoidable.
</user_constraints>

## Project Constraints (from AGENTS.md)

- Extend the current React/Vite app carefully or introduce a backend boundary deliberately; do not treat the frontend demo as the long-term source of truth. [VERIFIED: AGENTS.md]
- Keep OAuth secrets, refresh tokens, API keys, and merchant credentials server-side only; never store them in browser `localStorage` or committed files. [VERIFIED: AGENTS.md]
- Keep Facebook first and TikTok second in platform priority; this phase may add generation capabilities, but it must not dilute the merchant-owned publishing path. [VERIFIED: AGENTS.md]
- Evaluate reuse of external tooling before custom provider code, but use official API paths for production behavior and reject scraping, browser automation, or cookie posting. [VERIFIED: AGENTS.md]
- Preserve owner approval before live publish actions; this phase may create generation jobs, but must not weaken approval controls already present in publishing flows. [VERIFIED: AGENTS.md]
- Preserve current code conventions: Python backend route switch + SQLite store patterns, React client API boundary, two-space indentation, double quotes in JS, relative imports, and no path aliases. [VERIFIED: AGENTS.md]
- Extend existing backend tests and browser smoke checks instead of introducing an unrelated test stack by default. [VERIFIED: AGENTS.md]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEN-01 | Backend exposes a provider-agnostic generation contract that routes a request to a configured `{provider, model}` with API keys kept server-side only. | Use a catalog-driven adapter registry plus backend-owned provider config tables and route all launches through one `generation_jobs` admission path. [VERIFIED: LocalPilot codebase] [VERIFIED: AiToEarn reference code] |
| GEN-02 | Generation runs as asynchronous jobs with a normalized status lifecycle and a result reference surfaced to the client. | Reuse LocalPilot's publish-job pattern for `queued/running/succeeded/failed` generation jobs and add provider task refs plus append-only attempt/event records. [VERIFIED: LocalPilot codebase] [CITED: https://developers.openai.com/api/docs/guides/video-generation] |
| GEN-03 | Merchant can generate a real image / ad creative from a prompt and brand context. | Keep prompt admission synchronous, dispatch GPT image generation through a backend adapter, and return output asset refs through the workspace API. [VERIFIED: LocalPilot codebase] [CITED: https://developers.openai.com/api/docs/guides/image-generation] |
| CREDIT-01 | System meters credit usage per generation by content type, model, and duration. | Replace the current demo usage heuristic with an append-only ledger using reservation, settlement, and release rows tied to job IDs and catalog cost rules. [VERIFIED: LocalPilot codebase] |
| CREDIT-02 | Merchant can select among available models with visible per-model credit cost. | Expose a backend catalog endpoint that returns provider, capability, supported settings, and credit price for the workspace UI. [VERIFIED: AiToEarn reference code] [VERIFIED: LocalPilot codebase] |
| CREDIT-03 | System enforces plan credit limits and blocks or queues generation when credits are exhausted. | Perform balance checks at job admission in one transaction that writes both the job row and the reservation ledger row. [VERIFIED: LocalPilot codebase] |
| GENV-01 | Merchant can generate a short video from a text prompt. | Treat video generation as async submit + poll/callback, not a blocking HTTP request; normalize external task IDs under the same job contract. [CITED: https://developers.openai.com/api/docs/guides/video-generation] [VERIFIED: AiToEarn reference code] |
| GENV-02 | Merchant can generate a UGC avatar video by selecting an avatar and providing a script, producing a video with voiceover. | Reuse Phase 3's creator-style workflow and UGC package inputs as the frontend/source seam, but route execution through the new catalog + job + ledger system instead of deterministic demo artifacts. [VERIFIED: LocalPilot codebase] [ASSUMED] |
</phase_requirements>

## Summary

LocalPilot should **reuse its existing backend persistence and lifecycle patterns**, not import AiToEarn's NestJS, MongoDB, Redis, or BullMQ runtime. The current backend already has a stable shape for route admission in `backend/app/server.py`, schema/migration growth in `backend/app/store.py`, append-only publish attempts/events, and a narrow frontend client boundary in `src/api/publishingClient.js`; those are the right seams for Phase 13. [VERIFIED: LocalPilot codebase] [VERIFIED: LocalPilot test run]

AiToEarn is most useful here as a **reference architecture** for three ideas: a provider/model registry, a planner-versus-executor split, and normalized async task state with status lookup. LocalPilot should adapt those ideas into its current Python/SQLite stack instead of adopting AiToEarn's framework and infrastructure choices. [VERIFIED: AiToEarn reference code] [VERIFIED: LocalPilot codebase]

The first landing slice should be: backend catalog tables, ledger tables, generation job tables, one GPT-backed image path, one async video/avatar path behind a bounded CCDance-style adapter seam, and a single generation workspace inside `/app`. Cost display must be derived from the backend catalog before launch, and credit correctness must be enforced by transactional reservation/settlement logic rather than the current demo usage math. [VERIFIED: LocalPilot codebase] [CITED: https://developers.openai.com/api/docs/guides/image-generation] [CITED: https://developers.openai.com/api/docs/guides/video-generation] [ASSUMED]

**Primary recommendation:** Extend `backend/app/store.py`, `backend/app/server.py`, `src/api/publishingClient.js`, and the existing `/app` shell with a new generation subsystem; borrow AiToEarn's registry/planner/job patterns, but do not import its runtime stack. [VERIFIED: LocalPilot codebase] [VERIFIED: AiToEarn reference code]

## Reuse / No-Reuse

| Decision | Recommendation | Why |
|----------|----------------|-----|
| Reuse | LocalPilot's SQLite migration style in `store.py` for new generation, ledger, catalog, and attempt/event tables. [VERIFIED: LocalPilot codebase] | It already supports additive schema growth, row serialization, and backend-owned lifecycle state. [VERIFIED: LocalPilot codebase] |
| Reuse | LocalPilot's publish job pattern for immutable attempts, events, redacted diagnostics, and idempotent outcome recording. [VERIFIED: LocalPilot codebase] | Generation jobs need the same auditability guarantees as publish jobs. [VERIFIED: LocalPilot codebase] |
| Reuse | LocalPilot's frontend API boundary in `src/api/publishingClient.js` and current `/app` shell route. [VERIFIED: LocalPilot codebase] | The app already centralizes backend calls and can host a new workspace without a router rewrite. [VERIFIED: LocalPilot codebase] |
| Reuse | Phase 3 creator-style workflow inputs, UGC package concepts, and brand-kit context as source data for avatar/video requests. [VERIFIED: LocalPilot codebase] | Those product concepts already match the merchant-facing creation flow this phase needs. [VERIFIED: LocalPilot codebase] |
| No reuse | The current Phase 3 `creditsUsed` heuristic in `get_phase3_usage_summary`. [VERIFIED: LocalPilot codebase] | It is a demo estimate, not a ledger, and will produce non-auditable billing behavior if promoted. [VERIFIED: LocalPilot codebase] |
| No reuse | `generated_creatives` as the canonical execution record for provider jobs. [VERIFIED: LocalPilot codebase] | Generated creative rows describe workspace artifacts, not provider task lifecycle, reservation state, or retries. [VERIFIED: LocalPilot codebase] |
| No reuse | AiToEarn's NestJS module graph, BullMQ queues, Mongo repositories, and broad provider matrix. [VERIFIED: AiToEarn reference code] | They solve a larger multi-service platform than LocalPilot currently runs and would force an unnecessary stack migration. [VERIFIED: AiToEarn reference code] |
| No reuse | Browser-managed cost or provider state. [VERIFIED: AGENTS.md] | Locked decisions require backend ownership for credits, provider routing, secrets, and job state. [VERIFIED: 13-CONTEXT.md] |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Credit ledger and balance enforcement | API / Backend | Database / Storage | Admission and settlement must be transactional and merchant-scoped before any provider call is launched. [VERIFIED: 13-CONTEXT.md] |
| Provider/model catalog | API / Backend | Database / Storage | The UI can display catalog data, but provider identity, cost, and allowed settings must be backend-owned. [VERIFIED: 13-CONTEXT.md] |
| Generation job admission and retries | API / Backend | Database / Storage | Job creation, reservation, retry safety, and state normalization belong with server-owned credentials and business rules. [VERIFIED: 13-CONTEXT.md] |
| Provider task polling or callback handling | API / Backend | — | External task refs, polling cadence, webhook verification, and result normalization must stay server-side. [CITED: https://developers.openai.com/api/docs/guides/video-generation] [CITED: https://developers.openai.com/api/docs/guides/webhooks] |
| Merchant generation workspace | Browser / Client | API / Backend | The frontend should render catalog, cost, prompt input, status, and results, but not hold authoritative job state. [VERIFIED: 13-CONTEXT.md] |
| Output asset persistence and retrieval | Database / Storage | API / Backend | Generated outputs need stable refs that survive refresh and can later feed approvals and publishing flows. [VERIFIED: LocalPilot codebase] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `sqlite3` | Python 3.14.6 runtime builtin [VERIFIED: LocalPilot environment] | Persist `generation_jobs`, `generation_attempts`, `credit_ledger`, `provider_catalog`, and result refs. [VERIFIED: LocalPilot codebase] | LocalPilot already uses SQLite for workflow, publish, and Phase 3 records, so this lands cleanly without a data-store migration. [VERIFIED: LocalPilot codebase] |
| Python stdlib `http.server` + current route switch | Python 3.14.6 runtime builtin [VERIFIED: LocalPilot environment] | Add `/api/v1/generation/*`, `/api/v1/credits/*`, and `/api/v1/models/*` endpoints in the existing backend process. [VERIFIED: LocalPilot codebase] | `backend/app/server.py` already owns routing and request parsing; Phase 13 does not need a framework swap. [VERIFIED: LocalPilot codebase] |
| React + existing app shell | React 19.2.7 locked in repo [VERIFIED: LocalPilot codebase] | Render the generation workspace inside `/app` with the existing shell and preferences boundary. [VERIFIED: LocalPilot codebase] | The route shell and client API pattern already exist and are sufficient for a single coherent workspace. [VERIFIED: LocalPilot codebase] |
| OpenAI official HTTP APIs | Current official docs as of 2026-06-25 [CITED: https://developers.openai.com/api/docs/guides/image-generation] | Provide the first GPT-backed image path and an official async video path without exposing secrets to the browser. [CITED: https://developers.openai.com/api/docs/guides/image-generation] [CITED: https://developers.openai.com/api/docs/guides/video-generation] | Official endpoints match the locked requirement for backend-owned provider routing and async job handling. [VERIFIED: 13-CONTEXT.md] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `cryptography` | 49.0.0 installed and pinned [VERIFIED: LocalPilot environment] [VERIFIED: LocalPilot codebase] | Reuse existing server-side secret and token-boundary patterns for provider credentials if this phase stores provider API keys. [VERIFIED: LocalPilot codebase] | Use whenever Phase 13 needs persistent provider credentials or encrypted secret refs. [VERIFIED: AGENTS.md] |
| `openai` [WARNING: flagged as suspicious — verify before using.] | 2.44.0 on PyPI, published 2026-06-24 [VERIFIED: PyPI + package-legitimacy] | Optional SDK path for OpenAI images, videos, and webhook helpers. [CITED: https://developers.openai.com/api/docs/guides/webhooks] | Use only after a `checkpoint:human-verify`; the first vertical slice can ship with direct HTTPS calls and polling instead. [VERIFIED: PyPI + package-legitimacy] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLite-backed generation dispatch inside current backend | BullMQ/Redis worker infrastructure like AiToEarn | BullMQ gives richer concurrency and queue introspection, but it forces a stack jump that LocalPilot does not currently need for the first landing slice. [VERIFIED: AiToEarn reference code] [VERIFIED: LocalPilot codebase] |
| Current backend process + additive store schema | Full NestJS/Mongo provider platform like AiToEarn | AiToEarn's runtime is broader than LocalPilot's current needs and would delay Phase 13 behind a platform rewrite. [VERIFIED: AiToEarn reference code] |
| Backend catalog endpoint | Hardcoded frontend model/provider lists | Hardcoding is faster initially, but breaks locked backend ownership for cost, provider routing, and availability. [VERIFIED: 13-CONTEXT.md] |

**Installation:**
```bash
pip install -r backend/requirements.txt
# Optional only after checkpoint:human-verify
pip install openai
```

**Version verification:** `cryptography==49.0.0` is pinned in `backend/requirements.txt` and importable in the current environment. `openai` is available on PyPI at `2.44.0` as of 2026-06-25, but the package-legitimacy seam flagged it `[SUS]` because the current release is very new and download telemetry was unavailable during this run. [VERIFIED: LocalPilot codebase] [VERIFIED: LocalPilot environment] [VERIFIED: PyPI + package-legitimacy]

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `openai` | PyPI [VERIFIED: PyPI + package-legitimacy] | Published 2026-06-24 [VERIFIED: PyPI + package-legitimacy] | unknown during seam check [VERIFIED: PyPI + package-legitimacy] | `github.com/openai/openai-python` [VERIFIED: PyPI + package-legitimacy] | SUS [VERIFIED: PyPI + package-legitimacy] | Flagged — planner must add `checkpoint:human-verify` before install. [VERIFIED: PyPI + package-legitimacy] |

**Packages removed due to [SLOP] verdict:** none. [VERIFIED: PyPI + package-legitimacy]
**Packages flagged as suspicious [SUS]:** `openai`. [VERIFIED: PyPI + package-legitimacy]

## Architecture Patterns

### System Architecture Diagram

```text
Merchant in /app workspace
  -> Generation workspace form (prompt, capability, model, settings)
  -> POST /api/v1/generation/jobs
  -> Backend admission transaction
       -> validate merchant/session
       -> load provider/model catalog row
       -> reserve credits in credit_ledger
       -> create generation_job + initial event
  -> Dispatcher / poller
       -> select queued jobs
       -> call provider adapter submit()
       -> persist provider_task_ref + running status
       -> poll provider status or process verified callback
       -> store output refs
       -> settle or release credits
       -> append final event/attempt
  -> GET /api/v1/generation/jobs + /api/v1/models + /api/v1/credits
  -> Workspace renders history, balance, failures, and outputs
```

### Recommended Project Structure

```text
backend/app/
├── server.py                    # add /api/v1/generation/*, /api/v1/models/*, /api/v1/credits/*
├── store.py                     # add generation tables, ledger ops, serializers, migrations
├── generation_catalog.py        # code-seeded catalog + catalog validation helpers
├── generation_dispatch.py       # queued-job pickup, submit/poll orchestration
├── generation_providers/
│   ├── base.py                  # provider adapter contract
│   ├── openai_adapter.py        # GPT image + official async video path
│   └── ccdance_stub.py          # bounded submit/status/result seam until concrete provider is chosen
└── generation_status.py         # normalized status + error mapping helpers

src/
├── api/generationClient.js      # generation workspace API boundary
├── models/generation.js         # catalog, balance, and job normalizers
├── components/generation/       # workspace panels and job history UI
└── main.jsx                     # mount generation workspace inside existing /app shell
```

### Pattern 1: Ledger-Backed Reservation, Settlement, Release
**What:** Write an append-only `credit_ledger` row for every reservation, settlement, release, and manual adjustment; derive visible balance from the ledger or from a cached balance snapshot maintained by the same transaction path. [VERIFIED: 13-CONTEXT.md]
**When to use:** For every generation job that can consume credits or fail after admission. [VERIFIED: 13-CONTEXT.md]
**Example:**
```python
# Source: LocalPilot pattern adapted from publish job admission in backend/app/store.py
def create_generation_job(conn, merchant_id, catalog_row, request_payload):
    with conn:
        balance = current_credit_balance(conn, merchant_id)
        cost = catalog_row["credit_cost"]
        if balance < cost:
            raise StoreError(409, "Insufficient credits.")
        job_id = new_id("generation_job")
        insert_credit_ledger_row(conn, merchant_id, job_id, "reserve", -cost)
        insert_generation_job(conn, job_id, merchant_id, catalog_row, request_payload, "queued")
        append_generation_event(conn, job_id, "queued", "Credits reserved and job accepted.")
        return serialize_generation_job(conn, job_id)
```

### Pattern 2: Catalog-Driven Provider Dispatch
**What:** Store model capability metadata in one backend catalog keyed by `{provider, model, capability}` and let the dispatcher resolve adapters from that catalog instead of from route-specific `if/else` branches. [VERIFIED: AiToEarn reference code]
**When to use:** For image, video, and avatar launches and for cost display in the workspace. [VERIFIED: 13-CONTEXT.md]
**Example:**
```python
# Source: AiToEarn platform registry idea adapted to LocalPilot's Python backend
ADAPTERS = {
    ("openai", "image"): OpenAIImageAdapter(),
    ("openai", "video"): OpenAIVideoAdapter(),
    ("ccdance_stub", "avatar_video"): CCDanceStubAdapter(),
}

def dispatch_job(job, catalog_row):
    key = (catalog_row["provider_key"], catalog_row["capability"])
    adapter = ADAPTERS[key]
    return adapter.submit(job, catalog_row)
```

### Pattern 3: Sync Admission, Async Execution
**What:** The HTTP request should validate, reserve credits, create the job row, and return immediately; execution and completion happen in a background loop or verified callback path. [CITED: https://developers.openai.com/api/docs/guides/video-generation] [CITED: https://developers.openai.com/api/docs/guides/background]
**When to use:** Any provider call that can run longer than one request/response round trip or can require later polling. [CITED: https://developers.openai.com/api/docs/guides/video-generation]
**Example:**
```python
# Source: OpenAI async video flow adapted to LocalPilot
def handle_generation_launch(conn, payload):
    job = create_generation_job(conn, payload["merchantId"], load_catalog_row(conn, payload["modelId"]), payload)
    wake_dispatch_loop()
    return {"status": "accepted", "job": job}
```

### Pattern 4: Reuse Publish-Style Attempts and Events
**What:** Mirror LocalPilot's `publish_attempts` and `publish_events` design for generation attempts and state changes. [VERIFIED: LocalPilot codebase]
**When to use:** Submit retries, provider polling transitions, result-finalization, and failure classification. [VERIFIED: LocalPilot codebase]
**Example:**
```python
# Source: LocalPilot publish lifecycle adapted to generation lifecycle
append_generation_attempt(conn, job_id, attempt_number, "running", provider_task_ref, diagnostics)
append_generation_event(conn, job_id, "running", "Provider task accepted.")
```

### Anti-Patterns to Avoid

- **Promoting Phase 3 usage math into billing:** `creditsUsed` in `get_phase3_usage_summary` is deterministic demo math, not auditable ledger state. [VERIFIED: LocalPilot codebase]
- **Provider-specific routes per model family:** Do not create `/generate-openai-image`, `/generate-avatar-video`, and similar route sprawl; keep one admission surface and route internally by catalog row. [VERIFIED: 13-CONTEXT.md]
- **Blocking provider calls in request handlers:** Video generation is explicitly async in official docs, and long-running provider work will make the current server brittle if kept inline. [CITED: https://developers.openai.com/api/docs/guides/video-generation]
- **Importing AiToEarn's runtime stack wholesale:** Its registry and queue ideas are reusable, but its NestJS/BullMQ/Mongo architecture is out of proportion to LocalPilot's current runtime. [VERIFIED: AiToEarn reference code]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Credit balance enforcement | Mutable `balance` counter without history | Append-only ledger plus transactional derived balance | It is the only approach that can support reservation, settlement, release, audit, and retry safety together. [VERIFIED: 13-CONTEXT.md] |
| Provider/model availability in UI | Frontend constants scattered across components | Backend `provider_catalog` endpoint | Locked decisions require backend ownership of cost, provider routing, and capability metadata. [VERIFIED: 13-CONTEXT.md] |
| Async provider status tracking | Browser polling the provider directly | Backend-owned poll/callback path with normalized job status | Secrets must stay server-side and provider state must be normalized before the UI sees it. [VERIFIED: AGENTS.md] |
| Distributed queue platform | Custom Redis/Bull clone for Phase 13 | Current SQLite job table + in-process dispatcher for first slice | The current stack already supports additive persistence and testable job loops; distributed infra is premature here. [VERIFIED: LocalPilot codebase] [ASSUMED] |
| Avatar/video prompt orchestration | Duplicate image/video/avatar launch code per provider | One adapter contract with capability-specific settings | AiToEarn's provider split shows that the contract boundary is the reusable idea, not separate endpoint families. [VERIFIED: AiToEarn reference code] |

**Key insight:** LocalPilot already solved the hard part of backend-owned workflow state in publishing; Phase 13 should reuse that pattern for generation and only add the missing catalog, ledger, and provider-dispatch pieces. [VERIFIED: LocalPilot codebase]

## Common Pitfalls

### Pitfall 1: Charging Credits From Demo Usage Math
**What goes wrong:** The system shows balances that drift from actual provider work because generation cost is inferred from creative counts instead of from ledger events. [VERIFIED: LocalPilot codebase]
**Why it happens:** `get_phase3_usage_summary` currently computes credits from counts of creatives, assets, batches, and competitor runs for demo UX only. [VERIFIED: LocalPilot codebase]
**How to avoid:** Introduce `credit_ledger` and reserve/settle/release entries tied to job IDs before any real provider launch. [VERIFIED: 13-CONTEXT.md]
**Warning signs:** Credits decrease after draft edits or view refreshes rather than only after admitted jobs. [ASSUMED]

### Pitfall 2: Letting Provider Logic Leak Into Routes Or UI
**What goes wrong:** Route handlers and React components become full of model-specific branching, making later provider additions high-risk. [VERIFIED: AiToEarn reference code]
**Why it happens:** It is tempting to special-case the first GPT path and the first avatar path. [ASSUMED]
**How to avoid:** Keep one admission endpoint, one catalog lookup, and one adapter interface with provider-specific behavior under the adapter layer. [VERIFIED: 13-CONTEXT.md]
**Warning signs:** New provider work requires edits in both `server.py` and multiple UI components for every model. [ASSUMED]

### Pitfall 3: Treating Async Video As A Blocking HTTP Operation
**What goes wrong:** The current `ThreadingHTTPServer` spends threads waiting on external provider work, increasing timeouts and making retries opaque. [VERIFIED: LocalPilot codebase]
**Why it happens:** Image generation can feel synchronous, so teams often over-generalize that path to video. [ASSUMED]
**How to avoid:** Keep admission synchronous, persist a provider task ref, and move long-running progress through backend polling or verified callbacks. [CITED: https://developers.openai.com/api/docs/guides/video-generation]
**Warning signs:** Generation endpoints exceed normal request latency or need increasing server timeout knobs. [ASSUMED]

### Pitfall 4: Rewriting The Runtime To Match AiToEarn
**What goes wrong:** Phase 13 becomes a platform migration instead of a merchant-visible generation slice. [VERIFIED: AiToEarn reference code]
**Why it happens:** AiToEarn exposes mature queue and registry abstractions, but they are bundled with a much broader service architecture. [VERIFIED: AiToEarn reference code]
**How to avoid:** Copy the registry/planner/job ideas, not the framework, database, or provider sprawl. [VERIFIED: AiToEarn reference code]
**Warning signs:** Plans start with Redis, Mongo, Nest modules, or queue workers before any LocalPilot generation workspace exists. [ASSUMED]

## Code Examples

Verified patterns from official or inspected sources:

### OpenAI Async Video Admission
```python
# Source: https://developers.openai.com/api/docs/guides/video-generation
def submit_openai_video(adapter_input):
    provider_task = post_videos(adapter_input)      # returns provider id + initial status
    return {
        "providerTaskRef": provider_task["id"],
        "providerStatus": provider_task["status"],
    }

def refresh_openai_video(provider_task_ref):
    result = get_video(provider_task_ref)           # poll until terminal state
    return normalize_provider_result(result)
```

### LocalPilot-Style Append-Only Attempt Recording
```python
# Source: LocalPilot publish lifecycle in backend/app/store.py
def record_generation_attempt(conn, job_id, provider_task_ref, diagnostics):
    attempt = insert_generation_attempt(
        conn,
        job_id=job_id,
        status="running",
        provider_task_ref=provider_task_ref,
        diagnostics=diagnostics,
    )
    append_generation_event(conn, job_id, "running", "Provider accepted generation task.")
    return attempt
```

### Backend Catalog Response For The Workspace
```javascript
// Source: LocalPilot publishingClient pattern adapted for generation
export const loadGenerationCatalog = () => requestJson("/generation/catalog");
export const loadGenerationBalance = () => requestJson("/generation/balance");
export const createGenerationJob = (payload) =>
  requestJson("/generation/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Demo-estimated credit usage from creative counts | Ledger-backed reservation/settlement/release tied to real jobs | Phase 13 recommendation [VERIFIED: LocalPilot codebase] | Prevents double-spend, supports audit, and makes insufficient-balance behavior testable. [VERIFIED: 13-CONTEXT.md] |
| Provider-specific launch behavior exposed at the route layer | Catalog-driven provider dispatch behind one backend admission surface | Established in AiToEarn reference architecture [VERIFIED: AiToEarn reference code] | Reduces coupling and makes new providers cheaper to add. [VERIFIED: AiToEarn reference code] |
| Long-running provider work held inside one request | Async admission plus polling or verified callbacks | Current official provider guidance [CITED: https://developers.openai.com/api/docs/guides/video-generation] | Fits the current server better and keeps lifecycle visible to the UI. [VERIFIED: LocalPilot codebase] |

**Deprecated/outdated:**
- Treating the Phase 3 `usage` block as real billing state is outdated for this phase; keep it as demo UX only until the ledger exists. [VERIFIED: LocalPilot codebase]
- Treating generated creative rows as provider job truth is outdated for this phase; job truth should move to dedicated generation job tables. [VERIFIED: LocalPilot codebase]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A bounded in-process dispatcher loop is sufficient for the first Phase 13 landing slice before external queue infrastructure is needed. [ASSUMED] | Standard Stack, Don't Hand-Roll | If provider latency or concurrency is higher than expected, execution may need a separate worker sooner. |
| A2 | The concrete CCDance-style provider can fit a normalized `submit/status/result` adapter contract with optional avatar/template inputs. [ASSUMED] | Summary, Architecture Patterns | If the chosen provider has a radically different lifecycle, the adapter contract may need expansion. |
| A3 | The current `/app` shell can host the generation workspace without a route-tree rewrite. [ASSUMED] | Reuse / No-Reuse, Recommended Project Structure | If the shell layout is too constrained, Phase 13 may need targeted route extraction similar to prior debug/review routes. |
| A4 | Browser smoke coverage can remain script-based instead of introducing a new JS unit-test framework for this phase. [ASSUMED] | Validation Architecture | If the workspace interaction becomes too stateful, the team may need frontend component tests sooner. |

## Open Questions

1. **Which concrete provider satisfies the "CCDance-style video/avatar" requirement?**
   - What we know: The phase requires a CCDance-style video/avatar adapter seam, but the locked scope allows one target to start behind a bounded stub that preserves the final contract. [VERIFIED: 13-CONTEXT.md]
   - What's unclear: The exact commercial/API provider and its operational constraints were not specified in the phase inputs. [VERIFIED: 13-CONTEXT.md]
   - Recommendation: Plan the first slice around a stub-capable `avatar_video` adapter contract and make concrete provider selection an explicit checkpoint before live execution. [ASSUMED]

2. **Should provider/model catalog rows be seeded in code or stored as editable admin data first?**
   - What we know: LocalPilot currently grows schema and seed data through `store.py`, and phase scope does not require a separate admin console for provider management. [VERIFIED: LocalPilot codebase]
   - What's unclear: Whether the team needs non-code model price edits during the first slice. [ASSUMED]
   - Recommendation: Start with code-seeded rows inserted by `ensure_database`, then add admin editability only if live pricing churn becomes real. [ASSUMED]

3. **Is verified webhook handling needed in Phase 13, or is polling enough for the first slice?**
   - What we know: Official docs support polling or webhooks for async completion. [CITED: https://developers.openai.com/api/docs/guides/video-generation]
   - What's unclear: Whether LocalPilot needs webhook throughput now, given the current single-process backend. [ASSUMED]
   - Recommendation: Plan polling first and leave a callback seam in the adapter contract so webhook verification can be added without changing job storage. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Backend routes, store, dispatcher, tests | ✓ [VERIFIED: LocalPilot environment] | 3.14.6 [VERIFIED: LocalPilot environment] | — |
| Node.js | Frontend build, browser smoke scripts | ✓ [VERIFIED: LocalPilot environment] | v23.11.0 [VERIFIED: LocalPilot environment] | — |
| npm | Frontend scripts and full-suite command | ✓ [VERIFIED: LocalPilot environment] | 10.9.2 [VERIFIED: LocalPilot environment] | — |
| `cryptography` | Existing secret/token boundary reuse | ✓ [VERIFIED: LocalPilot environment] | 49.0.0 [VERIFIED: LocalPilot environment] | — |
| Redis / BullMQ | AiToEarn-style queue runtime | ✗ required for this plan [VERIFIED: LocalPilot codebase] | — | Use SQLite-backed dispatch loop for first slice. [ASSUMED] |
| OpenAI SDK package | Optional provider helper path | ✗ installed status not checked [ASSUMED] | PyPI 2.44.0 available [VERIFIED: PyPI + package-legitimacy] | Use direct HTTPS calls first. [CITED: https://developers.openai.com/api/docs/guides/image-generation] |

**Missing dependencies with no fallback:**
- None for planning or for the first stub-capable execution slice. [VERIFIED: LocalPilot environment] [ASSUMED]

**Missing dependencies with fallback:**
- Redis/BullMQ are absent, but the recommended plan does not require them. [VERIFIED: LocalPilot environment] [ASSUMED]
- Live provider credentials were not audited in this run; the phase can still execute against stub adapters until secrets are provisioned server-side. [VERIFIED: AGENTS.md] [ASSUMED]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` + existing Node smoke scripts [VERIFIED: LocalPilot codebase] |
| Config file | none — tests run directly via `python3 -m unittest` and script commands in `package.json` [VERIFIED: LocalPilot codebase] |
| Quick run command | `python3 -m unittest backend.tests.test_phase3_workspace backend.tests.test_fake_publish_lifecycle -v` [VERIFIED: LocalPilot test run] |
| Full suite command | `npm test` [VERIFIED: LocalPilot codebase] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GEN-01 | Catalog-driven provider dispatch and merchant-scoped job admission | unit | `python3 -m unittest backend.tests.test_generation_catalog -v` | ❌ Wave 0 |
| GEN-02 | Async lifecycle from queued to terminal with provider refs and result storage | integration | `python3 -m unittest backend.tests.test_generation_jobs -v` | ❌ Wave 0 |
| GEN-03 | GPT-backed image path returns result refs without exposing secrets | integration | `python3 -m unittest backend.tests.test_generation_openai_image -v` | ❌ Wave 0 |
| CREDIT-01 | Reserve, settle, release, and adjustment ledger behavior | unit | `python3 -m unittest backend.tests.test_credit_ledger -v` | ❌ Wave 0 |
| CREDIT-02 | Catalog API returns provider identity and visible cost for the workspace | unit | `python3 -m unittest backend.tests.test_generation_catalog_api -v` | ❌ Wave 0 |
| CREDIT-03 | Insufficient balance blocks admission without partial writes | unit | `python3 -m unittest backend.tests.test_credit_ledger -v` | ❌ Wave 0 |
| GENV-01 | Video submit + status refresh flow normalizes provider async state | integration | `python3 -m unittest backend.tests.test_generation_openai_video -v` | ❌ Wave 0 |
| GENV-02 | Avatar/video request flow reuses creator-style inputs through the new contract | integration + smoke | `python3 -m unittest backend.tests.test_generation_avatar_jobs -v && node scripts/smoke-generation-workspace.mjs` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m unittest <targeted test modules> -v` plus any touched smoke script. [VERIFIED: LocalPilot codebase]
- **Per wave merge:** `python3 -m unittest discover backend/tests -v` and `node scripts/smoke-generation-workspace.mjs`. [VERIFIED: LocalPilot codebase] [ASSUMED]
- **Phase gate:** `npm test` plus a focused generation workspace smoke path before `$gsd-verify-work`. [VERIFIED: LocalPilot codebase] [ASSUMED]

### Wave 0 Gaps

- [ ] `backend/tests/test_credit_ledger.py` — covers CREDIT-01 and CREDIT-03. [ASSUMED]
- [ ] `backend/tests/test_generation_catalog.py` — covers GEN-01 and CREDIT-02. [ASSUMED]
- [ ] `backend/tests/test_generation_jobs.py` — covers GEN-02 lifecycle and retry behavior. [ASSUMED]
- [ ] `backend/tests/test_generation_openai_image.py` — covers GEN-03 adapter contract. [ASSUMED]
- [ ] `backend/tests/test_generation_openai_video.py` — covers GENV-01 async provider path. [ASSUMED]
- [ ] `backend/tests/test_generation_avatar_jobs.py` — covers GENV-02 adapter behavior. [ASSUMED]
- [ ] `scripts/smoke-generation-workspace.mjs` — covers launch, insufficient-balance UX, status refresh, and result rendering in the browser. [ASSUMED]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no new auth in phase, but existing session identity still gates routes. [VERIFIED: LocalPilot codebase] | Reuse current session + merchant resolution patterns already present in backend routes. [VERIFIED: LocalPilot codebase] |
| V3 Session Management | yes [VERIFIED: LocalPilot codebase] | Scope all generation balance, jobs, and outputs to the current merchant/user context. [VERIFIED: LocalPilot codebase] |
| V4 Access Control | yes [VERIFIED: 13-CONTEXT.md] | Merchant-scoped catalog visibility, balance reads, job history reads, and retry actions. [VERIFIED: 13-CONTEXT.md] |
| V5 Input Validation | yes [VERIFIED: 13-CONTEXT.md] | Validate model IDs, capability types, duration/aspect settings, prompt length, and avatar/template IDs in backend admission. [VERIFIED: 13-CONTEXT.md] |
| V6 Cryptography | yes [VERIFIED: AGENTS.md] | Reuse `cryptography` and existing token-boundary patterns for provider secrets; never store them in browser state. [VERIFIED: AGENTS.md] [VERIFIED: LocalPilot codebase] |

### Known Threat Patterns for LocalPilot's Phase 13 Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Credit double-spend via retry or race | Tampering | Reserve credits and create the job row in one transaction; make settlement idempotent per job/attempt. [VERIFIED: 13-CONTEXT.md] |
| Cross-merchant job or balance reads | Information Disclosure | Resolve merchant context on every generation route and filter all reads by merchant ID. [VERIFIED: LocalPilot codebase] |
| Prompt or settings abuse causing runaway provider spend | Denial of Service | Enforce catalog-backed limits on model, duration, image count, aspect ratio, and capability before launch. [VERIFIED: AiToEarn reference code] [ASSUMED] |
| Secret leakage into browser or logs | Information Disclosure | Keep provider credentials server-side and redact provider diagnostics before serializing them. [VERIFIED: AGENTS.md] [VERIFIED: LocalPilot codebase] |
| Forged provider callbacks if webhooks are later enabled | Spoofing | Verify webhook signatures with a server-side secret before mutating job state. [CITED: https://developers.openai.com/api/docs/guides/webhooks] |

## Sources

### Primary (HIGH confidence)
- LocalPilot codebase: `backend/app/server.py`, `backend/app/store.py`, `src/api/publishingClient.js`, `src/main.jsx`, `src/routes/AppRoutes.jsx`, `src/models/publishing.js`, `package.json`, `backend/requirements.txt`. [VERIFIED: LocalPilot codebase]
- LocalPilot tests and execution evidence: `backend/tests/test_phase3_workspace.py`, `backend/tests/test_fake_publish_lifecycle.py`, plus local `python3 -m unittest` run passing 27 tests on 2026-06-25. [VERIFIED: LocalPilot test run]
- AiToEarn reference code: `apps/aitoearn-ai/src/core/draft-generation/*`, `apps/aitoearn-ai/src/core/ai/video/*`, `apps/aitoearn-ai/src/core/ai/libs/openai/*`, `apps/aitoearn-server/src/core/channels/platforms/platforms.registry.ts`, `libs/aitoearn-queue/src/*`. [VERIFIED: AiToEarn reference code]

### Secondary (MEDIUM confidence)
- OpenAI image generation guide: `https://developers.openai.com/api/docs/guides/image-generation`. [CITED: https://developers.openai.com/api/docs/guides/image-generation]
- OpenAI video generation guide: `https://developers.openai.com/api/docs/guides/video-generation`. [CITED: https://developers.openai.com/api/docs/guides/video-generation]
- OpenAI background mode guide: `https://developers.openai.com/api/docs/guides/background`. [CITED: https://developers.openai.com/api/docs/guides/background]
- OpenAI webhooks guide: `https://developers.openai.com/api/docs/guides/webhooks`. [CITED: https://developers.openai.com/api/docs/guides/webhooks]

### Tertiary (LOW confidence)
- Optional in-process dispatcher sufficiency for first slice. [ASSUMED]
- Concrete CCDance-style provider contract fit and final vendor choice. [ASSUMED]
- Need for a route-tree change inside the existing `/app` shell. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH for LocalPilot seams, MEDIUM for optional provider SDK choice because the recommended path avoids a mandatory new package. [VERIFIED: LocalPilot codebase] [VERIFIED: PyPI + package-legitimacy]
- Architecture: MEDIUM because LocalPilot and AiToEarn patterns are clear, but the exact CCDance-style provider remains unspecified. [VERIFIED: LocalPilot codebase] [VERIFIED: AiToEarn reference code] [ASSUMED]
- Pitfalls: MEDIUM because they are strongly grounded in the current demo/runtime mismatch and provider async behavior. [VERIFIED: LocalPilot codebase] [CITED: https://developers.openai.com/api/docs/guides/video-generation]

**Research date:** 2026-06-25
**Valid until:** 2026-07-02
