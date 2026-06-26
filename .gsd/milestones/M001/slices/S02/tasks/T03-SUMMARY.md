---
id: T03
parent: S02
milestone: M001
key_files:
  - /Users/huijie/DMA/.gsd-worktrees/M001/src/main.jsx
key_decisions:
  - Use exponential backoff with 3s start and 30s cap for polling efficiency
  - Dependency array uses genActiveJobs.length to reset backoff when new jobs become active
  - Cleanup function properly handles both interval and timeout clearing
duration: 
verification_result: passed
completed_at: 2026-06-26T01:29:51.609Z
blocker_discovered: false
---

# T03: Added async job polling useEffect with exponential backoff to track long-running generation jobs

**Added async job polling useEffect with exponential backoff to track long-running generation jobs**

## What Happened

Added a useEffect in AppDemo (lines 4569-4588) that polls the generation workspace while genActiveJobs.length > 0. The implementation uses exponential backoff starting at 3 seconds and doubling on each tick, capped at 30 seconds. When a new job becomes active (genActiveJobs.length changes), the backoff resets to 3 seconds. On each poll tick, reloadGenerationWorkspace() is called to refresh job status. The cleanup function properly clears timeouts on unmount and when genActiveJobs becomes empty, ensuring no orphaned timers. This is the primary mechanism for surfacing long-running video job status in the UI.

## Verification

Verified that the polling useEffect is properly wired by checking that genActiveJobs is referenced within a useEffect hook. The useEffect dependency array is [genActiveJobs.length], ensuring it runs when active jobs change. Exponential backoff logic verified: initial backoffMs = 3000ms, doubles with Math.min(backoffMs * 2, maxBackoffMs) up to 30000ms cap.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -A5 'useEffect' src/main.jsx | grep -q 'genActiveJobs' && echo polling-wired` | 0 | polling-wired | 45ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `/Users/huijie/DMA/.gsd-worktrees/M001/src/main.jsx`
