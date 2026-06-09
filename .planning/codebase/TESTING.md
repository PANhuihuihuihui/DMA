---
last_mapped_commit: 64e01e3dfea3229b13fc4d25ac8c657efe12dab9
---

# Testing Patterns

**Analysis Date:** 2026-06-09

## Test Framework

**Runner:**
- Not detected.
- No `jest.config.*`, `vitest.config.*`, `playwright.config.*`, or test setup file was detected.
- `package.json` does not define a `test` script.

**Assertion Library:**
- Not detected.

**Run Commands:**
```bash
npm run build          # Current production verification path
npm run package:sites  # Builds and creates the deployable Sites archive
npm run preview        # Serves the built Vite app for manual inspection
```

## Test File Organization

**Location:**
- No automated test files were detected under the repository.
- No files matching `*.test.*` or `*.spec.*` were detected.

**Naming:**
- Not established. If tests are added, prefer co-located files next to the code they cover because the codebase is compact: `src/main.test.jsx` for `src/main.jsx` and `scripts/package-sites.test.mjs` for `scripts/package-sites.mjs`.

**Structure:**
```text
Current repository:
src/
├── main.jsx        # React app, helpers, routes, and state
└── styles.css      # Global styles
scripts/
├── prepare-sites-dist.mjs
└── package-sites.mjs
```

## Test Structure

**Suite Organization:**
```javascript
// No existing automated suite is present.
// Match current helper boundaries when introducing tests:
describe("normalizeCampaignInput", () => {
  it("falls back to the default campaign input for invalid stored data", () => {
    // Exercise helpers from `src/main.jsx` after extracting/exporting them.
  });
});
```

**Patterns:**
- Current verification is command-based rather than test-runner-based. `npm run build` in `package.json` runs `vite build --outDir dist/client --emptyOutDir true` and then `node scripts/prepare-sites-dist.mjs`.
- Manual preview is documented in `README.md` with `npm run dev -- --port 4173` and inspection of `/`, `/app`, and `/app?module=...` routes.
- Visual QA evidence is documented in `docs/design-qa.md`, including desktop browser inspection of the landing page, campaign dashboard, ROI area, industry cards, Xiaohongshu feature, pricing, and footer.

## Mocking

**Framework:** Not detected.

**Patterns:**
```javascript
// No mocking pattern exists yet.
// Browser APIs that need mocks when tests are added:
window.localStorage.getItem("localpilot-demo-input");
window.localStorage.setItem("localpilot-demo-plans", JSON.stringify(plans));
window.localStorage.removeItem("localpilot-export-package");
```

**What to Mock:**
- Mock `window.localStorage` for persistence helpers and event handlers in `src/main.jsx`.
- Mock timers for toast behavior and translation debouncing: `window.setTimeout`, `window.clearTimeout` in `LanguageProvider`, `TranslationLayer`, `LandingPage`, and `AppDemo` in `src/main.jsx`.
- Mock `MutationObserver`, `document.createTreeWalker`, and DOM node attributes for translation-layer unit tests in `src/main.jsx`.
- Mock filesystem and child process operations for packaging script tests: `access`, `mkdir`, `stat`, and `spawn` in `scripts/package-sites.mjs`; `rm`, `mkdir`, `writeFile`, and `copyFile` in `scripts/prepare-sites-dist.mjs`.

**What NOT to Mock:**
- Do not mock pure campaign-plan helpers once they are importable: `normalizeCampaignInput`, `buildPlansFromInput`, `createInitialPlans`, `normalizePlan`, `clampIndex` in `src/main.jsx`.
- Do not mock React Router behavior in integration tests for route-level flows; render with a router and assert navigation between `/` and `/app`.
- Do not mock the production build in verification; `npm run build` should execute Vite and the post-build script.

## Fixtures and Factories

**Test Data:**
```javascript
const input = {
  business: "Sunny Side Bistro",
  businessType: "restaurant",
  offer: "Weekend lunch special",
  goal: "fill tables",
  audience: "nearby diners",
};
```

**Location:**
- Current fixture-like data lives inline in `src/main.jsx`: `defaultCampaignInput`, `businessTemplates`, `businessOptions`, `channelPlans`, `moduleDetails`, `moduleWorkflows`, `schedule`, `aiStudioTasks`, `inboxThreads`, `localRoiSignals`, `walkthroughSteps`, and `pricingPlans`.
- If test fixtures are introduced, keep small domain fixtures near tests or extract reusable app data from `src/main.jsx` into a dedicated source module before testing it.

## Coverage

**Requirements:** None enforced.

**View Coverage:**
```bash
# Not available. No coverage command is configured in `package.json`.
```

## Test Types

**Unit Tests:**
- Not currently present.
- Highest-value future unit targets are pure helpers in `src/main.jsx`: `translateDynamicText`, `normalizeTextKey`, `moduleSlug`, `moduleFromSlug`, `inferBusinessType`, `normalizeCampaignInput`, `buildPlansFromInput`, `createInitialPlans`, `normalizePlan`, `loadStoredIndex`, and `clampIndex`.
- Packaging scripts in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs` are also candidates for unit tests around expected files, archive path handling, and failure behavior.

**Integration Tests:**
- Not currently present.
- Highest-value future integration targets are route and state flows in `src/main.jsx`: fake login from `LandingPage` to `/app`, language toggle persistence, campaign regeneration, approval checklist state, package export to `localStorage`, and reset behavior.

**E2E Tests:**
- Not used.
- Manual E2E-style checks are documented in `README.md` and `docs/design-qa.md`, covering `http://127.0.0.1:4173/`, `http://127.0.0.1:4173/app`, and direct module links like `/app?module=calendar`.

## Common Patterns

**Async Testing:**
```javascript
// No automated async tests exist.
// Current async code is top-level Node ESM in `scripts/*.mjs` and React effects in `src/main.jsx`.
```

**Error Testing:**
```javascript
// Existing error behavior to preserve when tests are added:
// - invalid localStorage JSON returns safe defaults in `src/main.jsx`
// - missing Sites build files reject through `access(file)` in `scripts/package-sites.mjs`
// - empty archives throw `new Error(...)` in `scripts/package-sites.mjs`
```

**Manual Verification Checklist:**
- Run `npm run build` after source changes that affect `src/main.jsx`, `src/styles.css`, `index.html`, assets, or scripts.
- Run `npm run package:sites` after changes to `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs`, `.openai/hosting.json`, or deployable output assumptions.
- Manually inspect `/`, `/app`, and module routes listed in `README.md` after UI, routing, language, or state changes.
- Re-check `docs/design-qa.md` surfaces after visual changes: hero/root, campaign dashboard/ROI area, industry cards, Xiaohongshu feature, pricing, and footer.

---

*Testing analysis: 2026-06-09*
