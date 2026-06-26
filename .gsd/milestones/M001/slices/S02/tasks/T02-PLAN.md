---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Created src/models/generation.js with defensive normalizers for generation models, jobs, and credit summaries.

Create the generation model normalizer. Exports: normalizeGenerationCatalog(payload), normalizeCreditSummary(credits), normalizeGenerationJob(job), normalizeGenerationJobsList(payload). Mirror the defensive text()/number()/asArray()/asObject() pattern from models/publishing.js. normalizeGenerationJob must carry capability, workflowType, carouselStage, completedSlides, and outputs fields used by main.jsx derived state.

## Inputs

- `src/models/publishing.js — normalizer pattern`
- `src/main.jsx lines 4334-4337 — how normalizeCreditSummary and normalizeGenerationCatalog results are consumed`
- `backend/app/store.py serialize_generation_job — server-side field names`

## Expected Output

- `src/models/generation.js`

## Verification

cd /Users/huijie/DMA/.gsd-worktrees/M001 && node --input-type=module < src/models/generation.js && echo ok
