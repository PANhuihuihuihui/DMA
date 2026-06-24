# Phase 6 Discussion Log — Manual Fallback And Pilot Support

**Date:** 2026-06-24
**Mode:** discuss (default)

Human-reference audit log of the discussion. Not consumed by downstream agents — see `06-CONTEXT.md` for the canonical decisions.

## Areas Selected
All five presented gray areas: trigger policy, manual package, completion tracking, operator console, app-review evidence.

## Area 1 — Fallback trigger policy
- **Options:** auto-mark terminal non-retryable classes (recommended) / audit+scope only / manual-only.
- **Decision:** Auto-mark on terminal non-retryable classes (`authentication`, `scope`, `creator_setting`, `media_validation`, `audit_or_visibility_block`, `unknown`); retryable classes stay `retry_needed`. → D-01, D-02.

## Area 2 — Manual publishing package (STATUS-04)
- **Options:** JSON + copy text (recommended) / JSON only / file only.
- **Decision:** Not needed — do not give the merchant a manual-upload/manual-package option this phase. → Deferred (STATUS-04).

## Area 3 — Completion tracking (STATUS-05)
- **Options:** new `manual_completed` status (recommended) / published+flag / event-only.
- **Decision:** Not needed this phase. → Deferred (STATUS-05).

## Area 4 — Operator console boundary & auth
- **Options:** new `/api/v1/admin/*` + role gating (recommended) / extend `/debug/publish-jobs` / operator token.
- **Decision:** New `/api/v1/admin/*` namespace reusing redacted serializers, gated by operator/owner session role + localhost/dev allowance. → D-04, D-05, D-06, D-07.

## Area 5 — App-review evidence (ADMIN-04)
- **Options:** per-job redacted export bundle (recommended) / generated markdown doc / defer doc.
- **Decision:** Per-job redacted evidence export (JSON) composing existing data. → D-08.

## Clarification — merchant manual path scope
- **Question:** What do "no manual upload" + "no completion tracking" mean for STATUS-04/05?
- **Decision:** Drop both this phase. Phase 6 = operator support console + auto-fallback marking + redacted diagnostics + safe retry + app-review evidence export. STATUS-04 & STATUS-05 deferred.

## Deferred Ideas
- STATUS-04 merchant manual package; STATUS-05 manual completion tracking; manual-upload media workflow.

## the agent's Discretion (captured in CONTEXT.md)
- Admin route shapes / serializer reuse; operator-role representation + dev allowance; where auto-fallback marking is invoked; evidence export composition; manual-support-path representation.
