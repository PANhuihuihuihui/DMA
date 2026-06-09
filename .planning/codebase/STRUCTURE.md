---
last_mapped_commit: 64e01e3dfea3229b13fc4d25ac8c657efe12dab9
---
# Codebase Structure

**Analysis Date:** 2026-06-09

## Directory Layout

```text
DMA/
├── .openai/              # Deployment hosting configuration copied into dist
├── .planning/            # GSD planning and generated codebase maps
├── assets/               # Source image assets imported by React
├── dist/                 # Generated build output for client/server hosting
├── docs/                 # Product, design, market, QA, and planning documents
├── public/               # Static public files copied by Vite
├── scripts/              # Node packaging and deployment preparation scripts
├── src/                  # React SPA source and global CSS
├── index.html            # Vite HTML entry
├── package.json          # NPM scripts and runtime dependencies
├── package-lock.json     # Locked dependency graph
├── README.md             # Project usage/readme
└── .gitignore            # Ignored files
```

## Directory Purposes

**`.openai/`:**
- Purpose: Deployment metadata for OpenAI/Sites-style hosting.
- Contains: `hosting.json`.
- Key files: `.openai/hosting.json`.

**`.planning/`:**
- Purpose: GSD planning artifacts and generated codebase maps.
- Contains: `codebase/` documents.
- Key files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`.

**`assets/`:**
- Purpose: Source raster images imported from React.
- Contains: Business/industry visuals used by the marketing page and app demo.
- Key files: `assets/cafe-owner.png`, `assets/restaurant.png`, `assets/salon.png`, `assets/clinic.png`, `assets/shop.png`.

**`dist/`:**
- Purpose: Generated deployment output.
- Contains: Built client app, generated server worker, copied hosting config.
- Key files: `dist/client/index.html`, `dist/server/index.js`, `dist/.openai/hosting.json`.
- Guidance: Do not manually edit files under `dist/`; regenerate with `npm run build`.

**`docs/`:**
- Purpose: Product planning, design QA, market research, and visual option artifacts.
- Contains: Markdown documents and exported design images.
- Key files: `docs/design-qa.md`, `docs/landing_page_content_and_design_brief.md`, `docs/karen_demo_redesign_plan.md`, `docs/feature_gap_priority_review.md`.

**`public/`:**
- Purpose: Vite public assets copied directly to the client build.
- Contains: Static screenshot.
- Key files: `public/screenshot.jpeg`.

**`scripts/`:**
- Purpose: Build post-processing and deployment archive creation.
- Contains: ES module Node scripts using built-in Node APIs.
- Key files: `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs`.

**`src/`:**
- Purpose: Application source.
- Contains: A single React JSX module and one global stylesheet.
- Key files: `src/main.jsx`, `src/styles.css`.

## Key File Locations

**Entry Points:**
- `index.html`: Browser/Vite HTML entry and root DOM node.
- `src/main.jsx`: React application bootstrap, route tree, all app components, demo data, translation utilities, and state helpers.
- `package.json`: Script entry points for `dev`, `build`, `package:sites`, and `preview`.

**Configuration:**
- `package.json`: Package metadata, `"type": "module"`, NPM scripts, and dependencies.
- `package-lock.json`: Dependency lockfile.
- `.openai/hosting.json`: Hosting config copied to `dist/.openai/hosting.json`.
- `.gitignore`: Git ignore rules.

**Core Logic:**
- `src/main.jsx`: `LanguageProvider`, `TranslationLayer`, `LandingPage`, `AppDemo`, routing, localStorage persistence, and campaign plan generation.
- `src/styles.css`: Design tokens, layout, responsive behavior, marketing page styles, app shell styles, modals, forms, and toasts.

**Build and Packaging:**
- `scripts/prepare-sites-dist.mjs`: Post-build generation of `dist/server/index.js` and hosting config copy.
- `scripts/package-sites.mjs`: Dist validation and tarball packaging.
- `dist/client/`: Generated Vite client output.
- `dist/server/index.js`: Generated static asset worker with SPA fallback.

**Static Assets:**
- `assets/`: Images imported into the JavaScript bundle by `src/main.jsx`.
- `public/screenshot.jpeg`: Static public file copied to Vite build output.
- `docs/*.png`: Documentation/design reference images, not imported by the app.

**Documentation:**
- `README.md`: User-facing project instructions.
- `docs/*.md`: Supporting product/design/market analysis.
- `.planning/codebase/*.md`: Generated GSD codebase maps.

## Naming Conventions

**Files:**
- React app source uses concise lowercase names: `src/main.jsx`.
- Global stylesheet uses lowercase CSS filename: `src/styles.css`.
- Node build scripts use kebab-case with `.mjs`: `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs`.
- Documentation uses a mix of kebab-case and snake_case Markdown names under `docs/`, such as `docs/design-qa.md` and `docs/landing_page_content_and_design_brief.md`.
- Image assets use kebab-case descriptive names in `assets/`, such as `assets/cafe-owner.png`.

**Directories:**
- Source and operational directories use short lowercase names: `src/`, `assets/`, `public/`, `scripts/`, `docs/`, `dist/`.
- Hidden tool/config directories use dot-prefix names: `.openai/`, `.planning/`.

**React Symbols:**
- Components use PascalCase: `App`, `LandingPage`, `AppDemo`, `Modal`, `Brand`, `LanguageToggle`, `TranslationLayer`.
- Hooks use `use` prefix and camelCase: `useLanguage`.
- Helper functions use camelCase: `moduleSlug`, `moduleFromSlug`, `normalizeCampaignInput`, `buildPlansFromInput`, `loadStoredPlans`.
- Constants use camelCase for data registries: `businessTemplates`, `channelPlans`, `pricingPlans`, `localRoiSignals`.
- Storage key constants use SCREAMING_SNAKE_CASE when defined separately: `LANGUAGE_STORAGE_KEY`.

**CSS:**
- Class names use kebab-case: `.site-header`, `.hero-copy`, `.workspace-card`, `.app-shell`, `.primary-panel`, `.insight-card`.
- CSS custom properties are defined in `:root` with semantic names: `--ink`, `--muted`, `--green`, `--coral`, `--blue`, `--paper`.
- State classes use simple semantic modifiers: `.active`, `.popular`, `.done`, `.soft`, `.blue`.

## Where to Add New Code

**New Marketing Page Section:**
- Primary code: Add JSX inside `LandingPage` in `src/main.jsx`.
- Styles: Add section and component classes to `src/styles.css`.
- Assets: Put imported images in `assets/` and import them at the top of `src/main.jsx`.

**New App Demo Module:**
- Primary code: Add the module name to `modules` in `src/main.jsx`.
- Configuration: Add module metadata to `moduleDetails` in `src/main.jsx`.
- Workflow copy: Add or extend `moduleWorkflows` in `src/main.jsx` when the default module branch is used.
- Rendering: Add a `config.view` branch inside `AppDemo` in `src/main.jsx` only when the module needs a custom layout.
- Styles: Add classes to `src/styles.css`.

**New Campaign Business Type:**
- Primary code: Add a key to `businessTemplates` in `src/main.jsx`.
- Required fields: Include `label`, `business`, `offer`, `goal`, `audience`, `kpis`, and `byChannel` entries for `TikTok`, `Instagram`, `Facebook`, `Xiaohongshu`, and `Google Local`.
- Selection UI: `businessOptions` is generated from `businessTemplates`, so no separate dropdown list is required.

**New Channel Plan:**
- Primary code: Add an object to `channelPlans` in `src/main.jsx`.
- Required related updates: Add matching `byChannel` entries to each `businessTemplates` item and update UI assumptions where the app mentions current channels.
- Styles/assets: Add an imported image in `assets/` if the channel needs a unique visual.

**New Translation Copy:**
- Static text: Add English-to-Chinese entries to `zhTranslations` in `src/main.jsx`.
- Dynamic text: Add focused replacements in `translateDynamicText` in `src/main.jsx`.
- Opt-out: Add `data-no-translate` to JSX elements whose text or values must not be mutated by the translation observer.

**New Persistence Field:**
- Storage helpers: Follow existing `localpilot-*` key naming in `src/main.jsx`.
- Initialization: Read with `try/catch` and fallback defaults.
- Persistence: Write from a `useEffect` tied to the specific React state value.

**New Build/Deploy Behavior:**
- Build scripts: Put Node post-processing in `scripts/prepare-sites-dist.mjs` or a new `.mjs` script under `scripts/`.
- Package verification: Extend `requiredFiles` in `scripts/package-sites.mjs` when new deployment-critical files must exist.
- Hosting config: Update `.openai/hosting.json`, then allow the prepare script to copy it into `dist/.openai/hosting.json`.

**Utilities:**
- Shared UI/data helpers currently live in `src/main.jsx` near the data they support.
- If helper count grows, split by responsibility under `src/` and import from `src/main.jsx`; preserve the existing React entry point.

## Special Directories

**`dist/`:**
- Purpose: Generated deployment artifact.
- Generated: Yes.
- Committed: Present in the working tree.
- Guidance: Regenerate from source with `npm run build`; do not use as source of truth.

**`node_modules/`:**
- Purpose: Installed dependencies.
- Generated: Yes.
- Committed: No source role.
- Guidance: Do not inspect or edit for application changes.

**`.planning/`:**
- Purpose: Planning and codebase intelligence artifacts.
- Generated: Yes.
- Committed: Project-dependent.
- Guidance: Only GSD mapping/planning commands should update generated files here.

**`.openai/`:**
- Purpose: Hosting metadata used by deployment preparation.
- Generated: No.
- Committed: Yes.
- Guidance: Edit source config here, not the copied file in `dist/.openai/`.

**`docs/`:**
- Purpose: Human-authored product and design context.
- Generated: Mixed; includes Markdown docs and exported images.
- Committed: Yes.
- Guidance: Use as product/design reference; app runtime does not import these files.

---

*Structure analysis: 2026-06-09*
