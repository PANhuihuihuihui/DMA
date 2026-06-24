# Looping Engineering Plan for LocalPilot AI

Owner: Pan
Project: LocalPilot AI (`/Users/huijie/DMA`)
Status: design plan, not implemented yet

## 0. North Star

Build a personal-project engineering loop that turns Pan's idea into a verified artifact, then captures the lessons as reusable constraints and skills.

The loop should not be "one big agent prompt". It should be a small operating system:

```text
SPEC.md + CONSTRAINTS.md
        ↓
orchestrator plans and routes
        ↓
engineering executes the smallest working slice
        ↓
verifier tries to refute it
        ↓
BLOCK rules append to CONSTRAINTS.md
        ↓
rerun until pass or circuit break
        ↓
stable workflow becomes a skill
```

For this repo, the active Hermes team is:

```text
default       Pan's personal entrypoint
orchestrator  harness/coordinator
engineering   execution loop / builder
verifier      hostile verify gate
market        market-research input when needed
outbound      content/outbound drafts when needed
Pan           deployer / public-release owner
```

Deleted legacy profiles:

```text
research -> replaced by market
socials  -> replaced by outbound
```

## 1. Three-layer stack for our setup

### Harness — owned by Hermes profiles

Harness means who sees what, who is allowed to act, and who returns structured output.

Mapping:

| Harness part | Hermes profile | Job |
|---|---|---|
| Coordinator | `orchestrator` | Reads SPEC/CONSTRAINTS, breaks work into slices, owns loop state and gates |
| Executor | `engineering` | Implements one slice in the repo; uses GSD + Ponytail to avoid bloat |
| Refuter | `verifier` | Runs hostile verification with a different profile/model |
| Research input | `market` | Only when product/market/source claims are needed |
| Drafting input | `outbound` | Only when final deliverable needs copy/lead/content drafts |
| Release | Pan | Only Pan pushes/deploys/sends/publishes |

Rule: the executor should not see the whole past. It sees only:

```text
- SPEC.md
- CONSTRAINTS.md
- current slice instructions
- relevant files only
- previous verify BLOCKs for this slice
```

The verifier sees:

```text
- SPEC.md
- CONSTRAINTS.md
- git diff / changed files
- commands actually run
- screenshots/logs/build outputs
```

### Loop — owned by repo files + small runner

Loop means the repeatable process:

```text
Trigger -> Load constraints -> Plan slice -> Execute -> Observe -> Verify -> Evolve -> Repeat/Stop
```

The loop must have five hard parts:

1. Trigger
2. Feedback gate
3. Exit condition
4. Verify model/profile
5. Constraints file

### Skill — owned by `~/.hermes/skills` or profile-local skills

Skill means a repeated loop pattern becomes reusable.

A workflow should only become a skill after:

```text
- used at least twice
- had at least one verify failure folded into CONSTRAINTS.md
- has a concrete trigger and output schema
- has a verification checklist
```

## 2. Files to add to `/Users/huijie/DMA`

### Phase 1 files

```text
SPEC.md
CONSTRAINTS.md
.harness/LOOP.md
.harness/state.json
.harness/runs/YYYYMMDD-HHMMSS/
.harness/templates/SPEC.template.md
.harness/templates/VERIFY_GATE.md
.harness/templates/SLICE.md
.harness/templates/RUN_REPORT.md
```

Recommended contents:

#### `SPEC.md`

One active contract for the current feature/slice. Not a prompt.

Must include:

```text
PROJECT
GOAL
SCOPE IN / OUT
RULES
SOURCES
OUTPUT type/count/naming/schema
ON_CONFLICT
STOP_CONDITION
BUDGET steps/time/cost
VERIFY_COMMANDS
```

For LocalPilot, every SPEC should include these default rules:

```text
- No OAuth secrets, refresh tokens, API keys, or merchant credentials in browser localStorage.
- Publishing requires explicit owner approval before any post is sent.
- Facebook first, TikTok second, Xiaohongshu deferred.
- Use official APIs for production publishing; no scraping/cookie posting for production.
- Near-term app is React/Vite in src/main.jsx and src/styles.css unless backend boundary is explicitly in scope.
```

#### `CONSTRAINTS.md`

Project-level hard rules, auto-loaded before every loop.

Seed it with current repo constraints:

```text
# CONSTRAINTS.md

## Always loaded
- Do not store OAuth secrets, refresh tokens, API keys, or merchant credentials in browser localStorage or committed files.
- Publishing must require explicit user approval before posts are sent.
- Facebook is priority 1, TikTok priority 2, Xiaohongshu deferred.
- Production publishing must use official API paths; no scraping, browser automation, or cookie posting.
- Keep near-term changes inside React/Vite frontend unless SPEC explicitly defines a backend boundary.
- If a claim relies on numbers or external platform behavior, cite source or mark [UNVERIFIED].
- If verifier returns BLOCK, append one rule here before rerun.
- Same slice failing 3 times triggers circuit break and report to Pan.
```

#### `.harness/state.json`

Small machine-readable loop state:

```json
{
  "active_spec": "SPEC.md",
  "run_id": null,
  "slice_id": null,
  "status": "idle",
  "consecutive_failures": 0,
  "max_failures": 3,
  "last_verdict": null,
  "last_verified_commit": null
}
```

## 3. Loop protocol

### Step A — Trigger

Initial triggers should be manual only:

```text
Pan says: loop this / run engineering loop / execute SPEC.md
```

Later triggers can be added:

```text
- file change: SPEC.md changes
- issue/kanban card moves to Ready
- scheduled hardening pass
- verifier failure creates rerun
```

Do not start with cron. Cron comes after the loop is boring and reliable.

### Step B — Orchestrator prepares slice

`orchestrator` reads:

```text
/Users/huijie/DMA/SPEC.md
/Users/huijie/DMA/CONSTRAINTS.md
/Users/huijie/DMA/AGENTS.md
```

Then outputs one slice:

```text
SLICE_ID
GOAL
FILES_ALLOWED
FILES_FORBIDDEN
ACCEPTANCE_CRITERIA
VERIFY_COMMANDS
BUDGET
CONSTRAINTS_TO_WATCH
```

Ponytail rule: if code is not needed, do not code. Report that the slice is unnecessary.

### Step C — Engineering executes

`engineering` runs the slice.

It must use:

```text
- GSD execute-phase / quick / verify-work when applicable
- ponytail for simplest working implementation
- ponytail-review before handoff if diff feels bloated
```

Engineering output must include:

```text
- files changed
- exact commands run
- command outputs summary
- what was intentionally skipped
- risks / known gaps
```

Engineering should not:

```text
- deploy
- push
- send external messages
- broaden scope without SPEC change
```

### Step D — Verifier refutes

`verifier` runs hostile review.

Strict output:

```text
| Row | Item | Status | Why |
|-----|------|--------|-----|
| 1 | ... | PASS/RISK/BLOCK | ... |
```

Verifier must check:

```text
- SPEC compliance
- CONSTRAINTS compliance
- build/test result
- UI/screenshots for visual tasks
- secrets/token leakage
- browser localStorage boundaries
- owner approval before publish
- no accidental external sends
```

BLOCK rule:

```text
Every BLOCK must include one line to append to CONSTRAINTS.md.
```

### Step E — Evolve constraints

If verifier returns BLOCK:

1. Extract each BLOCK rule.
2. Append under `CONSTRAINTS.md -> Failure-derived rules`.
3. Increment `consecutive_failures`.
4. If failures >= 3, stop and report to Pan.
5. Else rerun the same slice with updated constraints.

If PASS:

1. Reset failure count.
2. Mark slice pass.
3. If more slices remain, continue.
4. If complete, write run report.

## 4. Runner design

Start with a dumb script, not a giant platform.

Create later:

```text
scripts/loop.mjs
```

Commands:

```bash
node scripts/loop.mjs init
node scripts/loop.mjs plan
node scripts/loop.mjs execute
node scripts/loop.mjs verify
node scripts/loop.mjs evolve
node scripts/loop.mjs run
```

But implementation should be boring:

```text
- reads SPEC.md and CONSTRAINTS.md
- creates .harness/runs/<run_id>/
- writes slice prompt files
- calls Hermes profile CLIs, e.g. orchestrator / engineering / verifier
- captures stdout/stderr
- parses verifier BLOCK lines
- updates state.json
```

No database. No queue. No dashboard. Not yet.

Ponytail default: filesystem is the database until proven insufficient.

## 5. Concrete MVP loop

MVP should support one manual feature slice:

```text
Input:
- SPEC.md
- CONSTRAINTS.md

Run:
- orchestrator creates .harness/runs/<id>/slice-001.md
- engineering executes slice
- verifier reviews diff and commands
- if BLOCK: append constraints and stop/rerun
- if PASS: write RUN_REPORT.md

Output:
- .harness/runs/<id>/RUN_REPORT.md
- updated CONSTRAINTS.md if needed
- changed app files
```

MVP does not need:

```text
- parallel waves
- cron
- 300 agents
- cost accounting
- web dashboard
- automatic git commit
- automatic deploy
```

## 6. Apply to current Predis-style Phase 3 work

Example SPEC for the current LocalPilot UI/workflow hardening:

```text
PROJECT: LocalPilot Phase 3 Predis-style workflow parity
GOAL: Make the logged-in LocalPilot app match the reference screenshots' workflow structure closely enough for a sales demo.
SCOPE IN:
  - React/Vite frontend changes in src/main.jsx and src/styles.css
  - Login-after-dashboard workflow
  - Campaign/post generation UI parity
  - Review/approval states
SCOPE OUT:
  - Real OAuth token storage
  - Real Facebook/TikTok publishing
  - Backend secrets
  - Scraping/cookie posting
RULES:
  validation: npm run build passes; verifier browser QA passes against reference screenshots; no token/secret in localStorage.
OUTPUT:
  type: code + screenshot QA report
  count: 1 working app build + 1 verifier report
  naming: .harness/runs/<run_id>/RUN_REPORT.md
STOP_CONDITION: 3 verifier BLOCK cycles or build cannot run due environment blocker.
BUDGET:
  steps_max: 12
  time_max: 120 minutes
```

## 7. Model/profile strategy

Use profiles as the real harness boundary:

| Stage | Profile | Model strategy |
|---|---|---|
| Plan/decompose | orchestrator | cheap/fast unless complex |
| Execute | engineering | strong coding model; has GSD + Ponytail |
| Verify | verifier | different model family/provider where possible |
| Market facts | market | only when product/market claims are in scope |
| Draft copy | outbound | only when content/outreach draft is in scope |

Do not let engineering verify itself.

## 8. Promotion path

### Stage 1 — Manual loop

Pan runs it by asking default/orchestrator.

Success criterion:

```text
3 feature slices completed with PASS and useful constraint additions.
```

### Stage 2 — Scripted loop

Add `scripts/loop.mjs`.

Success criterion:

```text
The script creates run folders, captures profile outputs, and updates state without manual copy/paste.
```

### Stage 3 — Skill-backed loop

Create a Hermes skill, likely:

```text
looping-engineering
```

Skill contains:

```text
- trigger conditions
- file templates
- runner commands
- verify gate rules
- troubleshooting
```

Success criterion:

```text
Any future personal project can copy the same loop files and run the protocol.
```

### Stage 4 — Background agent

Only after manual/scripted loop is boring.

Triggers:

```text
- SPEC.md changed
- issue marked ready
- nightly ponytail-audit
```

Delivery rule:

```text
Ping Pan only on PASS, BLOCK, or deviation above threshold.
No silent infinite loops.
```

## 9. Implementation phases

### Phase L0 — Templates only

Create:

```text
SPEC.md
CONSTRAINTS.md
.harness/templates/*
```

No automation.

### Phase L1 — Manual profile loop

Run one LocalPilot slice manually through:

```text
orchestrator -> engineering -> verifier
```

Capture outputs under `.harness/runs/`.

### Phase L2 — Scripted local runner

Create `scripts/loop.mjs` with manual subcommands.

### Phase L3 — Auto evolve constraints

Parse verifier output and append BLOCK rules to CONSTRAINTS.md.

### Phase L4 — Skill extraction

Create `looping-engineering` skill from the proven flow.

### Phase L5 — Optional background mode

Add cron only for safe jobs:

```text
nightly ponytail-audit
weekly dependency/bloat review
watch SPEC.md and propose plan, but do not auto-write code unless Pan asks
```

## 10. Hard guardrails

- No public deploy, git push, external sends, posts, or lead outreach without Pan explicitly approving that exact action.
- No secrets in repo, localStorage, logs, screenshots, or run reports.
- No infinite retry loop.
- No scope expansion without editing SPEC.md.
- No claiming PASS without verifier evidence.
- No auto-creating skills from one-off experiments; require repeated stable use.

## 11. My recommended next action

Do Phase L0 now:

```text
1. Create SPEC.md template in repo root.
2. Create CONSTRAINTS.md with LocalPilot's current hard rules.
3. Create .harness/templates/VERIFY_GATE.md.
4. Create .harness/state.json.
```

Then use it immediately on the current Phase 3 Predis-style UI/workflow task.
