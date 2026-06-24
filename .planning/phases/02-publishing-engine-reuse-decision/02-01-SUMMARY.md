---
phase: 02-publishing-engine-reuse-decision
plan: 01
subsystem: publishing-engine-reuse-decision
tags: [postiz, native-adapters, publishing-provider, licensing, facebook, tiktok, api]
requirements-completed:
  - ENGINE-01
  - ENGINE-02
  - ENGINE-03
  - ENGINE-04
  - ENGINE-05
  - SEC-04
  - SEC-05
status: complete
completed: 2026-06-10
---

# Phase 02 Summary: Publishing Engine Reuse Decision

## Decision

**No-go for Postiz-style runtime reuse.**

Phase 02 concludes that LocalPilot should proceed with **native provider adapters** as the runtime publishing path, while keeping Postiz-style tooling only as a research reference and possible developer-only spike aid.

## Why This Wins

Postiz is a credible reference system:
- it exposes public API, CLI, MCP, and OAuth surfaces,
- it covers Facebook and TikTok entry points,
- and it is self-hostable.

But it does not beat LocalPilot's boundary requirements:
- LocalPilot must own backend workflow records.
- LocalPilot must preserve immutable approval snapshots.
- LocalPilot must keep attempt history and idempotency in its own contract.
- LocalPilot must keep redacted diagnostics under its own support surface.

Postiz also adds meaningful adoption friction:
- AGPL-3.0 matters.
- The recommended self-host stack is heavy.
- CLI and MCP are better suited to developer research than merchant runtime publishing.

So the strongest product decision is to keep the runtime publishing engine native to LocalPilot's backend boundary rather than borrowing Postiz as the primary engine.

## Evidence Synthesis

### Facebook

Postiz can connect and post through documented API surfaces, which is useful as a comparison baseline.

However, LocalPilot still needs to preserve:
- exact draft version approval,
- audit trail for who approved,
- and backend-owned status transitions.

Native adapters are the cleaner fit for that boundary.

### TikTok

Postiz exposes TikTok posting and upload-style surfaces, but TikTok is the stricter compliance surface.

The phase confirms that LocalPilot should treat:
- public HTTPS media,
- creator-info-driven settings,
- and audit-gated Direct Post

as LocalPilot-controlled decisions rather than inheriting a scheduler's assumptions.

### Status, error, and diagnostics

Postiz offers status and error fields, but not the same support contract LocalPilot already established in Phase 1:
- approval snapshots,
- attempt ledger,
- idempotency,
- and redacted diagnostics.

That support boundary is a core product asset and should stay LocalPilot-owned.

### Deployment and licensing

The comparison found a heavier self-host story than a thin adapter path:
- PostgreSQL
- Redis
- Temporal
- Docker Compose
- AGPL-3.0

Those are acceptable for a reusable infrastructure experiment, but not compelling enough to make Postiz the runtime engine for LocalPilot's MVP.

## Residual Risk

Choosing native adapters means more custom implementation work later:
- provider-specific Facebook code,
- provider-specific TikTok code,
- and continued care around media and compliance edges.

That is still preferable to giving up LocalPilot's backend-owned workflow model or inheriting a heavier scheduling stack that does not naturally carry the approval and diagnostic contracts we already need.

## Constraint Preservation

SEC-04 remains a hard requirement:
- a merchant must explicitly approve the exact draft version before any live publish request.

Production publishing remains forbidden from:
- scraping,
- cookie posting,
- and browser-session automation.

CLI and MCP stay developer-only spike tooling, not the merchant runtime.

## Next Phase Boundary

Phase 03 should build on this decision by using native provider adapters as the path forward for local campaign draft generation and platform-native Facebook/TikTok records.

