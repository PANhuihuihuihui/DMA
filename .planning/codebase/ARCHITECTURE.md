---
last_mapped_commit: 64e01e3dfea3229b13fc4d25ac8c657efe12dab9
---
<!-- refreshed: 2026-06-09 -->
# Architecture

**Analysis Date:** 2026-06-09

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    Browser React SPA                         │
├──────────────────┬──────────────────┬───────────────────────┤
│  Marketing Site  │    App Demo      │    i18n Layer         │
│ `src/main.jsx`   │ `src/main.jsx`   │ `src/main.jsx`        │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Module-level Demo Data and Pure Builders          │
│            `src/main.jsx`                                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Browser localStorage + Static Vite Assets + Sites Worker     │
│ `index.html`, `dist/client/`, `dist/server/index.js`         │
└─────────────────────────────────────────────────────────────┘
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

**Overall:** Single-file React SPA prototype with module-level fixtures, client-side routing, browser-local persistence, and generated static deployment wrapper.

**Key Characteristics:**
- Use `src/main.jsx` as the application composition root, fixture store, route tree, component tree, and local interaction model.
- Use `react-router-dom` for two public routes: `/` for the marketing site and `/app` for the demo workspace.
- Use browser `localStorage` as the only mutable persistence layer for language, pilot requests, demo session, selected module, generated plans, checklist state, and exported package.
- Use `src/styles.css` as a global stylesheet keyed by semantic class names; there is no CSS module, component-scoped CSS, or design-token build step.
- Build with Vite into `dist/client/`, then generate a minimal fetch worker under `dist/server/index.js` for static asset hosting and SPA fallback.

## Layers

**HTML and Bundler Entry:**
- Purpose: Host the client bundle and provide document metadata.
- Location: `index.html`
- Contains: `#root`, SEO description, inline SVG favicon, module script to `/src/main.jsx`.
- Depends on: Vite resolving `/src/main.jsx`.
- Used by: Vite dev server and Vite production build.

**React Application Layer:**
- Purpose: Render the marketing page, app demo, modals, route switch, and browser interactions.
- Location: `src/main.jsx`
- Contains: `App`, `LandingPage`, `AppDemo`, `Modal`, `Brand`, `LanguageToggle`, hooks, event handlers, and JSX.
- Depends on: `react`, `react-dom/client`, `react-router-dom`, `src/styles.css`, and images in `assets/`.
- Used by: Browser runtime through `createRoot(document.getElementById("root")).render(<App />)`.

**Translation Layer:**
- Purpose: Provide English/Chinese toggling without threading translation calls through every JSX node.
- Location: `src/main.jsx`
- Contains: `zhTranslations`, phrase replacements, `LanguageContext`, `LanguageProvider`, `TranslationLayer`, `translateSubtree`, and DOM mutation observer logic.
- Depends on: Browser DOM APIs (`document`, `NodeFilter`, `MutationObserver`), React context/effects, and `localStorage`.
- Used by: `App` and `LanguageToggle`.

**Fixture and Plan Builder Layer:**
- Purpose: Hold all demo product data and generate normalized campaign plans for the app workspace.
- Location: `src/main.jsx`
- Contains: arrays/objects such as `platforms`, `modules`, `moduleDetails`, `moduleWorkflows`, `businessTemplates`, `channelPlans`, `inboxThreads`, `localRoiSignals`, and helper functions.
- Depends on: imported images from `assets/`.
- Used by: `LandingPage` previews and `AppDemo` module views.

**Browser Persistence Layer:**
- Purpose: Preserve prototype state in the browser across refreshes.
- Location: `src/main.jsx`
- Contains: `loadStoredPlans`, `loadStoredInput`, `loadStoredIndex`, `loadStoredModule`, and `useEffect` persistence calls.
- Depends on: `window.localStorage`.
- Used by: `LandingPage`, `LanguageProvider`, and `AppDemo`.

**Styling Layer:**
- Purpose: Define visual system, responsive page layout, app shell, cards, forms, modals, toasts, and module-specific surfaces.
- Location: `src/styles.css`
- Contains: CSS custom properties, global reset, marketing sections, app shell, panels, responsive `@media` blocks.
- Depends on: class names emitted by `src/main.jsx`.
- Used by: All rendered UI.

**Packaging and Deployment Layer:**
- Purpose: Convert Vite output into deployable static client + server worker package.
- Location: `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs`, `.openai/hosting.json`
- Contains: generated worker source with asset fetch and HTML fallback, dist validation, tar archive creation.
- Depends on: Node built-ins and output from `vite build --outDir dist/client`.
- Used by: `npm run build` and `npm run package:sites`.

## Data Flow

### Primary Request Path

1. Browser loads `index.html`, reads metadata, and creates `<div id="root"></div>` (`index.html:1`).
2. Vite serves or builds the module script `/src/main.jsx` (`index.html:18`).
3. `src/main.jsx` imports React, router, CSS, and image assets (`src/main.jsx:1`).
4. `createRoot(document.getElementById("root")).render(<App />)` mounts the SPA (`src/main.jsx:2979`).
5. `App` wraps routes in `LanguageProvider` and `BrowserRouter` (`src/main.jsx:2964`).
6. Router renders `/` as `LandingPage`, `/app` as `AppDemo`, and unknown paths as `<Navigate to="/" replace />` (`src/main.jsx:2969`).

### Marketing-to-Demo Flow

1. `LandingPage` renders the public marketing experience and owns modal state (`src/main.jsx:1708`).
2. Pilot request form serializes `FormData` into `localStorage` under `localpilot-pilot-request` (`src/main.jsx:1720`).
3. Login form serializes `FormData` into `localStorage` under `localpilot-demo-session` with `loggedInAt` (`src/main.jsx:1729`).
4. Successful login calls `navigate("/app")`, causing the router to render `AppDemo` (`src/main.jsx:1736`).

### App Demo Campaign Flow

1. `AppDemo` reads the session, URL `?module=`, stored module, selected indices, campaign input, and stored plans on initialization (`src/main.jsx:2121`).
2. `normalizeCampaignInput` chooses a valid business template and fills missing campaign fields (`src/main.jsx:1572`).
3. `buildPlansFromInput` maps canonical `channelPlans` through the selected `businessTemplates` channel copy (`src/main.jsx:1587`).
4. `createInitialPlans` initializes status and checklist state for each generated plan (`src/main.jsx:1628`).
5. User actions such as approve, request changes, checklist toggle, regenerate, and export update React state and show toasts (`src/main.jsx:2220`).
6. `useEffect` handlers persist campaign input, plans, active module, and selected indices back to `localStorage` (`src/main.jsx:2185`).

### Translation Flow

1. `LanguageProvider` initializes language from `localStorage` key `localpilot-language` (`src/main.jsx:932`).
2. Language changes update `document.documentElement.lang` and persist the language (`src/main.jsx:950`).
3. `TranslationLayer` observes `#root` with `MutationObserver` and debounces translation passes (`src/main.jsx:970`).
4. `translateSubtree` updates translatable element attributes, campaign input values, and text nodes (`src/main.jsx:915`).
5. `data-no-translate` is the opt-out marker for controls that must remain stable, such as `LanguageToggle` (`src/main.jsx:998`).

### Build and Deployment Flow

1. `npm run build` runs `vite build --outDir dist/client --emptyOutDir true` and then `node scripts/prepare-sites-dist.mjs` (`package.json`).
2. `scripts/prepare-sites-dist.mjs` creates `dist/server/index.js` and copies `.openai/hosting.json` to `dist/.openai/hosting.json`.
3. Generated worker serves static assets through `env.ASSETS.fetch(request)` and falls back HTML requests to `/index.html` for SPA routing (`scripts/prepare-sites-dist.mjs`).
4. `npm run package:sites` runs the build and archives `dist/` to `SITES_ARCHIVE_PATH` or `/tmp/localpilot-ai-karen-demo-sites.tar.gz` (`scripts/package-sites.mjs`).

**State Management:**
- React local component state owns UI state inside `LandingPage` and `AppDemo`.
- Browser `localStorage` owns persistence; all stored values use `localpilot-*` keys in `src/main.jsx`.
- There is no backend state, database, server API, global state library, or external auth provider.

## Key Abstractions

**Language Provider and DOM Translation:**
- Purpose: Keep visible UI translatable while preserving the prototype's existing JSX copy.
- Examples: `LanguageProvider`, `TranslationLayer`, `translateDynamicText`, `translateSubtree` in `src/main.jsx`.
- Pattern: React context plus imperative DOM post-processing.

**Module Catalog:**
- Purpose: Drive the demo sidebar, active module, and module-specific views from a fixed list.
- Examples: `modules`, `moduleSlug`, `moduleFromSlug`, `moduleDetails`, `moduleWorkflows` in `src/main.jsx`.
- Pattern: Static registry plus URL/localStorage-selected state.

**Business Templates:**
- Purpose: Provide industry-specific default campaign input and channel copy.
- Examples: `defaultCampaignInput`, `businessTemplates`, `businessOptions` in `src/main.jsx`.
- Pattern: Fixture dictionary keyed by business type.

**Channel Plans:**
- Purpose: Provide canonical cross-platform plan structure for TikTok, Instagram, Facebook, Xiaohongshu, and Google Local.
- Examples: `channelPlans`, `buildPlansFromInput`, `createInitialPlans`, `normalizePlan` in `src/main.jsx`.
- Pattern: Base plan templates transformed by selected business context.

**Local Prototype Session:**
- Purpose: Simulate login and workspace persistence without a backend.
- Examples: `localpilot-demo-session`, `localpilot-demo-input`, `localpilot-demo-plans`, `localpilot-export-package` keys in `src/main.jsx`.
- Pattern: `localStorage`-backed session and state snapshots.

**Generated Sites Worker:**
- Purpose: Serve the static client bundle and support client-side routing on deployment.
- Examples: `workerSource` in `scripts/prepare-sites-dist.mjs`, generated output `dist/server/index.js`.
- Pattern: Static asset fetch with 404 HTML fallback.

## Entry Points

**Development Server:**
- Location: `package.json`
- Triggers: `npm run dev`
- Responsibilities: Starts Vite on `127.0.0.1` and serves `index.html` plus `src/main.jsx`.

**Production Build:**
- Location: `package.json`
- Triggers: `npm run build`
- Responsibilities: Builds client assets into `dist/client/` and prepares deployment worker/config.

**Sites Package:**
- Location: `package.json`, `scripts/package-sites.mjs`
- Triggers: `npm run package:sites`
- Responsibilities: Builds the app, verifies deployment files, and creates a tar archive.

**HTML Entry:**
- Location: `index.html`
- Triggers: Browser document load.
- Responsibilities: Provides root node and loads `/src/main.jsx`.

**React Entry:**
- Location: `src/main.jsx`
- Triggers: Module evaluation in the browser.
- Responsibilities: Mounts React and configures routes.

**Route `/`:**
- Location: `src/main.jsx`
- Triggers: Browser path `/`.
- Responsibilities: Renders `LandingPage`.

**Route `/app`:**
- Location: `src/main.jsx`
- Triggers: Browser path `/app`.
- Responsibilities: Renders `AppDemo`.

**Route `*`:**
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

**What happens:** Changing files under `dist/client/`, `dist/server/index.js`, or `dist/.openai/hosting.json` directly.
**Why it's wrong:** `npm run build` regenerates `dist/`, so manual changes disappear and source of truth becomes unclear.
**Do this instead:** Edit `src/main.jsx`, `src/styles.css`, `public/`, `.openai/hosting.json`, or `scripts/prepare-sites-dist.mjs`, then rebuild.

### Adding New Demo Views Outside the Module Registry

**What happens:** Rendering a new app section without adding it to `modules`, `moduleDetails`, and any needed `moduleWorkflows` in `src/main.jsx`.
**Why it's wrong:** Sidebar navigation, URL `?module=`, stored active module, and fallback config all depend on the registry.
**Do this instead:** Add the module name to `modules`, define its config in `moduleDetails`, and render through the existing `config.view` branching in `AppDemo`.

### Bypassing Plan Normalization

**What happens:** Writing raw plan objects to state or `localStorage` without using `normalizeCampaignInput`, `buildPlansFromInput`, `createInitialPlans`, or `normalizePlan`.
**Why it's wrong:** The app expects every plan to include canonical channel fields, `nativeCreative`, status, and checklist objects.
**Do this instead:** Route generated or restored plan data through the builder helpers in `src/main.jsx`.

### Translating JSX Inline While TranslationLayer Is Active

**What happens:** Mixing hardcoded bilingual strings directly into JSX for nodes also handled by `TranslationLayer`.
**Why it's wrong:** The mutation observer can rewrite text nodes and attributes after render, creating drift between React state and DOM text.
**Do this instead:** Add English source copy to JSX and extend `zhTranslations` or phrase replacement logic in `src/main.jsx`.

## Error Handling

**Strategy:** Best-effort prototype error handling with `try/catch` around browser persistence reads/writes and explicit fallback defaults.

**Patterns:**
- Wrap `localStorage` reads and JSON parsing in `try/catch`, falling back to default values in `LanguageProvider`, `loadStoredPlans`, `loadStoredInput`, `loadStoredIndex`, and `loadStoredModule`.
- Use `useLanguage` to throw if the hook is consumed outside `LanguageProvider`.
- Packaging scripts rely on promise rejection from `access`, `copyFile`, `tar` exit status, and archive size checks.
- Generated worker returns HTTP 500 when `env.ASSETS` is missing and otherwise returns original 404 responses for non-HTML missing assets.

## Cross-Cutting Concerns

**Logging:** Minimal. Runtime user feedback uses visible toasts in `LandingPage` and `AppDemo`; packaging logs final archive path in `scripts/package-sites.mjs`.
**Validation:** Form-level HTML `required`/`type` attributes in `LandingPage`; data normalization helpers in `src/main.jsx`; file existence checks in `scripts/package-sites.mjs`.
**Authentication:** Prototype-only. Login stores arbitrary form data in `localStorage` under `localpilot-demo-session`; no credentials, auth server, token validation, or protected route guard.
**Internationalization:** DOM-level translation observer in `src/main.jsx` with English/Chinese toggle persisted to `localStorage`.
**Assets:** Vite imports source images from `assets/`; public static files live under `public/`; generated build assets live under `dist/client/`.

---

*Architecture analysis: 2026-06-09*
