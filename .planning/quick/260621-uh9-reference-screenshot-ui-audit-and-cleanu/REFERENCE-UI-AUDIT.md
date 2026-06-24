---
quick_id: 260621-uh9
status: complete
created: 2026-06-22
---

# Reference UI Audit

## Evidence

- Reference screenshots: `reference/*.png`
- Current viewport screenshots: `.planning/quick/260621-uh9-reference-screenshot-ui-audit-and-cleanu/screenshots/current-viewport/`
- Current full-page screenshots: `.planning/quick/260621-uh9-reference-screenshot-ui-audit-and-cleanu/screenshots/current/`
- Contact sheets:
  - `.planning/quick/260621-uh9-reference-screenshot-ui-audit-and-cleanu/screenshots/contact-sheets/reference-sheet.png`
  - `.planning/quick/260621-uh9-reference-screenshot-ui-audit-and-cleanu/screenshots/contact-sheets/current-sheet.png`
  - `.planning/quick/260621-uh9-reference-screenshot-ui-audit-and-cleanu/screenshots/contact-sheets/final3-sheet.png`
- Final viewport screenshots:
  - `.planning/quick/260621-uh9-reference-screenshot-ui-audit-and-cleanu/screenshots/final3-viewport/`

`Screenshot 2026-06-21 at 7.52.01 AM.png` is an invalid 8x86 fragment and should not drive layout decisions.

## Global Reference Architecture

### Shell

- Fixed left sidebar, light gray background.
- Sidebar width is approximately 260-280 CSS px on a 1728 px viewport.
- Main content starts immediately to the right of sidebar.
- No global top KPI strip.
- No persistent right-side summary rail.
- Main page background is white.
- Most module content sits directly on canvas with thin borders rather than inside nested dashboard cards.

### Sidebar

- Top logo block.
- Primary `Create New` button in bright pink.
- `Auto Posting` as blue outline button.
- Nav rows: Ad Inspirations, Content Library, Content Calendar, Brand & Social Accounts, Competitor Analysis, Analytics, Need help?
- Active nav is a white pill with subtle shadow/border.
- Trial card near bottom.
- Account footer at very bottom.

### Visual Tokens

- Background: `#f4f6fb` sidebar, `#ffffff` main surface.
- Primary action: pink/red for Create New.
- Secondary action/accent: blue for active tabs/buttons.
- Border: pale blue-gray, thin.
- Radius: medium, not blob-like.
- Typography: compact, SaaS-admin, not oversized marketing display.
- Cards: subtle 1 px border, minimal shadow.
- Density: high but calm; controls and content fit one viewport.

## Module Mapping

| Reference screenshot | Module | Visible structure |
|---|---|---|
| `7.47.43` | Ad Inspirations | Sidebar + title + Trending collection horizontal row + UGC Ads row + category tabs + card thumbnails |
| `7.47.57` | Content Library | Title + All/Image/Video/Carousel tabs + search/date/tags/users/source/archive filters + asset cards + Remove Watermark button |
| `7.48.07` | Content Calendar | Title + month nav + Today/Weekly/Monthly controls + large 7-column calendar grid + status legend + timezone selector |
| `7.48.14` | Brand & Social Accounts | Title + tabs + Social Platforms section + full-width connection rows |
| `7.48.47` | Facebook OAuth | Official external OAuth consent modal/page |
| `7.49.00` | Page picker | Compact modal with page cards and Save button |
| `7.49.19` | Analytics | Greeting/header + analytics tabs/date filter + posting streak + empty-state cards |
| `7.49.32` | Help | Floating support widget, not a full heavy dashboard |
| `7.50.03` | Inspirations detail | UGC Ads and Image Ads sections with horizontal media rows |
| `7.50.31` | Publish modal | Content Library dimmed backdrop + right drawer/modal with platform/post type rows |
| `7.50.51` | Schedule confirmation | Compact success/upsell modal after schedule |
| `7.51.16` | Scheduled detail drawer | Calendar dimmed backdrop + right scheduled-post drawer |
| `7.52.05` | Create New | Centered page title + 2-column by 3-row format cards |
| `7.55.52` | Create Image | Centered narrow setup list, four source method rows |
| `7.55.59` | Create UGC Video | Same narrow setup list pattern |
| `7.56.13` | Carousel config | Centered narrow form with style tabs and aspect ratio selector |
| `7.56.36` | Brand Details | Tabs + two-column form style with business fields |
| `7.56.51` | Brand Style | Tabs + typography/logo/color fields |
| `7.57.02` | Integrations | Tabs + horizontal integration cards/rows |
| `7.57.46` | Content cooking | Content Library grid with cooking overlay on a card |

## Current UI Mismatches

### Severity: Blocking

1. Global dashboard chrome overwhelms module content.
   - Every module starts with a big title and KPI strip before the actual work area.
   - Reference modules start directly with the module title and work surface.

2. Persistent right rail creates visual noise.
   - Package readiness / attention / approval queue appear on every screen.
   - Reference only shows contextual drawers/modals when needed.

3. Typography is too large and too heavy.
   - Current H1 sizes behave like a marketing landing page.
   - Reference uses compact admin-product headings.

4. Modules are vertically bloated.
   - Current Content Library full-page screenshot is over 11000 px tall.
   - Reference Content Library is a single calm workbench screen.

5. Calendar is not calendar-first.
   - Current Calendar first screen shows approval messaging and status cards.
   - Reference Calendar first screen is the calendar grid.

6. Brand & Social Accounts is not row/list-first.
   - Current screen uses hero + cards.
   - Reference uses tabs and full-width platform rows.

### Severity: High

1. Sidebar visual language does not match.
   - Current uses LocalPilot cards, navy Create New, green active states.
   - Reference uses light gray sidebar, pink Create New, blue active/outline states.

2. Decorative gradients make the app feel less like a SaaS workbench.
   - Reference is mostly neutral white/gray.

3. Repeated titles fragment attention.
   - Example: Create New has page title, panel title, and inner hero title.

4. Card shapes are too large and too rounded.
   - Reference cards are flatter, smaller, and more rectangular.

## Required Correction Strategy

The correct fix is not a cosmetic pass. The post-login workspace should be rebuilt around reference information architecture:

1. App shell owns sidebar only.
2. Each module owns one top title row.
3. Remove global metric strip and right rail from normal module pages.
4. Use modal/drawer only for contextual publish, schedule, and help states.
5. Make module components narrower and denser.
6. Preserve LocalPilot-specific content inside the reference layout skeleton.

## Implemented Result

- Rebuilt the post-login shell around the reference workbench pattern: fixed light-gray sidebar, pink Create New action, compact nav rows, white main canvas, and no global KPI/right rail on normal module pages.
- Reworked Create New into the same two-level flow as the references: initial six format cards, then narrow setup lists for Image/UGC and carousel configuration after a format is selected.
- Reworked Ad Inspirations into two horizontal media rows with six visual cards per section and category tabs.
- Reworked Content Library into tabs, filter controls, top-right Remove Watermark action, and vertical media cards using LocalPilot-owned assets instead of generic gradients.
- Reworked Content Calendar into a month grid with month navigation, weekday header, status legend, timezone control, and a contextual scheduled-post drawer.
- Reworked Brand & Social Accounts into tabbed rows matching the social-platform list pattern.
- Reworked Help into a compact support drawer surface instead of a heavy dashboard.

The final implementation intentionally does not copy Predis trademarks, exact competitor artwork, or external OAuth UI chrome. LocalPilot uses its own brand, local-business assets, and official-account safety boundaries.
