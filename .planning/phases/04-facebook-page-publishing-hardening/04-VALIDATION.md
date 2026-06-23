---
phase: 4
slug: facebook-page-publishing-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-23
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (backend) + Node smoke scripts (`scripts/smoke-*.mjs`) |
| **Config file** | none — tests discovered via `python3 -m unittest discover backend/tests` |
| **Quick run command** | `python3 -m unittest backend.tests.test_facebook_publisher backend.tests.test_facebook_oauth backend.tests.test_token_boundary -v` |
| **Full suite command** | `npm test` (runs backend unittest discover + smoke scripts + build) |
| **Estimated runtime** | ~60–120 seconds (full suite incl. build) |

---

## Sampling Rate

- **After every task commit:** Run the quick run command (relevant Facebook/token tests)
- **After every plan wave:** Run `npm test`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds (quick), ~120 seconds (full)

---

## Per-Task Verification Map

> Filled in concretely by the planner per task. Skeleton below reflects the validation targets from RESEARCH.md "Validation Architecture".

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | SEC-02/D-01..D-05 | T-04-01 | Page token stored as ciphertext only; raw token never serialized to client | unit | `python3 -m unittest backend.tests.test_token_boundary -v` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | D-04/D-05 | T-04-02 | Prod + no key → fail closed; dev + no key → labeled insecure fallback | unit | `python3 -m unittest backend.tests.test_token_boundary -v` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | ACCT-01/ACCT-02 | — | OAuth callback returns N pages without committing; select commits one active + token | unit | `python3 -m unittest backend.tests.test_facebook_oauth -v` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | ACCT-03 | T-04-03 | Publish blocked when health != connected; allowed when connected | unit | `python3 -m unittest backend.tests.test_facebook_publisher -v` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 3 | FB-02/FB-03/MEDIA-03 | — | Link `/feed?link=`; single image `/photos?url=`; invalid media → 400 pre-job | unit | `python3 -m unittest backend.tests.test_facebook_publisher -v` | ❌ W0 | ⬜ pending |
| 04-04-02 | 04 | 3 | FB-04/FB-05/FB-06 | — | Post ID/permalink stored; 190 → reconnect_required; retry no duplicate | unit | `python3 -m unittest backend.tests.test_facebook_publisher -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/requirements.txt` — pin `cryptography` (first third-party Python dep); CI/dev `pip install`
- [ ] Test setup sets `LOCALPILOT_TOKEN_KEY` (generated Fernet key) so encrypted-token tests can run
- [ ] Extend `backend/tests/test_token_boundary.py` (or new `test_facebook_token_store.py`) — encryption round-trip + fail-closed
- [ ] Extend `backend/tests/test_facebook_oauth.py` — page-list/select split
- [ ] Extend `backend/tests/test_facebook_publisher.py` — link/photo publish + media validation + 190 handling (reuse `opener`/`graph_base` seams)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Facebook Page publish through a real Meta app | FB-02/FB-03 | Requires real Meta app, Page admin, and approved permissions | Configure `FACEBOOK_APP_ID/SECRET`, connect a test Page, approve a draft, publish, verify live post + permalink |
| App-review evidence completeness | FB-01 | Documentation/screencast artifact | Review the docs artifact against Meta App Review checklist |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
