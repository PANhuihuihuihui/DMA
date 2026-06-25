---
phase: 11
slug: carousel-generation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-25
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` + existing Node smoke scripts |
| **Config file** | none — existing repo test commands |
| **Quick run command** | `python3 -m unittest backend.tests.test_phase11_carousel_generation -v` |
| **Full suite command** | `python3 -m unittest discover backend/tests -v` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m unittest backend.tests.test_phase11_carousel_generation -v`
- **After every plan wave:** Run `python3 -m unittest discover backend/tests -v`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | GENC-01 | T-11-01 | Carousel job admission reserves one package-level charge and stores fixed slide order | unit/integration | `python3 -m unittest backend.tests.test_phase11_carousel_generation -v` | ✅ | ⬜ pending |
| 11-01-02 | 01 | 1 | GENC-01 | T-11-02 | MiniMax-backed dispatch persists five outputs and one creative/five asset handoff without leaking secrets | unit/integration | `python3 -m unittest backend.tests.test_phase11_carousel_generation -v` | ✅ | ⬜ pending |
| 11-01-03 | 01 | 1 | GENC-01 | T-11-03 | AI Studio idea flow launches the default MiniMax carousel job, renders one branded five-slide package card, and opens the editor handoff correctly | smoke | `python3 -m unittest backend.tests.test_phase11_carousel_generation -v && npm run test:phase3-screens` | ✅ | ⬜ pending |
| 11-02-01 | 02 | 2 | GENC-01 | T-11-04 | Public URL intake uses guarded fetch/extraction and does not override merchant brand styling | integration | `python3 -m unittest backend.tests.test_phase11_carousel_generation -v` | ✅ | ⬜ pending |
| 11-02-02 | 02 | 2 | GENC-01 | T-11-05 | Weak/noisy URLs degrade gracefully into a usable fallback storyline on the same package job path | integration | `python3 -m unittest backend.tests.test_phase11_carousel_generation -v` | ✅ | ⬜ pending |
| 11-03-01 | 03 | 3 | GENC-01 | T-11-06 | Editor remains slide-locked with approval continuity and no layer/preset unlocks, and the success-card-to-editor handoff keeps the saved composed slide payload visible | integration/smoke | `python3 -m unittest backend.tests.test_phase11_carousel_generation backend.tests.test_phase3_workspace -v && npm run test:phase3-screens` | ✅ | ⬜ pending |
| 11-03-02 | 03 | 3 | GENC-01 | T-11-07 | Real Nike URL + MiniMax + normal ledger smoke succeeds and subtracts real credits | manual | `manual-only` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/test_phase11_carousel_generation.py` — targeted contract coverage for Phase 11 carousel admission, dispatch, and editor handoff
- [x] Existing backend unittest infrastructure covers the phase
- [x] Existing manual smoke path covers the real-provider pre-release gate

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Nike URL + MiniMax + real ledger smoke | GENC-01 | Requires real provider credits, real public URL fetch, and real merchant/test-account credit subtraction | Launch a carousel from a real Nike public URL using the default MiniMax carousel model, wait for the five-slide package to materialize, confirm one `generated_creative` plus five ordered `creative_media_assets`, open it in Creative Editor, and confirm the normal credit ledger shows the real package debit with no bypass path. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or explicit manual-only coverage
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all required references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
