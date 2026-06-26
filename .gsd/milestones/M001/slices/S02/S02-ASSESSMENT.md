---
sliceId: S02
uatType: browser-executable
verdict: PASS
attempt: 2
runId: uat:M001:S02:attempt-2
worktreeRoot: /Users/huijie/DMA/.gsd-worktrees/M001
date: 2026-06-26T04:20:49.715Z
---

# UAT Result - S02

## Checks

| Check | Mode | Result | Evidence | Notes |
|-------|------|--------|----------|-------|
| AI Studio loads with model catalog showing all 4 provider models | browser | PASS | screenshot:.gsd/exec/ai-studio.png |  |
| Sora 2 video job submitted and appears in Job activity with status chip | browser | PASS | screenshot:.gsd/exec/ai-studio.png |  |
| Generated videos section appears after succeeded video job | browser | PASS | gsd_uat_exec:77dae941-317a-4271-99fe-2e77380b028e<br>screenshot:.gsd/exec/ai-studio-video-output.png |  |

## Overall Verdict

PASS - Live browser session confirmed AI Studio loads with full model catalog, job submission and activity tracking work, and succeeded video jobs surface in the Generated videos section.

## Tool Presentation

```json
{
  "surface": "mcp",
  "presentedTools": [
    "mcp__gsd-workflow__gsd_uat_exec",
    "mcp__gsd-workflow__gsd_uat_result_save",
    "mcp__gsd-workflow__gsd_resume",
    "mcp__gsd-workflow__gsd_milestone_status",
    "mcp__gsd-workflow__gsd_journal_query",
    "gsd_uat_exec",
    "gsd_uat_result_save",
    "gsd_resume",
    "gsd_milestone_status",
    "gsd_journal_query",
    "find",
    "glob",
    "grep",
    "ls",
    "read",
    "browser_navigate",
    "browser_click",
    "browser_type",
    "browser_fill_form",
    "browser_click_ref",
    "browser_fill_ref",
    "browser_wait_for",
    "browser_assert",
    "browser_verify",
    "browser_screenshot",
    "browser_snapshot_refs",
    "browser_find",
    "browser_get_console_logs",
    "browser_get_network_logs",
    "browser_evaluate",
    "browser_reload",
    "browser_batch",
    "browser_act"
  ],
  "blockedTools": [
    {
      "name": "gsd_exec",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "gsd_summary_save",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "gsd_save_gate_result",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "edit",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "write",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "search-the-web",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "WebSearch",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "Bash",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "Write",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "Edit",
      "reason": "forbidden during run-uat"
    }
  ],
  "notes": "Browser session via gsd-browser CLI; Vite proxy to backend on port 8790",
  "toolPresentationPlanId": "run-uat/default-v1"
}
```

## Gate

Aggregate UAT gate saved as pass.
