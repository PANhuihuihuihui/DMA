# Phase 11: Carousel Generation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-25
**Phase:** 11-Carousel Generation
**Areas discussed:** Carousel structure, URL source behavior, Brand/layout strictness, Post-generation editing handoff

---

## Carousel Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed 5-slide template | Cover, problem, proof, offer, CTA; easiest to keep brand-safe and predictable. | ✓ |
| Style-based template families | Reuse existing style presets and vary the structure by preset. | |
| Fully dynamic slide planning | Let the model decide slide count and sequence each time. | |

**User's choice:** Fixed 5-slide template.
**Notes:** User locked the exact order as cover → problem → proof → offer → CTA; wanted one core input expanded into the full story; wanted full slide packages with image + copy + brand layout for each slide.

---

## URL Source Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Any public page URL | Allow landing pages, product pages, blog posts, menu pages, and similar public URLs. | ✓ |
| Only merchant-owned URLs | Keep the source bounded to the merchant's own site. | |
| Two explicit URL types | Separate merchant-site URLs from external reference URLs. | |

**User's choice:** Any public page URL.
**Notes:** User locked that URL supplies content only while the merchant profile and brand kit stay authoritative. Extraction should focus on core marketing/story content only. Weak URLs should degrade gracefully. User explicitly added a manual pre-release smoke requirement using a real Nike URL, real MiniMax image generation, and real credit subtraction from the normal merchant/test ledger.

---

## Brand/Layout Strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Strong brand lock with preset layouts | Merchant colors, typography, logo rules, and approved carousel composition remain fixed. | ✓ |
| Brand-guided but flexible | Keep some brand constraints, but let layout vary more per run. | |
| Mostly model-driven | Treat brand kit as a hint instead of a strong constraint. | |

**User's choice:** Strong brand lock with preset layouts.
**Notes:** User wanted one canonical preset only, with layout driven only by saved brand-kit values and fixed logo placement on every slide.

---

## Post-Generation Editing Handoff

| Option | Description | Selected |
|--------|-------------|----------|
| Open directly in Creative Editor | Generation hands the merchant straight into the existing editing surface. | ✓ |
| Show preview then edit | Add an intermediate review step before editing. | |
| Stay in AI Studio results only | Keep editing out of the first handoff. | |

**User's choice:** Open directly in the existing Creative Editor.
**Notes:** User wanted slide-level editing only for the first Phase 11 handoff, all five slides loaded as one editable package, and the normal approval flow still required before publishing.

---

## the agent's Discretion

- Exact prompt-planning, schema, and job payload shapes inside the existing Phase 13 generation framework.
- Exact representation of the five-slide package inside the Creative Editor, as long as it behaves as one editable carousel unit.

## Deferred Ideas

- Additional carousel presets beyond the first canonical preset.
- Layer-level editing as a Phase 11 requirement.
- Free or bypassed internal smoke-test credits.
- Automated browser coverage for the live Nike + MiniMax smoke.
