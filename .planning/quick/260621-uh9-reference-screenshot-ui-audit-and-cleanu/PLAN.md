---
quick_id: 260621-uh9
slug: reference-screenshot-ui-audit-and-cleanu
status: complete
created: 2026-06-22T01:56:43Z
---

# Quick Plan: Reference Screenshot UI Audit And Cleanup

## Goal

Make the post-login LocalPilot workspace closely follow the information architecture, density, layout, and visual hierarchy visible in the `reference/` screenshots, while preserving LocalPilot-specific safety constraints: official OAuth boundaries, owner approval, and no token exposure.

## Problem

The current UI contains the right rough modules but presents them as a cluttered dashboard:

- global KPI cards appear above every module;
- a right-side package-readiness rail appears on every module;
- each module has multiple nested heroes and repeated titles;
- many screens require scrolling before the actual module content appears;
- page backgrounds, oversized typography, and cards compete for attention;
- calendar, brand accounts, and content library do not visually match the reference's restrained SaaS workbench.

## Reference Target

Use the reference screenshots as the source of truth:

- fixed light-gray left sidebar, about 260 px wide;
- primary pink Create New button;
- Auto Posting blue outlined button;
- nav rows with icon + label + active white pill;
- main content is mostly white, not decorative gradient;
- each module has one title area and one working surface;
- no global KPI strip on normal module screens;
- no persistent right-side readiness rail;
- thin borders, subtle shadows, compact controls;
- single-screen workbench where possible.

## Implementation Slices

1. Capture evidence - complete
   - Reference contact sheet.
   - Current viewport screenshots.
   - Current full-page screenshots to detect vertical bloat.

2. Write UI audit - complete
   - Map each reference screenshot to module purpose and visible UI.
   - List mismatch categories and required corrections.

3. Refactor app shell - complete
   - Replace current demo dashboard shell with Predis-like app shell.
   - Remove global KPI strip and persistent right rail from module screens.
   - Normalize sidebar, nav, trial card, and account footer.

4. Refactor key modules - complete
   - Create New: centered title + six format cards.
   - Ad Inspirations: compact sections with category chips and horizontal card rows.
   - Content Library: title + tabs + filter row + asset grid.
   - Content Calendar: toolbar + monthly/weekly grid as primary content.
   - Brand & Social Accounts: tabs + full-width platform rows/forms.
   - Analytics: posting streak and empty-state cards, no hero clutter.
   - Need help: compact drawer/widget layout.

5. Verify visually - complete
   - Capture after screenshots at 1728x900 CSS viewport, 2x scale.
   - Compare with reference contact sheet.
   - Run syntax and focused tests where available.

## Constraints

- Do not copy Predis trademarks or exact template art.
- Do not add token/client secret storage.
- Do not imply autonomous publishing without owner approval.
- Keep existing backend APIs working.
- Avoid large backend changes for this UI cleanup unless unavoidable.
