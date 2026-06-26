---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T03: Added async job polling useEffect with exponential backoff to track long-running generation jobs

Add a useEffect in AppDemo that polls GET /api/v1/generation/jobs while genActiveJobs.length > 0. Use exponential backoff: start at 3s, double each tick up to 30s cap, reset to 3s when a new job becomes active. On each tick call reloadGenerationWorkspace(). Clean up the interval/timeout on unmount and when genActiveJobs drops to zero. This is the only place long-running video jobs surface their status in the UI.

## Inputs

- `src/main.jsx lines 4449-4450 — genActiveJobs derived value`
- `src/main.jsx lines 4326-4346 — reloadGenerationWorkspace`

## Expected Output

- `src/main.jsx`

## Verification

cd /Users/huijie/DMA/.gsd-worktrees/M001 && grep -n 'genActiveJobs' src/main.jsx | grep -q useEffect && echo polling-wired
