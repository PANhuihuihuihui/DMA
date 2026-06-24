# Phase 02 Comparison Matrix

## Decision Frame

Phase 02 compares two paths:
- Postiz-style reuse behind a LocalPilot `PublishingProvider` boundary
- Native provider adapters owned by LocalPilot from the start

The comparison is constrained by Phase 01 outcomes:
- Backend-owned workflow records remain the source of truth.
- Approval snapshots, attempt history, idempotency, and redacted diagnostics stay LocalPilot-owned.
- Explicit merchant approval is required before any live publish request.
- Production publishing rejects scraping, cookie posting, and browser-session automation.

## Comparison Criteria

| Criterion | Why it matters | Postiz-style reuse | Native adapters |
|---|---|---|---|
| Facebook connect/list/post | Must support the core merchant publishing loop | Good API surface for connect/list/post via docs and provider schemas | Direct control over Page posting and LocalPilot-specific gating |
| TikTok upload/post | Must handle the stricter media and visibility rules | Exposes upload/direct-post style flows, but with heavier compliance assumptions | Lets LocalPilot shape upload/draft fallback and Direct Post gates explicitly |
| Media submission | Must fit public media delivery constraints | Requires publicly reachable HTTPS media and extra ops assumptions | Can be designed around LocalPilot storage and delivery requirements |
| Status and error reporting | Support needs redacted, audit-friendly diagnostics | Has state/error surfaces, but no clear approval snapshot or attempt ledger contract | Can be shaped exactly to LocalPilot support and audit needs |
| Workflow record ownership | Backend must own approval snapshots, attempts, idempotency, and redaction | Partial fit; would need adapter wrapping and contract translation | Exact fit; LocalPilot controls the record model directly |
| Deployment burden | Ops cost and setup complexity matter for MVP speed | Heavy self-host stack: AGPL-3.0, Docker Compose, PostgreSQL, Redis, Temporal | Lighter path if LocalPilot only builds the needed backend boundary |
| Licensing fit | Must not create avoidable legal/ops friction | AGPL-3.0 adds adoption and redistribution considerations | No inherited AGPL obligations from a reused engine |
| CLI/MCP role | Must stay developer-only, not a production runtime path | Useful for spike tooling, but not appropriate as the merchant runtime | Not applicable; LocalPilot runtime stays API-backed |

## Threshold Rules

Use Postiz-style reuse only if all of the following remain true:
1. The approved payload version stays immutable in LocalPilot.
2. Attempt rows and idempotency remain LocalPilot-owned.
3. Debug and diagnostics stay redacted at the LocalPilot boundary.
4. CLI and MCP remain developer-only spike tooling.
5. Production publishing remains free of scraping, cookie posting, and browser-session automation.

If any of the above require Postiz to become the source of truth, the reuse path is a no-go for runtime publishing.

## Evidence Summary

### Postiz strengths

- Public API surfaces exist for integrations and posts.
- Provider docs exist for Facebook and TikTok.
- CLI and MCP exist for developer workflows.
- The stack is already oriented around self-hosted publishing.

### Postiz gaps

- No clear official approval snapshot contract.
- No first-class attempt ledger equivalent in the public API.
- Redacted diagnostics are not a documented public contract.
- The deployment footprint is substantial.
- AGPL-3.0 may be acceptable for research and adapter comparison, but it is a real adoption consideration.

### Native adapter strengths

- Direct alignment with LocalPilot-owned workflow records.
- Easier to preserve approval snapshot immutability and attempt history.
- Easier to keep redacted diagnostics and idempotency fully under LocalPilot control.
- Easier to model Facebook/TikTok differences without inheriting a broad scheduler abstraction.

### Native adapter gaps

- More implementation work up front.
- More provider-specific code to maintain.
- Requires careful follow-up in later phases for Facebook and TikTok compliance details.

## Recommendation Direction

The comparison favors native provider adapters for the runtime path.

Postiz remains useful as:
- a research reference,
- a comparison baseline,
- and possibly developer-only spike tooling.

But Postiz does not win the boundary test for LocalPilot's backend-owned workflow records, approval gating, or redacted diagnostics.

## Constraint Reminder

SEC-04 stays non-negotiable: a merchant must explicitly approve the exact draft version before any live publish request can be submitted.

Production publishing remains barred from scraping, cookie posting, and browser-session automation.

