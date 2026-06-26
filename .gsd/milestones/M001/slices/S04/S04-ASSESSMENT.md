---
sliceId: S04
uatType: runtime-executable
verdict: PASS
attempt: 1
runId: uat:M001:S04:attempt-1
worktreeRoot: /Users/huijie/DMA/.gsd-worktrees/M001
date: 2026-06-26T03:47:57.823Z
---

# UAT Result - S04

## Checks

| Check | Mode | Result | Evidence | Notes |
|-------|------|--------|----------|-------|
| Test Case 1: Catalog Credit Costs - Run CatalogCostTest to verify Sora 2 credit_cost=180, HeyGen credit_cost=220, readiness_status=ready | runtime | PASS | gsd_uat_exec:76b80bbf-d5f5-4373-b380-8f282d32bb3b | All 10 tests passed: Sora 2 (model_key, provider_key, credit_cost=180, capability=video, readiness=ready) and HeyGen (model_key, provider_key, credit_cost=220, capability=avatar_video, readiness=ready). Duration: 433ms. |
| Test Case 2: Model API Surface - Run ModelApiSurfaceTest to verify GET /api/v1/generation/models exposes creditCost fields | runtime | PASS | gsd_uat_exec:cd93848b-1aeb-42b5-8d93-7d195e560eb4 | Both API surface tests passed: openai_video (Sora 2) creditCost=180 and heygen creditCost=220 exposed via HTTP endpoint. Duration: 1233ms. |
| Test Case 3: Insufficient Balance Gating - Run InsufficientBalanceTest to verify zero-balance merchant is blocked from job creation | runtime | PASS | gsd_uat_exec:6d65711e-6d3c-4ee6-ac49-45a623914848 | Insufficient balance test passed: zero-balance merchant with no credit account raises StoreError(404) with correct message. Duration: 164ms. |
| Test Case 4: Catalog Costs via Smoke Script - Verify CATALOG_COSTS check shows status=PASS with openai_video=180, heygen=220 | runtime | PASS | gsd_uat_exec:5dc909b3-c354-4813-bbc3-ea60c42ec981 | Smoke script CATALOG_COSTS check passed with detail 'openai_video=180, heygen=220'. Elapsed: 20ms. |
| Test Case 5: Insufficient Balance via Smoke Script - Verify INSUFFICIENT_BALANCE check shows status=PASS with credit-related detail | runtime | PASS | gsd_uat_exec:5dc909b3-c354-4813-bbc3-ea60c42ec981 | Smoke script INSUFFICIENT_BALANCE check passed with detail 'Got expected StoreError status=404: Credit account not configured.' Elapsed: 19ms. |
| Test Case 6: Model API Surface via Smoke Script - Verify MODEL_API_SURFACE check shows status=PASS with credit costs exposed | runtime | PASS | gsd_uat_exec:5dc909b3-c354-4813-bbc3-ea60c42ec981 | Smoke script MODEL_API_SURFACE check passed with detail 'openai_video creditCost=180, heygen creditCost=220'. HTTP server confirmed endpoint availability. Elapsed: 534ms. |
| Test Case 7: Provider Real-Generation Checks - Verify SORA2_REAL_GEN and HEYGEN_REAL_GEN show SKIP (expected in CI without API keys) or PASS (with keys) | runtime | PASS | gsd_uat_exec:5dc909b3-c354-4813-bbc3-ea60c42ec981 | Both provider checks correctly show SKIP status (OPENAI_API_KEY and HEYGEN_API_KEY not set in CI environment). Expected behavior: CI runs without real provider calls for safety, local developer runs can set keys for real testing. smoke_s04_report.json summary: 3 pass, 2 skip, 0 fail (total 5). |

## Overall Verdict

PASS - All automatable checks passed: catalog costs verified (Sora 2=180, HeyGen=220), model API surface exposes creditCost fields correctly, insufficient balance gating works (zero-balance merchant blocked), and smoke diagnostics script completed successfully with 3 pass and 2 expected skip (API keys absent for real provider checks).

## Tool Presentation

```json
{
  "surface": "mcp",
  "presentedTools": [
    "gsd_uat_exec",
    "gsd_uat_result_save",
    "gsd_resume",
    "gsd_milestone_status",
    "gsd_journal_query",
    "Glob",
    "Grep",
    "Read",
    "find",
    "glob",
    "grep",
    "ls",
    "read"
  ],
  "blockedTools": [
    {
      "name": "Edit",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "Write",
      "reason": "forbidden during run-uat"
    },
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
      "name": "search-the-web",
      "reason": "forbidden during run-uat"
    },
    {
      "name": "Bash",
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
      "name": "WebSearch",
      "reason": "forbidden during run-uat"
    }
  ],
  "toolPresentationPlanId": "run-uat/default-v1"
}
```

## Gate

Aggregate UAT gate saved as pass.
