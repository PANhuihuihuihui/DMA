---
phase: 4
slug: facebook-page-publishing-hardening
status: draft
shadcn_initialized: false
preset: none
created: 2026-06-23
---

# Phase 4 — UI Design Contract

> Visual and interaction contract for the Facebook Page Publishing Hardening frontend surfaces.
> Grounded in the existing LocalPilot design system (`src/styles.css` `:root` tokens). No new design system is introduced — Phase 4 reuses current tokens and component classes.

## Scope — Screens & Surfaces This Phase Adds/Changes

All surfaces live inside the authenticated `/app` workspace (and its connected-accounts/brand area), reusing the existing app shell (236px sidebar + content). New/changed surfaces:

1. **Facebook connect entry (ACCT-01)** — a "Connect Facebook" action in the connected-accounts/brand area that starts OAuth.
2. **Page picker screen (ACCT-02)** — after OAuth returns managed Pages, a selectable list to choose the active publish Page (replaces silent auto-pick). Shown as a modal/panel within `/app`.
3. **Connection & capability health (ACCT-03 / FB-05)** — per-Page status badge: `Connected`, `Action needed` (missing permission), `Reconnect required`. Gates the publish action.
4. **Active Page + switch (D-09/D-10)** — shows the active publish Page with a "Switch Page" affordance among connected Pages.
5. **Media validation feedback (MEDIA-03 / FB-03)** — inline pre-publish validation messages on the draft/review surface when a link or single image fails Facebook checks.
6. **Publish failure actions (FB-05/FB-06)** — on a failed Facebook publish, surface contextual buttons: `Reconnect`, `Retry`, and a `Get manual package` handoff (full manual flow is Phase 6).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (hand-rolled CSS in `src/styles.css`) |
| Preset | not applicable |
| Component library | none — reuse existing app-shell, card, badge, button, and modal classes |
| Icon library | none currently; use text + existing status-dot pattern (no new icon dependency) |
| Font | "Avenir Next", Inter, ui-sans-serif fallback (body/UI); Georgia, serif (display/headings) — both already defined |

---

## Spacing Scale

Declared values (multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Badge inner padding, status-dot gap |
| sm | 8px | Compact gaps (badge↔label, icon↔text) |
| md | 16px | Default element spacing, card inner padding rows |
| lg | 24px | Card padding, Page-list row padding |
| xl | 32px | Section gaps, modal padding |
| 2xl | 48px | Major section breaks in the connect/picker panel |
| 3xl | 64px | Page-level vertical rhythm (rare) |

Exceptions: none (reuse existing layout spacing; do not introduce off-scale values).

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 15px | 400 | 1.5 |
| Label | 13px | 600 | 1.35 |
| Heading | 20px | 600 | 1.3 |
| Display | 28px | 600 (Georgia serif) | 1.2 |

Notes: Page names render as Body 15px/600 (semibold) within list rows. Status badge text is Label 13px. Reuse existing heading classes — do not add new font sizes outside this table.

---

## Color

Palette from `src/styles.css` `:root`. 60/30/10 distribution:

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--paper` #ffffff / `--wash` #f7f3eb | Page background, panel/modal surfaces |
| Secondary (30%) | `--soft` #f2f0ea, `--line` rgba(17,24,39,.11) | Cards, list rows, dividers, sidebar |
| Accent (10%) | `--green` #15825c / `--green-dark` #0f6648 | Primary actions only: Connect, Select this Page, Publish, Retry |
| Destructive | `--red` #c84b45 | Reconnect-required state, disconnect confirmation only |

Status semantics (reuse existing status-dot/badge colors):
- `Connected` → `--green` #15825c
- `Action needed` (missing permission) → `--coral` #d86f3d
- `Reconnect required` → `--red` #c84b45

Accent reserved for: Connect Facebook button, Select-this-Page button, Publish-to-Facebook button, Retry button. Never apply green to every interactive element (secondary actions like "Switch Page" use neutral/outline styling).

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Connect CTA | "Connect Facebook" |
| Connect helper | "Connect your official Facebook Page to publish approved posts." |
| Page picker heading | "Choose the Page to publish from" |
| Page picker body | "Select one of the Pages you manage. You can switch later." |
| Page picker primary CTA | "Use this Page" |
| Active Page label | "Publishing as: {Page name}" |
| Switch action | "Switch Page" |
| Health: connected | "Connected" |
| Health: missing permission | "Action needed — grant publishing permission" |
| Health: reconnect | "Reconnect required" |
| Capability gate (publish blocked) | "This Page can't publish yet — reconnect or grant the publishing permission first." |
| Media error: type | "Use a JPG, PNG, or GIF image for Facebook." |
| Media error: size | "Image is too large for Facebook (max 10 MB). Use a smaller file." |
| Media error: unreachable | "We can't reach this image URL. Make sure it's public, then try again." |
| Primary publish CTA | "Publish to Facebook" |
| Empty state heading (no Pages) | "No Facebook Pages found" |
| Empty state body | "This account doesn't manage any Pages. Connect an account that admins a Page, then try again." |
| Error state (publish failed) | "Facebook publish failed: {normalized reason}. Try the suggested action below." |
| Failure actions | "Reconnect" · "Retry" · "Get manual package" |
| Destructive confirmation (switch active Page) | "Switch publishing Page: New approved posts will publish from {new Page}. Continue?" |

Tone: plain, local-business-owner friendly; every error names the problem AND the next step.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| none (no shadcn / third-party component registry) | n/a | not required |

No external component registry is used. All UI is built from existing `src/styles.css` classes; no new runtime UI dependency is added (consistent with the project's no-new-heavy-deps tendency — the only new dependency in this phase is backend `cryptography`, not a UI library).

---

## Interaction Notes (non-token contract)

- **Owner control preserved:** Publish remains gated behind explicit approval (existing approval flow). The capability-health gate is an *additional* block, never a bypass.
- **No secrets in UI:** The UI only ever renders redacted token-boundary refs/fingerprints and Page metadata (name, id) — never tokens (enforced by backend serialization; UI must not request raw tokens).
- **Loading/disabled states:** Connect/Select/Publish/Retry buttons show a disabled+pending state during in-flight requests; reuse existing button busy styling.
- **Health badge placement:** badge sits next to the active Page name in the connected-accounts area and near the Publish action on the review surface, so the gate reason is visible at the point of action.

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS — every CTA is verb+noun; every error states problem + next step
- [x] Dimension 2 Visuals: PASS — reuses existing app-shell/card/badge/modal patterns; no ad-hoc components
- [x] Dimension 3 Color: PASS — 60/30/10 with green accent reserved to a named list; red/coral reserved for status/destructive
- [x] Dimension 4 Typography: PASS — 4 roles, reuses existing sans + Georgia display, no new sizes
- [x] Dimension 5 Spacing: PASS — all tokens multiples of 4, no exceptions
- [x] Dimension 6 Registry Safety: PASS — no third-party UI registry; no new UI dependency

**Approval:** approved 2026-06-23 (authored + self-verified inline against existing design system; researcher subagent path was unreliable in this session)
