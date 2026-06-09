---
last_mapped_commit: 64e01e3dfea3229b13fc4d25ac8c657efe12dab9
---

# Technology Stack

**Analysis Date:** 2026-06-09

## Languages

**Primary:**
- JavaScript / JSX - React application code in `src/main.jsx`, styling imports through `src/styles.css`, and browser APIs such as `window.localStorage`, `FormData`, `MutationObserver`, and `URLSearchParams`.
- CSS - Responsive visual system and layout rules in `src/styles.css`.

**Secondary:**
- HTML - Vite document shell in `index.html`.
- Node.js ES modules - Build and packaging helpers in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.
- JSON - Package metadata in `package.json`, dependency lock in `package-lock.json`, and Sites hosting metadata in `.openai/hosting.json`.

## Runtime

**Environment:**
- Browser runtime for the application UI. `index.html` loads `/src/main.jsx`, which mounts React into `#root` with `createRoot(document.getElementById("root")).render(<App />)`.
- Node.js for development/build scripts. Vite 7.3.5 and `@vitejs/plugin-react` 5.2.0 require Node `^20.19.0 || >=22.12.0` according to `package-lock.json`; `react-router-dom` 7.17.0 requires Node `>=20.0.0`.
- Cloudflare Worker-compatible static asset runtime for packaged deployment. `scripts/prepare-sites-dist.mjs` writes `dist/server/index.js`, whose generated worker uses `env.ASSETS.fetch(request)` and falls back HTML requests to `/index.html`.

**Package Manager:**
- npm - scripts and lockfile use npm conventions in `package.json` and `package-lock.json`.
- Lockfile: present at `package-lock.json` with lockfileVersion 3.

## Frameworks

**Core:**
- React `^19.2.1` requested in `package.json`; locked to 19.2.7 in `package-lock.json`. Used for all UI components, context, effects, memoized state, and rendering in `src/main.jsx`.
- React DOM `^19.2.1` requested in `package.json`; locked to 19.2.7 in `package-lock.json`. Used through `createRoot` in `src/main.jsx`.
- React Router DOM `^7.10.1` requested in `package.json`; locked to 7.17.0 in `package-lock.json`. Used for `BrowserRouter`, `Routes`, `Route`, `Navigate`, `Link`, `useLocation`, and `useNavigate` in `src/main.jsx`.

**Testing:**
- Not detected. `package.json` defines no `test` script and there are no test framework dependencies in `package.json`.

**Build/Dev:**
- Vite `^7.2.7` requested in `package.json`; locked to 7.3.5 in `package-lock.json`. `npm run dev` runs `vite --host 127.0.0.1`; `npm run build` runs `vite build --outDir dist/client --emptyOutDir true`.
- `@vitejs/plugin-react` `^5.1.1` requested in `package.json`; locked to 5.2.0 in `package-lock.json`. Installed as the React transform plugin, with no explicit `vite.config.*` file detected.
- Node built-ins are used by packaging scripts: `node:fs/promises`, `node:path`, `node:url`, and `node:child_process` in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.
- System `tar` is invoked by `scripts/package-sites.mjs` via `spawn("tar", ["-C", root, "-czf", archivePath, "dist"])`.

## Key Dependencies

**Critical:**
- `react` - Component framework for landing page, fake login, app demo, translation layer, and stateful workflows in `src/main.jsx`.
- `react-dom` - Browser rendering entrypoint in `src/main.jsx`.
- `react-router-dom` - Client-side routing for `/`, `/app`, module query links, and fallback navigation in `src/main.jsx`.
- `vite` - Development server and production bundler configured through `package.json` scripts.

**Infrastructure:**
- `@vitejs/plugin-react` - React refresh and JSX/Babel integration for Vite, present in `package.json` and `package-lock.json`.
- `node:fs/promises` - Creates deployment output, writes generated worker code, and validates packaged artifacts in `scripts/prepare-sites-dist.mjs` and `scripts/package-sites.mjs`.
- `node:child_process` - Runs `tar` to create the Sites archive in `scripts/package-sites.mjs`.

## Configuration

**Environment:**
- No `.env` or `.env.*` files detected in the repository scan.
- `SITES_ARCHIVE_PATH` is the only detected environment variable. `scripts/package-sites.mjs` reads `process.env.SITES_ARCHIVE_PATH` and defaults to `/tmp/localpilot-ai-karen-demo-sites.tar.gz`.
- Browser-local persistence uses fixed `localStorage` keys in `src/main.jsx`, including `localpilot-language`, `localpilot-demo-session`, `localpilot-demo-input`, `localpilot-demo-plans`, `localpilot-pilot-request`, and `localpilot-export-package`.

**Build:**
- `package.json` owns all runnable scripts:
  - `npm run dev` starts Vite on `127.0.0.1`.
  - `npm run build` emits the Vite client bundle into `dist/client` and then runs `node scripts/prepare-sites-dist.mjs`.
  - `npm run package:sites` builds and archives `dist`.
  - `npm run preview` starts `vite preview --host 127.0.0.1`.
- `index.html` is the Vite HTML entry and sets the page title, description, favicon, root container, and module script.
- `.openai/hosting.json` configures OpenAI/Sites storage bindings with `"d1": null` and `"r2": null`.
- No `vite.config.*`, `tsconfig.json`, ESLint config, Prettier config, or test config files were detected.

## Platform Requirements

**Development:**
- Node.js `^20.19.0 || >=22.12.0` is required by Vite and `@vitejs/plugin-react`; Node `>=20.0.0` is required by React Router packages in `package-lock.json`.
- npm install uses `package-lock.json`.
- Local preview instructions in `README.md` use `npm install` and `npm run dev -- --port 4173`, then browse `http://127.0.0.1:4173/`.

**Production:**
- Frontend-only static deployment with a generated Cloudflare Worker-compatible Sites wrapper.
- `npm run build` prepares `dist/client/**`, `dist/server/index.js`, and `dist/.openai/hosting.json`.
- `npm run package:sites` writes a deployable archive to `SITES_ARCHIVE_PATH` or `/tmp/localpilot-ai-karen-demo-sites.tar.gz`.
- `README.md` states remote Sites deployment is blocked until Sites is enabled for the workspace.

---

*Stack analysis: 2026-06-09*
