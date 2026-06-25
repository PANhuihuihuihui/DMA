# Phase 11: Carousel Generation - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 11 extends the existing Phase 13 generation platform so a merchant can generate a branded multi-slide carousel from one idea or one public URL, using the backend-owned generation job and credit framework instead of a separate carousel engine. The output should become a full five-slide branded carousel package that opens in the existing Creative Editor and still follows the normal approval flow before any publishing step.

</domain>

<decisions>
## Implementation Decisions

### Carousel Structure
- **D-01:** Default carousel output is a fixed five-slide template.
- **D-02:** The exact slide order is locked: cover, problem, proof, offer, CTA.
- **D-03:** Merchant gives one core input and the system expands it into the full five-slide storyline.
- **D-04:** Phase 11 should generate the full slide package for each slide: real image, copy, and brand layout.

### URL Source Behavior
- **D-05:** Phase 11 should accept any public page URL as a carousel source input.
- **D-06:** The URL provides content only; brand styling still comes from the saved merchant profile and brand kit.
- **D-07:** URL extraction should focus on core marketing and story content only, not full visual-brand inference.
- **D-08:** Weak or noisy URLs should degrade gracefully and still produce a usable carousel draft where possible.
- **D-09:** Pre-release validation must include a manual smoke using a real public URL such as Nike and a real MiniMax-backed image generation path.
- **D-10:** The manual smoke must run through the normal merchant or test-account credit ledger and subtract real credits; no bypass or free internal path.

### Brand And Layout Strictness
- **D-11:** Carousel visuals should use a strong brand lock by default.
- **D-12:** Phase 11 should start with one canonical carousel layout preset only.
- **D-13:** Generation should use only saved brand-kit values for colors, typography, logo behavior, and voice; no URL-derived style override.
- **D-14:** Logo placement should stay fixed on every slide in the canonical preset.

### Post-Generation Editing Handoff
- **D-15:** Completed carousel generation should open directly in the existing Creative Editor.
- **D-16:** First Phase 11 handoff supports slide-level editing only; deep layer-level tooling is not a requirement of this phase.
- **D-17:** The editor should open with all five generated slides loaded as one editable carousel package.
- **D-18:** Carousel outputs still go through the normal owner approval flow before publishing or downstream use.

### the agent's Discretion
- Exact backend schema names, job payload shapes, and prompt-planning internals, as long as they respect the locked five-slide structure and reuse the Phase 13 generation framework.
- Exact Creative Editor packaging shape for the five-slide handoff, as long as the merchant lands on one complete editable carousel package.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project And Scope
- `.planning/PROJECT.md` — product wedge, merchant-owned workflow rules, and v2.0 generative engine direction.
- `.planning/ROADMAP.md` — Phase 11 goal, dependency on Phase 13, reuse strategy, and success criteria.
- `.planning/REQUIREMENTS.md` — `GENC-01` and neighboring milestone requirements that constrain scope.
- `.planning/STATE.md` — current milestone routing and recent completed generation/onboarding/auth work.

### Prior Phase Context
- `.planning/phases/13-aitoearn-inspired-credits-and-multi-provider-generation-plat/13-CONTEXT.md` — locked backend-first generation-platform decisions that Phase 11 must extend instead of replacing.
- `.planning/phases/03-local-campaign-draft-workbench/03-01-SUMMARY.md` — prior Creative Editor, media asset, and carousel/storyboard surface behavior already present in the product.
- `.planning/phases/03-local-campaign-draft-workbench/03-02-PLAN.md` — existing carousel config and brand-kit-extension seams that may be reusable, but must not expand Phase 11 scope by default.

### Existing Code Seams
- `backend/app/server.py` — generation and media routes where Phase 11 will connect.
- `backend/app/store.py` — generation records, creative media assets, storyboard/carousel seed structures, and credit-aware persistence patterns.
- `backend/app/generation_dispatch.py` — normalized async job lifecycle and retry behavior to extend.
- `backend/app/generation_providers/openai_adapter.py` — current real image generation adapter seam and provider error handling pattern.
- `src/api/generationClient.js` — frontend boundary for model catalog, balances, job creation, and job status.
- `src/main.jsx` — AI Studio, carousel config UI, Creative Editor handoff surface, and approval flow.
- `src/styles.css` — existing carousel and Creative Editor styling hooks.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/main.jsx` already contains carousel style presets, aspect-ratio choices, and AI Studio generation workspace patterns that can be upgraded instead of replaced.
- `backend/app/store.py` already contains generated creative, media asset, storyboard, and carousel-oriented seed records that can anchor a real carousel package flow.
- `backend/app/generation_dispatch.py` plus the Phase 13 provider catalog already provide the async job and credit-metering seams this phase should reuse.
- `src/api/generationClient.js` already exposes the generation catalog and job client boundary; Phase 11 should extend that boundary rather than invent a second generation client.

### Established Patterns
- Generation authority stays in the backend; the frontend should render normalized results, not provider-native payloads.
- Credits and job state are backend-owned and auditable; carousel generation must be metered through the same ledger path as other generation work.
- Existing product direction prefers one coherent generation workspace and reuse of current Creative Editor surfaces over adding one-off generation panels.

### Integration Points
- AI Studio should admit a carousel job through the existing model/cost/job launch path.
- Successful carousel generation should hand off into the existing Creative Editor as a single five-slide package.
- Approval remains part of the downstream flow; Phase 11 must not bypass the current owner-approval discipline.

</code_context>

<specifics>
## Specific Ideas

- The canonical output should feel like one reliable branded carousel product, not five unrelated generated images.
- The merchant brand kit remains authoritative even when the source content comes from an arbitrary public page URL.
- Manual pre-release smoke should use a real Nike page, real MiniMax-backed imagery, and real credit subtraction from the normal merchant or test-account ledger.

</specifics>

<deferred>
## Deferred Ideas

- Additional carousel layout presets beyond the first canonical preset.
- Layer-level editing as a Phase 11 requirement.
- Free or bypassed internal smoke-test credits; validation should stay on the real ledger path.
- Automated browser coverage for the Nike + MiniMax smoke; current intent is manual pre-release validation.

</deferred>

---

*Phase: 11-Carousel Generation*
*Context gathered: 2026-06-25*
