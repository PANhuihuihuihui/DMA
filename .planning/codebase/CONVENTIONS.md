---
last_mapped_commit: 64e01e3dfea3229b13fc4d25ac8c657efe12dab9
---

# Coding Conventions

**Analysis Date:** 2026-06-09

## Naming Patterns

**Files:**
- Use short lowercase source filenames for the current app surface: `src/main.jsx`, `src/styles.css`, `index.html`.
- Use kebab-case for Node utility scripts: `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs`.
- Use kebab-case for generated/static image assets: `assets/cafe-owner.png`, `assets/restaurant.png`, `assets/salon.png`.
- Keep documentation filenames descriptive and snake_case or kebab-case under `docs/`, such as `docs/design-qa.md` and `docs/landing_page_content_and_design_brief.md`.

**Functions:**
- Use PascalCase for React components and hooks providers: `LanguageProvider`, `TranslationLayer`, `LanguageToggle`, `LandingPage`, `Modal`, `AppDemo`, `App` in `src/main.jsx`.
- Use `use` prefix for React hooks: `useLanguage` in `src/main.jsx`.
- Use camelCase for helper functions: `translateDynamicText`, `normalizeTextKey`, `translateSubtree`, `moduleSlug`, `moduleFromSlug`, `normalizeCampaignInput`, `buildPlansFromInput`, `loadStoredPlans`, `clampIndex` in `src/main.jsx`.
- Use action-oriented camelCase for event handlers inside components: `submitPilot`, `submitLogin`, `showToast`, `showAppToast`, `logout`, `selectModule`, `applyWalkthroughStep`, `resetDemo`, `updatePlan`, `approvePlan`, `requestChanges`, `toggleChecklist`, `regeneratePlan`, `exportPackage`, `applyBusinessType` in `src/main.jsx`.

**Variables:**
- Use camelCase for local state and derived values: `menuOpen`, `pilotOpen`, `loginOpen`, `appToast`, `safeSelectedChannel`, `pendingPlans`, `approvedCount`, `checklistPercent`, `packageReadiness` in `src/main.jsx`.
- Use uppercase snake case for true constants: `LANGUAGE_STORAGE_KEY` in `src/main.jsx`.
- Use plural nouns for collection data: `platforms`, `modules`, `moduleWorkflows`, `schedule`, `aiStudioTasks`, `inboxThreads`, `localRoiSignals`, `pricingPlans`, `businessOptions`, `channelPlans` in `src/main.jsx`.
- Use `root`, `dist`, `serverDir`, `openAiDir`, `archivePath`, and `requiredFiles` for filesystem script paths in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.

**Types:**
- Not applicable. The codebase uses JavaScript/JSX rather than TypeScript, with no `.ts` or `.tsx` files detected.
- Data shapes are expressed as plain object literals in `src/main.jsx`, such as `defaultCampaignInput`, `businessTemplates`, `moduleDetails`, and `channelPlans`.

## Code Style

**Formatting:**
- No formatter configuration is present. No `.prettierrc`, `eslint.config.*`, `biome.json`, `tsconfig.json`, or `jsconfig.json` was detected at the repository root.
- Follow the existing style in `src/main.jsx`: two-space indentation, double quotes, semicolons, trailing commas in multiline arrays/objects/calls, and parenthesized multiline JSX returns.
- Keep JSX props on separate lines when elements have several attributes, as shown by `LanguageToggle`, `LandingPage`, and `AppDemo` in `src/main.jsx`.
- Keep CSS custom properties in `:root` and reuse them throughout `src/styles.css`: `--ink`, `--muted`, `--soft`, `--line`, `--green`, `--green-dark`, `--coral`, `--blue`, `--red`, `--paper`, `--wash`, `--shadow`.

**Linting:**
- No linting tool is configured in `package.json`.
- No lint script is available. Current scripts are `dev`, `build`, `package:sites`, and `preview` in `package.json`.
- Preserve React hook rules manually: call hooks only at component/hook top level in `src/main.jsx`, as done by `LanguageProvider`, `TranslationLayer`, `LandingPage`, and `AppDemo`.

## Import Organization

**Order:**
1. React imports first, grouped by package: `react` in `src/main.jsx`.
2. React platform/router imports next: `react-dom/client` and `react-router-dom` in `src/main.jsx`.
3. Local stylesheet import next: `./styles.css` in `src/main.jsx`.
4. Local asset imports last: PNG imports from `../assets/*.png` in `src/main.jsx`.

**Path Aliases:**
- No path aliases are configured. Use relative imports from the file location.
- Use package imports for dependencies: `react`, `react-dom/client`, `react-router-dom`.
- Use `node:` protocol imports for built-in modules in scripts: `node:fs/promises`, `node:path`, `node:url`, `node:child_process` in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.

## Error Handling

**Patterns:**
- Use guarded `try`/`catch` for browser persistence reads and writes where failure should not break the demo: `LanguageProvider`, `loadStoredPlans`, `loadStoredInput`, `loadStoredIndex`, `loadStoredModule`, and session parsing in `AppDemo` in `src/main.jsx`.
- Return safe defaults from persistence helpers when stored data is missing or invalid: `createInitialPlans(input)`, `normalizeCampaignInput(defaultCampaignInput)`, numeric fallback indexes, and `"Home"` in `src/main.jsx`.
- Throw explicit programmer errors for invalid hook usage: `useLanguage` throws `new Error("useLanguage must be used inside LanguageProvider")` in `src/main.jsx`.
- In Node scripts, allow top-level `await` failures to fail the command, and throw explicit validation errors after external work: `scripts/package-sites.mjs` throws if the archive is empty.
- For child processes, reject on non-zero exit codes with a clear message: `scripts/package-sites.mjs` rejects with `new Error(\`tar exited with code ${code}\`)`.

## Logging

**Framework:** console

**Patterns:**
- Use `console.log` only for successful CLI/script status messages, as in `scripts/package-sites.mjs`.
- The React app communicates user-visible status through toast state instead of console logging: `showToast` in `LandingPage` and `showAppToast` in `AppDemo` in `src/main.jsx`.
- No structured logging framework is configured.

## Comments

**When to Comment:**
- Comments are sparse. Add comments only for behavior that is not obvious from names or control flow.
- Existing comment style explains intentional degradation, such as the localStorage write fallback in `LanguageProvider` in `src/main.jsx`.

**JSDoc/TSDoc:**
- Not used. No JSDoc or TSDoc blocks were detected in `src/main.jsx` or `scripts/*.mjs`.
- Prefer self-describing helper and handler names over adding documentation comments for small functions.

## Function Design

**Size:** Keep new pure helpers small and data-oriented like `moduleSlug`, `moduleFromSlug`, `inferBusinessType`, `normalizeCampaignInput`, `loadStoredIndex`, and `clampIndex` in `src/main.jsx`. Existing screen components are large; place new transformation logic in helpers above components rather than growing JSX handlers further.

**Parameters:** Use object inputs for campaign/domain data, with defaults where appropriate: `normalizeCampaignInput(input = defaultCampaignInput)`, `buildPlansFromInput(input = defaultCampaignInput)`, `createInitialPlans(input = defaultCampaignInput)`, `normalizePlan(plan, index, input = defaultCampaignInput)` in `src/main.jsx`.

**Return Values:** Return normalized plain objects and arrays from helpers. For UI event handlers, mutate React state and localStorage, then show a toast; do not return data from handlers such as `submitPilot`, `submitLogin`, `approvePlan`, `requestChanges`, and `exportPackage` in `src/main.jsx`.

## Module Design

**Exports:** The current app does not export application modules from `src/main.jsx`; it renders directly with `createRoot(document.getElementById("root")).render(<App />)`.

**Barrel Files:** Not used. No `index.js` barrel modules are present in `src/` or `scripts/`.

**State Pattern:** Use React component state for UI state and `window.localStorage` for prototype persistence. Persist app fields with focused `useEffect` blocks keyed to individual state values in `AppDemo` in `src/main.jsx`.

**Styling Pattern:** Use global CSS classes in `src/styles.css`. Class names are descriptive kebab-case and grouped by surface, such as `.site-header`, `.language-toggle`, `.primary-button`, `.workspace-card`, `.campaign-builder`, and `.industry-card`.

---

*Convention analysis: 2026-06-09*
