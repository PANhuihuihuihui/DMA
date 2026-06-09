---
last_mapped_commit: 64e01e3dfea3229b13fc4d25ac8c657efe12dab9
---

# Codebase Concerns

**Analysis Date:** 2026-06-09

## Tech Debt

**Single-file React application:**
- Issue: The full application routing, landing page, demo workspace, translation logic, fixtures, state persistence, and rendering live in one 2,979-line file.
- Files: `src/main.jsx`
- Impact: Small UI or behavior changes require navigating unrelated concerns in the same file, increasing regression risk around routing, demo state, translation, and rendering.
- Fix approach: Split by responsibility: route shell/components in `src/main.jsx`, landing components under `src/landing/`, demo workspace modules under `src/app/`, static demo data under `src/data/`, and language helpers under `src/i18n/`.

**Monolithic stylesheet:**
- Issue: The visual system, landing page, app shell, panels, controls, and responsive rules live in one 2,834-line CSS file.
- Files: `src/styles.css`
- Impact: Selector collisions and mobile regressions are hard to isolate because unrelated UI surfaces share global class names and media queries.
- Fix approach: Keep global tokens/reset in `src/styles.css`, move landing styles to `src/landing/landing.css`, app styles to `src/app/app.css`, and reusable controls to component-scoped CSS modules or clearly prefixed class groups.

**No lint, format, or test commands:**
- Issue: `package.json` exposes only dev/build/package/preview scripts and has no ESLint, Prettier, TypeScript, Vitest, Jest, or Playwright configuration.
- Files: `package.json`, `src/main.jsx`, `src/styles.css`
- Impact: Naming, formatting, accessibility, route behavior, localStorage behavior, and responsive layout regressions rely on manual review only.
- Fix approach: Add `lint`, `format:check`, and `test` scripts in `package.json`; start with React lint rules and smoke tests for `/`, `/app`, and direct `?module=` routes.

**Generated deployment output present in the worktree:**
- Issue: `dist/` contains generated Cloudflare Sites output while `.gitignore` also ignores `dist/`.
- Files: `dist/client/index.html`, `dist/client/assets/index-Cl1ruq9U.js`, `dist/server/index.js`, `.gitignore`
- Impact: Local generated artifacts can drift from source and confuse manual deployment validation, especially because the packaging script archives `dist/` directly.
- Fix approach: Treat `dist/` as build output only. Regenerate through `npm run build` before packaging and avoid reviewing or editing `dist/` manually.

**Hard-coded demo fixtures mixed with UI:**
- Issue: Business templates, module details, schedules, inbox threads, ROI signals, pricing plans, walkthrough steps, and generated plan logic are embedded in `src/main.jsx`.
- Files: `src/main.jsx`
- Impact: Product copy updates and logic updates touch the same component file, making content review and feature changes coupled.
- Fix approach: Move fixture arrays and business templates into `src/data/demoContent.js`; keep `src/main.jsx` focused on composition and event handlers.

## Known Bugs

**Potential stale plan name in toast after approval/change:**
- Symptoms: `approvePlan` and `requestChanges` show toast messages from `plans[index]` immediately after scheduling state updates. If the index becomes stale after a route/module change or stored state normalization, the toast can reference the wrong item or throw when `plans[index]` is undefined.
- Files: `src/main.jsx:2270`, `src/main.jsx:2275`
- Trigger: Trigger a topbar action or approval action while selected indexes are being clamped after stored state or regenerated plans change.
- Workaround: Use `const plan = plans[index]` with a guard before updating, or derive the toast message inside the state updater from the matched plan.

**Reset does not clear all persisted demo state:**
- Symptoms: `resetDemo` removes `localpilot-export-package` and resets selected post/channel, but it leaves `localpilot-demo-selected-inbox`, `localpilot-demo-selected-walkthrough`, and `localpilot-demo-active-module` persistence to subsequent effects.
- Files: `src/main.jsx:2250`, `src/main.jsx:2212`, `src/main.jsx:2216`
- Trigger: Use the walkthrough or inbox, reset the demo, then revisit after localStorage effects settle or after reload.
- Workaround: Remove all `localpilot-demo-*` keys in one reset helper before applying default in-memory state.

**No route guard for fake login:**
- Symptoms: `/app` renders the demo workspace even when `localpilot-demo-session` is missing; the session fallback displays a default workspace.
- Files: `src/main.jsx:2121`, `src/main.jsx:2124`, `src/main.jsx:2350`
- Trigger: Open `http://127.0.0.1:4173/app` directly or clear `localpilot-demo-session` and reload `/app`.
- Workaround: Keep this behavior only if intentional for demos; otherwise redirect to `/` when `session` is null.

## Security Considerations

**Personally identifiable form data stored in localStorage:**
- Risk: Pilot request data and fake login form data are persisted in browser localStorage with names, emails, business names, and challenge text.
- Files: `src/main.jsx:1720`, `src/main.jsx:1729`
- Current mitigation: The README describes the app as a frontend-only prototype with fake login/demo data; localStorage access is wrapped in some read paths.
- Recommendations: For production, submit form data to a backend over HTTPS, avoid storing emails and free-text challenge fields in localStorage, and clear demo keys on logout/reset.

**User-controlled prompt and campaign fields feed rendered copy:**
- Risk: User-entered prompt, offer, goal, and audience values flow into visible campaign text and saved localStorage payloads.
- Files: `src/main.jsx:2289`, `src/main.jsx:2326`, `src/main.jsx:2305`
- Current mitigation: React escapes rendered text by default and no `dangerouslySetInnerHTML` or `eval` usage is detected.
- Recommendations: Preserve React text rendering, avoid adding HTML injection paths, and validate length/content before sending these fields to any future API or report export.

**Future social integrations imply token risk but no secret handling layer exists:**
- Risk: Product docs call for Meta, TikTok, Google Business, and Xiaohongshu integrations, but the app currently has no backend boundary, OAuth storage, token refresh, or secrets management pattern.
- Files: `docs/feature_gap_priority_review.md`, `docs/digital_marketing_agent_market_research.md`, `src/main.jsx`
- Current mitigation: Current implementation is frontend-only and mock-only.
- Recommendations: Add a backend integration layer before real publishing APIs. Keep OAuth secrets and refresh tokens out of the browser and document required environment variables without committing secret values.

**Deployment package path can include arbitrary local destination:**
- Risk: `SITES_ARCHIVE_PATH` controls where `scripts/package-sites.mjs` writes the tarball.
- Files: `scripts/package-sites.mjs:8`, `scripts/package-sites.mjs:17`, `scripts/package-sites.mjs:20`
- Current mitigation: The script defaults to `/tmp/localpilot-ai-karen-demo-sites.tar.gz` and uses `spawn("tar", args)` without shell interpolation.
- Recommendations: Restrict `SITES_ARCHIVE_PATH` to an expected output directory in CI and fail if it points inside source directories or sensitive paths.

## Performance Bottlenecks

**DOM-wide translation pass after mutations:**
- Problem: Language switching scans the entire `#root` subtree, translates attributes/input values, walks every text node, and repeats after observed child-list mutations.
- Files: `src/main.jsx:921`, `src/main.jsx:970`, `src/main.jsx:986`
- Cause: Translation is implemented as a DOM mutation layer outside React rather than rendering translated strings from state.
- Improvement path: Move translations into React render data or a small i18n helper so only affected components rerender; remove the global `MutationObserver`.

**Large initial JavaScript and CSS surface:**
- Problem: Landing page and full demo workspace load together from `src/main.jsx` and `src/styles.css`.
- Files: `src/main.jsx`, `src/styles.css`, `package.json:8`
- Cause: No route-level code splitting or component-level style splitting is present.
- Improvement path: Split `LandingPage` and `AppDemo` into lazy-loaded routes using `React.lazy`; split CSS by route or component group.

**Heavy image footprint for prototype assets:**
- Problem: Source images total about 10 MB in `assets/`; generated deployment output in `dist/` totals about 11 MB.
- Files: `assets/cafe-owner.png`, `assets/restaurant.png`, `assets/salon.png`, `assets/clinic.png`, `assets/shop.png`, `dist/client/assets/`
- Cause: Generated raster assets are committed as large PNGs and imported directly into the app.
- Improvement path: Convert large PNGs to optimized WebP/AVIF variants, add explicit dimensions, and keep deployment artifacts generated from source assets.

## Fragile Areas

**Translation layer mutates React-owned DOM:**
- Files: `src/main.jsx:970`, `src/main.jsx:982`, `src/main.jsx:986`
- Why fragile: React owns the rendered DOM, but `TranslationLayer` changes text nodes, placeholders, aria labels, and input values after render. React updates can overwrite translations, and translation mutations can trigger additional observer passes.
- Safe modification: Avoid adding new user-editable fields to the DOM mutation path. Prefer extracting translation keys and rendering translated values directly from React state.
- Test coverage: No automated coverage exists for language toggling, form values, aria labels, or rerender behavior.

**localStorage schema has no versioning or centralized key management:**
- Files: `src/main.jsx:935`, `src/main.jsx:1657`, `src/main.jsx:1668`, `src/main.jsx:2185`, `src/main.jsx:2305`
- Why fragile: Stored objects are normalized opportunistically, but keys and payload shapes are scattered through the file. Future plan shape changes can leave old localStorage data partially compatible.
- Safe modification: Centralize storage keys and migrations in `src/storage/demoStorage.js`; add schema version and a single reset/clear function.
- Test coverage: No automated coverage exists for corrupted localStorage, old payloads, quota errors, or reset behavior.

**Responsive layout depends on broad global media overrides:**
- Files: `src/styles.css:2600`, `src/styles.css:2639`, `src/styles.css:2692`
- Why fragile: The mobile breakpoint applies many unrelated selectors in one rule set, so changing one component can affect landing sections, app panels, inbox, analytics, and package layout together.
- Safe modification: Keep route-specific responsive rules near the component group they affect, and prefer component class prefixes such as `.landing-*` and `.app-*`.
- Test coverage: No automated screenshot or viewport tests are detected.

**Deployment helper deletes and rewrites pieces of `dist/`:**
- Files: `scripts/prepare-sites-dist.mjs:34`, `scripts/prepare-sites-dist.mjs:35`, `scripts/prepare-sites-dist.mjs:38`
- Why fragile: Build output is reshaped after Vite emits files. Changes to Vite output structure or Cloudflare Sites expectations can break packaging without source-level type checks.
- Safe modification: Keep `scripts/prepare-sites-dist.mjs` small and covered by a smoke check that asserts `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json` exist after build.
- Test coverage: No automated deployment artifact test is detected.

## Scaling Limits

**Frontend-only prototype state:**
- Current capacity: One browser/localStorage workspace with fake session and demo data.
- Limit: Multi-user collaboration, server-side persistence, real approvals, reports, publishing jobs, and audit trails cannot work reliably in browser-only storage.
- Scaling path: Add a backend API and database for users, workspaces, campaigns, approvals, content assets, and publishing job status.

**Static module configuration:**
- Current capacity: A fixed list of modules and static demo cards in `src/main.jsx`.
- Limit: Adding real feature modules increases the size and complexity of the same source file.
- Scaling path: Move each module to its own route/component and load module metadata from `src/app/modules/`.

**Manual deployment packaging:**
- Current capacity: Local `npm run package:sites` writes a tarball to `/tmp` or `SITES_ARCHIVE_PATH`.
- Limit: Reproducibility depends on the developer’s local environment and current `dist/` output.
- Scaling path: Add CI that runs install, build, artifact smoke checks, and package creation from a clean checkout.

## Dependencies at Risk

**No pinned runtime version:**
- Risk: `package.json` has no `engines` field and no `.nvmrc` is detected.
- Impact: Vite 7 and React 19 builds may behave differently across Node versions or fail on unsupported runtimes.
- Migration plan: Add `engines.node` in `package.json` and a matching `.nvmrc`; document the version in `README.md`.

**No dependency audit workflow:**
- Risk: No script or CI config runs dependency vulnerability checks.
- Impact: Browser-build dependencies can accumulate known vulnerabilities unnoticed.
- Migration plan: Add a regular `npm audit --omit=dev` or dependency scanning workflow once CI exists.

## Missing Critical Features

**Automated tests:**
- Problem: No test files, test scripts, or test framework configuration are detected.
- Blocks: Safe refactoring of `src/main.jsx`, storage migrations, language behavior, routing, and responsive app flows.

**Accessibility verification:**
- Problem: Modal focus trapping, keyboard escape handling, route focus management, and interactive control semantics are not covered by automated checks.
- Blocks: Reliable keyboard-only and screen-reader use as the prototype moves toward production.

**Backend/API boundary:**
- Problem: The app stores session, pilot requests, campaign plans, and export packages entirely in localStorage.
- Blocks: Real login, secure pilot requests, real integrations, team workflows, and persistent campaign packages.

## Test Coverage Gaps

**Routes and navigation:**
- What's not tested: `/`, `/app`, unknown-route redirect, direct `?module=` links, module switching, and logout navigation.
- Files: `src/main.jsx`
- Risk: Route changes or React Router upgrades can break demo entry points without detection.
- Priority: High

**Demo persistence and reset behavior:**
- What's not tested: localStorage load/normalize paths, corrupted JSON handling, quota failures, reset behavior, and export package persistence.
- Files: `src/main.jsx:1657`, `src/main.jsx:1668`, `src/main.jsx:2185`, `src/main.jsx:2250`, `src/main.jsx:2296`
- Risk: Returning demo users can see stale or inconsistent workspace state.
- Priority: High

**Language switching:**
- What's not tested: English/Chinese toggling, translated placeholders, aria labels, user input preservation, dynamic DOM updates, and observer cleanup.
- Files: `src/main.jsx:900`, `src/main.jsx:970`
- Risk: Translation changes can overwrite form input, miss dynamically rendered content, or create unnecessary DOM work.
- Priority: High

**Deployment artifact generation:**
- What's not tested: Output files required by Cloudflare Sites packaging and fallback behavior in the generated worker.
- Files: `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs`, `.openai/hosting.json`
- Risk: Packaging can succeed locally while producing incomplete or stale deploy artifacts.
- Priority: Medium

**Responsive visual regressions:**
- What's not tested: Landing page and app workspace at mobile/tablet/desktop breakpoints.
- Files: `src/styles.css`, `src/main.jsx`
- Risk: Broad CSS changes can break critical demo screens without functional test failures.
- Priority: Medium

---

*Concerns audit: 2026-06-09*
