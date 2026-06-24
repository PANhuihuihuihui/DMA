---
quick_task: phase3-multilingual-creative-variants
status: complete
created_at: 2026-06-19T02:05:00Z
phase: 03-predis-replica-plus-proof-loop
---

# Phase 3 Multilingual Creative Variants

## Evidence

- Predis.ai home page says users can "Create multilingual ads for global campaigns" and "switch input and output language in two clicks."
- Predis.ai also positions AI-generated creatives as editable multi-platform social content.
- LocalPilot should adapt that idea to local-business organic publishing, not paid campaign booking.

## Goal

Add a backend-owned multilingual creative variant flow so a generated creative can produce localized copy packages for customer demos.

## Scope

- Add persistent multilingual variant records for generated creatives.
- Add an API route to generate variants from an existing creative.
- Serialize variants through the Phase 3 workspace/creative payload.
- Add UI controls to generate English, Spanish, and Chinese local-business variants.
- Add tests and smoke coverage proving the route, workspace serialization, and UI are wired.

## Verification

- `npm run test:phase3`
- `npm run test:phase3-screens`
- `npm run build`
