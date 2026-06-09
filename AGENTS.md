<!-- GSD:project-start source:PROJECT.md -->

## Project

**LocalPilot AI**

LocalPilot AI is an AI marketing operator for local small businesses that turns one promotion, service, product, or content idea into platform-native social posts. The next stage focuses on making publishing real: business owners connect their official accounts, generate Facebook and TikTok posts, review the output, and publish from one workflow.

The product is not trying to become a generic scheduler. Its wedge is local-business growth: strategy-aware content, platform-specific copy, owner approval, and eventually a feedback loop from posts to calls, bookings, DMs, coupons, and walk-ins.

**Core Value:** A local business owner can go from one marketing idea to approved, platform-native Facebook and TikTok posts published through their own official accounts with minimal effort.

### Constraints

- **Tech stack**: Current app is React/Vite with JavaScript and CSS in `src/main.jsx` and `src/styles.css` - near-term work must either extend this carefully or introduce a backend boundary deliberately.
- **Existing architecture**: The app is frontend-only and stores demo state in localStorage - real publishing requires server-side persistence, token handling, or a self-hosted publishing engine boundary.
- **Security**: OAuth secrets, refresh tokens, API keys, and merchant account credentials must never live in browser localStorage or committed files.
- **Platform priority**: Facebook is first, TikTok second, Xiaohongshu third/deferred - roadmap and requirements should reflect this ordering.
- **Integration reuse**: Evaluate CLI/MCP/self-hosted publishing tools before writing custom platform-specific request code.
- **Compliance**: Use official API paths for Facebook and TikTok; do not rely on scraping, browser automation, or cookie posting for production publishing.
- **Sales readiness**: The output must support local field sales: a merchant should understand the value quickly and see a credible path from offer to published post.
- **Owner control**: Publishing must require explicit user approval before posts are sent.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- JavaScript / JSX - React application code in `src/main.jsx`, styling imports through `src/styles.css`, and browser APIs such as `window.localStorage`, `FormData`, `MutationObserver`, and `URLSearchParams`.
- CSS - Responsive visual system and layout rules in `src/styles.css`.
- HTML - Vite document shell in `index.html`.
- Node.js ES modules - Build and packaging helpers in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.
- JSON - Package metadata in `package.json`, dependency lock in `package-lock.json`, and Sites hosting metadata in `.openai/hosting.json`.

## Runtime

- Browser runtime for the application UI. `index.html` loads `/src/main.jsx`, which mounts React into `#root` with `createRoot(document.getElementById("root")).render(<App />)`.
- Node.js for development/build scripts. Vite 7.3.5 and `@vitejs/plugin-react` 5.2.0 require Node `^20.19.0 || >=22.12.0` according to `package-lock.json`; `react-router-dom` 7.17.0 requires Node `>=20.0.0`.
- Cloudflare Worker-compatible static asset runtime for packaged deployment. `scripts/prepare-sites-dist.mjs` writes `dist/server/index.js`, whose generated worker uses `env.ASSETS.fetch(request)` and falls back HTML requests to `/index.html`.
- npm - scripts and lockfile use npm conventions in `package.json` and `package-lock.json`.
- Lockfile: present at `package-lock.json` with lockfileVersion 3.

## Frameworks

- React `^19.2.1` requested in `package.json`; locked to 19.2.7 in `package-lock.json`. Used for all UI components, context, effects, memoized state, and rendering in `src/main.jsx`.
- React DOM `^19.2.1` requested in `package.json`; locked to 19.2.7 in `package-lock.json`. Used through `createRoot` in `src/main.jsx`.
- React Router DOM `^7.10.1` requested in `package.json`; locked to 7.17.0 in `package-lock.json`. Used for `BrowserRouter`, `Routes`, `Route`, `Navigate`, `Link`, `useLocation`, and `useNavigate` in `src/main.jsx`.
- Not detected. `package.json` defines no `test` script and there are no test framework dependencies in `package.json`.
- Vite `^7.2.7` requested in `package.json`; locked to 7.3.5 in `package-lock.json`. `npm run dev` runs `vite --host 127.0.0.1`; `npm run build` runs `vite build --outDir dist/client --emptyOutDir true`.
- `@vitejs/plugin-react` `^5.1.1` requested in `package.json`; locked to 5.2.0 in `package-lock.json`. Installed as the React transform plugin, with no explicit `vite.config.*` file detected.
- Node built-ins are used by packaging scripts: `node:fs/promises`, `node:path`, `node:url`, and `node:child_process` in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.
- System `tar` is invoked by `scripts/package-sites.mjs` via `spawn("tar", ["-C", root, "-czf", archivePath, "dist"])`.

## Key Dependencies

- `react` - Component framework for landing page, fake login, app demo, translation layer, and stateful workflows in `src/main.jsx`.
- `react-dom` - Browser rendering entrypoint in `src/main.jsx`.
- `react-router-dom` - Client-side routing for `/`, `/app`, module query links, and fallback navigation in `src/main.jsx`.
- `vite` - Development server and production bundler configured through `package.json` scripts.
- `@vitejs/plugin-react` - React refresh and JSX/Babel integration for Vite, present in `package.json` and `package-lock.json`.
- `node:fs/promises` - Creates deployment output, writes generated worker code, and validates packaged artifacts in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.
- `node:child_process` - Runs `tar` to create the Sites archive in `scripts/package-sites.mjs`.

## Configuration

- No `.env` or `.env.*` files detected in the repository scan.
- `SITES_ARCHIVE_PATH` is the only detected environment variable. `scripts/package-sites.mjs` reads `process.env.SITES_ARCHIVE_PATH` and defaults to `/tmp/localpilot-ai-karen-demo-sites.tar.gz`.
- Browser-local persistence uses fixed `localStorage` keys in `src/main.jsx`, including `localpilot-language`, `localpilot-demo-session`, `localpilot-demo-input`, `localpilot-demo-plans`, `localpilot-pilot-request`, and `localpilot-export-package`.
- `package.json` owns all runnable scripts:
- `index.html` is the Vite HTML entry and sets the page title, description, favicon, root container, and module script.
- `.openai/hosting.json` configures OpenAI/Sites storage bindings with `"d1": null` and `"r2": null`.
- No `vite.config.*`, `tsconfig.json`, ESLint config, Prettier config, or test config files were detected.

## Platform Requirements

- Node.js `^20.19.0 || >=22.12.0` is required by Vite and `@vitejs/plugin-react`; Node `>=20.0.0` is required by React Router packages in `package-lock.json`.
- npm install uses `package-lock.json`.
- Local preview instructions in `README.md` use `npm install` and `npm run dev -- --port 4173`, then browse `http://127.0.0.1:4173/`.
- Frontend-only static deployment with a generated Cloudflare Worker-compatible Sites wrapper.
- `npm run build` prepares `dist/client/**`, `dist/server/index.js`, and `dist/.openai/hosting.json`.
- `npm run package:sites` writes a deployable archive to `SITES_ARCHIVE_PATH` or `/tmp/localpilot-ai-karen-demo-sites.tar.gz`.
- `README.md` states remote Sites deployment is blocked until Sites is enabled for the workspace.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- Use short lowercase source filenames for the current app surface: `src/main.jsx`, `src/styles.css`, `index.html`.
- Use kebab-case for Node utility scripts: `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs`.
- Use kebab-case for generated/static image assets: `assets/cafe-owner.png`, `assets/restaurant.png`, `assets/salon.png`.
- Keep documentation filenames descriptive and snake_case or kebab-case under `docs/`, such as `docs/design-qa.md` and `docs/landing_page_content_and_design_brief.md`.
- Use PascalCase for React components and hooks providers: `LanguageProvider`, `TranslationLayer`, `LanguageToggle`, `LandingPage`, `Modal`, `AppDemo`, `App` in `src/main.jsx`.
- Use `use` prefix for React hooks: `useLanguage` in `src/main.jsx`.
- Use camelCase for helper functions: `translateDynamicText`, `normalizeTextKey`, `translateSubtree`, `moduleSlug`, `moduleFromSlug`, `normalizeCampaignInput`, `buildPlansFromInput`, `loadStoredPlans`, `clampIndex` in `src/main.jsx`.
- Use action-oriented camelCase for event handlers inside components: `submitPilot`, `submitLogin`, `showToast`, `showAppToast`, `logout`, `selectModule`, `applyWalkthroughStep`, `resetDemo`, `updatePlan`, `approvePlan`, `requestChanges`, `toggleChecklist`, `regeneratePlan`, `exportPackage`, `applyBusinessType` in `src/main.jsx`.
- Use camelCase for local state and derived values: `menuOpen`, `pilotOpen`, `loginOpen`, `appToast`, `safeSelectedChannel`, `pendingPlans`, `approvedCount`, `checklistPercent`, `packageReadiness` in `src/main.jsx`.
- Use uppercase snake case for true constants: `LANGUAGE_STORAGE_KEY` in `src/main.jsx`.
- Use plural nouns for collection data: `platforms`, `modules`, `moduleWorkflows`, `schedule`, `aiStudioTasks`, `inboxThreads`, `localRoiSignals`, `pricingPlans`, `businessOptions`, `channelPlans` in `src/main.jsx`.
- Use `root`, `dist`, `serverDir`, `openAiDir`, `archivePath`, and `requiredFiles` for filesystem script paths in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.
- Not applicable. The codebase uses JavaScript/JSX rather than TypeScript, with no `.ts` or `.tsx` files detected.
- Data shapes are expressed as plain object literals in `src/main.jsx`, such as `defaultCampaignInput`, `businessTemplates`, `moduleDetails`, and `channelPlans`.

## Code Style

- No formatter configuration is present. No `.prettierrc`, `eslint.config.*`, `biome.json`, `tsconfig.json`, or `jsconfig.json` was detected at the repository root.
- Follow the existing style in `src/main.jsx`: two-space indentation, double quotes, semicolons, trailing commas in multiline arrays/objects/calls, and parenthesized multiline JSX returns.
- Keep JSX props on separate lines when elements have several attributes, as shown by `LanguageToggle`, `LandingPage`, and `AppDemo` in `src/main.jsx`.
- Keep CSS custom properties in `:root` and reuse them throughout `src/styles.css`: `--ink`, `--muted`, `--soft`, `--line`, `--green`, `--green-dark`, `--coral`, `--blue`, `--red`, `--paper`, `--wash`, `--shadow`.
- No linting tool is configured in `package.json`.
- No lint script is available. Current scripts are `dev`, `build`, `package:sites`, and `preview` in `package.json`.
- Preserve React hook rules manually: call hooks only at component/hook top level in `src/main.jsx`, as done by `LanguageProvider`, `TranslationLayer`, `LandingPage`, and `AppDemo`.

## Import Organization

- No path aliases are configured. Use relative imports from the file location.
- Use package imports for dependencies: `react`, `react-dom/client`, `react-router-dom`.
- Use `node:` protocol imports for built-in modules in scripts: `node:fs/promises`, `node:path`, `node:url`, `node:child_process` in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.

## Error Handling

- Use guarded `try`/`catch` for browser persistence reads and writes where failure should not break the demo: `LanguageProvider`, `loadStoredPlans`, `loadStoredInput`, `loadStoredIndex`, `loadStoredModule`, and session parsing in `AppDemo` in `src/main.jsx`.
- Return safe defaults from persistence helpers when stored data is missing or invalid: `createInitialPlans(input)`, `normalizeCampaignInput(defaultCampaignInput)`, numeric fallback indexes, and `"Home"` in `src/main.jsx`.
- Throw explicit programmer errors for invalid hook usage: `useLanguage` throws `new Error("useLanguage must be used inside LanguageProvider")` in `src/main.jsx`.
- In Node scripts, allow top-level `await` failures to fail the command, and throw explicit validation errors after external work: `scripts/package-sites.mjs` throws if the archive is empty.
- For child processes, reject on non-zero exit codes with a clear message: `scripts/package-sites.mjs` rejects with `new Error(\`tar exited with code ${code}\`)`.

## Logging

- Use `console.log` only for successful CLI/script status messages, as in `scripts/package-sites.mjs`.
- The React app communicates user-visible status through toast state instead of console logging: `showToast` in `LandingPage` and `showAppToast` in `AppDemo` in `src/main.jsx`.
- No structured logging framework is configured.

## Comments

- Comments are sparse. Add comments only for behavior that is not obvious from names or control flow.
- Existing comment style explains intentional degradation, such as the localStorage write fallback in `LanguageProvider` in `src/main.jsx`.
- Not used. No JSDoc or TSDoc blocks were detected in `src/main.jsx` or `scripts/*.mjs`.
- Prefer self-describing helper and handler names over adding documentation comments for small functions.

## Function Design

## Module Design

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| HTML shell | Defines metadata, favicon, `#root`, and Vite module entry. | `index.html` |
| React bootstrap | Imports React, router, CSS, image assets, and mounts `<App />` into `#root`. | `src/main.jsx` |
| `App` | Composes language provider, translation observer, and React Router routes. | `src/main.jsx` |
| `LandingPage` | Owns public marketing page, pricing, pilot request modal, login modal, and marketing form persistence. | `src/main.jsx` |
| `AppDemo` | Owns authenticated demo shell, module navigation, generated campaign state, approval state, local package export, and demo toasts. | `src/main.jsx` |
| Translation utilities | Translate static/dynamic text nodes, attributes, and campaign input values after React renders. | `src/main.jsx` |
| Demo data builders | Normalize campaign input and derive per-channel plans from business templates. | `src/main.jsx` |
| Global styles | Provides reset, tokens, marketing layout, app layout, modal, responsive rules, and component classes. | `src/styles.css` |
| Build preparation script | Generates `dist/server/index.js`, copies `.openai/hosting.json`, and removes root-level built assets duplicated outside `dist/client`. | `scripts/prepare-sites-dist.mjs` |
| Sites packaging script | Verifies required dist files and archives `dist/` for deployment. | `scripts/package-sites.mjs` |

## Pattern Overview

- Use `src/main.jsx` as the application composition root, fixture store, route tree, component tree, and local interaction model.
- Use `react-router-dom` for two public routes: `/` for the marketing site and `/app` for the demo workspace.
- Use browser `localStorage` as the only mutable persistence layer for language, pilot requests, demo session, selected module, generated plans, checklist state, and exported package.
- Use `src/styles.css` as a global stylesheet keyed by semantic class names; there is no CSS module, component-scoped CSS, or design-token build step.
- Build with Vite into `dist/client/`, then generate a minimal fetch worker under `dist/server/index.js` for static asset hosting and SPA fallback.

## Layers

- Purpose: Host the client bundle and provide document metadata.
- Location: `index.html`
- Contains: `#root`, SEO description, inline SVG favicon, module script to `/src/main.jsx`.
- Depends on: Vite resolving `/src/main.jsx`.
- Used by: Vite dev server and Vite production build.
- Purpose: Render the marketing page, app demo, modals, route switch, and browser interactions.
- Location: `src/main.jsx`
- Contains: `App`, `LandingPage`, `AppDemo`, `Modal`, `Brand`, `LanguageToggle`, hooks, event handlers, and JSX.
- Depends on: `react`, `react-dom/client`, `react-router-dom`, `src/styles.css`, and images in `assets/`.
- Used by: Browser runtime through `createRoot(document.getElementById("root")).render(<App />)`.
- Purpose: Provide English/Chinese toggling without threading translation calls through every JSX node.
- Location: `src/main.jsx`
- Contains: `zhTranslations`, phrase replacements, `LanguageContext`, `LanguageProvider`, `TranslationLayer`, `translateSubtree`, and DOM mutation observer logic.
- Depends on: Browser DOM APIs (`document`, `NodeFilter`, `MutationObserver`), React context/effects, and `localStorage`.
- Used by: `App` and `LanguageToggle`.
- Purpose: Hold all demo product data and generate normalized campaign plans for the app workspace.
- Location: `src/main.jsx`
- Contains: arrays/objects such as `platforms`, `modules`, `moduleDetails`, `moduleWorkflows`, `businessTemplates`, `channelPlans`, `inboxThreads`, `localRoiSignals`, and helper functions.
- Depends on: imported images from `assets/`.
- Used by: `LandingPage` previews and `AppDemo` module views.
- Purpose: Preserve prototype state in the browser across refreshes.
- Location: `src/main.jsx`
- Contains: `loadStoredPlans`, `loadStoredInput`, `loadStoredIndex`, `loadStoredModule`, and `useEffect` persistence calls.
- Depends on: `window.localStorage`.
- Used by: `LandingPage`, `LanguageProvider`, and `AppDemo`.
- Purpose: Define visual system, responsive page layout, app shell, cards, forms, modals, toasts, and module-specific surfaces.
- Location: `src/styles.css`
- Contains: CSS custom properties, global reset, marketing sections, app shell, panels, responsive `@media` blocks.
- Depends on: class names emitted by `src/main.jsx`.
- Used by: All rendered UI.
- Purpose: Convert Vite output into deployable static client + server worker package.
- Location: `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs`, `.openai/hosting.json`
- Contains: generated worker source with asset fetch and HTML fallback, dist validation, tar archive creation.
- Depends on: Node built-ins and output from `vite build --outDir dist/client`.
- Used by: `npm run build` and `npm run package:sites`.

## Data Flow

### Primary Request Path

### Marketing-to-Demo Flow

### App Demo Campaign Flow

### Translation Flow

### Build and Deployment Flow

- React local component state owns UI state inside `LandingPage` and `AppDemo`.
- Browser `localStorage` owns persistence; all stored values use `localpilot-*` keys in `src/main.jsx`.
- There is no backend state, database, server API, global state library, or external auth provider.

## Key Abstractions

- Purpose: Keep visible UI translatable while preserving the prototype's existing JSX copy.
- Examples: `LanguageProvider`, `TranslationLayer`, `translateDynamicText`, `translateSubtree` in `src/main.jsx`.
- Pattern: React context plus imperative DOM post-processing.
- Purpose: Drive the demo sidebar, active module, and module-specific views from a fixed list.
- Examples: `modules`, `moduleSlug`, `moduleFromSlug`, `moduleDetails`, `moduleWorkflows` in `src/main.jsx`.
- Pattern: Static registry plus URL/localStorage-selected state.
- Purpose: Provide industry-specific default campaign input and channel copy.
- Examples: `defaultCampaignInput`, `businessTemplates`, `businessOptions` in `src/main.jsx`.
- Pattern: Fixture dictionary keyed by business type.
- Purpose: Provide canonical cross-platform plan structure for TikTok, Instagram, Facebook, Xiaohongshu, and Google Local.
- Examples: `channelPlans`, `buildPlansFromInput`, `createInitialPlans`, `normalizePlan` in `src/main.jsx`.
- Pattern: Base plan templates transformed by selected business context.
- Purpose: Simulate login and workspace persistence without a backend.
- Examples: `localpilot-demo-session`, `localpilot-demo-input`, `localpilot-demo-plans`, `localpilot-export-package` keys in `src/main.jsx`.
- Pattern: `localStorage`-backed session and state snapshots.
- Purpose: Serve the static client bundle and support client-side routing on deployment.
- Examples: `workerSource` in `scripts/prepare-sites-dist.mjs`, generated output `dist/server/index.js`.
- Pattern: Static asset fetch with 404 HTML fallback.

## Entry Points

- Location: `package.json`
- Triggers: `npm run dev`
- Responsibilities: Starts Vite on `127.0.0.1` and serves `index.html` plus `src/main.jsx`.
- Location: `package.json`
- Triggers: `npm run build`
- Responsibilities: Builds client assets into `dist/client/` and prepares deployment worker/config.
- Location: `package.json`, `scripts/package-sites.mjs`
- Triggers: `npm run package:sites`
- Responsibilities: Builds the app, verifies deployment files, and creates a tar archive.
- Location: `index.html`
- Triggers: Browser document load.
- Responsibilities: Provides root node and loads `/src/main.jsx`.
- Location: `src/main.jsx`
- Triggers: Module evaluation in the browser.
- Responsibilities: Mounts React and configures routes.
- Location: `src/main.jsx`
- Triggers: Browser path `/`.
- Responsibilities: Renders `LandingPage`.
- Location: `src/main.jsx`
- Triggers: Browser path `/app`.
- Responsibilities: Renders `AppDemo`.
- Location: `src/main.jsx`
- Triggers: Any unmatched browser route.
- Responsibilities: Redirects to `/`.

## Architectural Constraints

- **Threading:** Single-threaded browser React event loop. Packaging scripts run as single Node processes and spawn `tar` only in `scripts/package-sites.mjs`.
- **Global state:** Module-level fixture objects and arrays in `src/main.jsx` are shared by all components. Browser-persisted mutable state is scoped through `localStorage` keys in `src/main.jsx`.
- **Circular imports:** Not detected. The app has one source JS module (`src/main.jsx`) importing CSS and images; scripts do not import app source.
- **Backend boundary:** There is no backend API. Do not add server calls without introducing a clear API layer and deployment plan.
- **Routing boundary:** Use `react-router-dom` route definitions inside `App` in `src/main.jsx`; the deployment worker supports SPA fallback for HTML requests.
- **Persistence boundary:** Use `localStorage` only for demo persistence unless a backend/data layer is intentionally added.
- **Generated output:** Treat `dist/` as build output. Source changes belong in `src/`, `assets/`, `public/`, `.openai/`, or `scripts/`, not manually in `dist/`.

## Anti-Patterns

### Editing Generated Deployment Output

### Adding New Demo Views Outside the Module Registry

### Bypassing Plan Normalization

### Translating JSX Inline While TranslationLayer Is Active

## Error Handling

- Wrap `localStorage` reads and JSON parsing in `try/catch`, falling back to default values in `LanguageProvider`, `loadStoredPlans`, `loadStoredInput`, `loadStoredIndex`, and `loadStoredModule`.
- Use `useLanguage` to throw if the hook is consumed outside `LanguageProvider`.
- Packaging scripts rely on promise rejection from `access`, `copyFile`, `tar` exit status, and archive size checks.
- Generated worker returns HTTP 500 when `env.ASSETS` is missing and otherwise returns original 404 responses for non-HTML missing assets.

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
