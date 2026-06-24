# LocalPilot AI

AI marketing operator for local small businesses.

LocalPilot AI helps owners turn one video, menu item, service, or promotion into platform-native campaigns for TikTok, Instagram, Facebook, and Xiaohongshu. The demo is now a React + Vite app with a public landing page, fake login, and post-login agency workspace prototype.

## Preview

Install dependencies and run the local Vite dev server:

```bash
npm install
npm run dev -- --port 4173
```

Then visit:

```text
http://127.0.0.1:4173/
```

Fake login from the landing page routes into:

```text
http://127.0.0.1:4173/app
```

Direct app module review links:

```text
http://127.0.0.1:4173/app?module=home
http://127.0.0.1:4173/app?module=ai-studio
http://127.0.0.1:4173/app?module=calendar
http://127.0.0.1:4173/app?module=inbox
http://127.0.0.1:4173/app?module=analytics
```

## Deployment Package

The app is frontend-only and builds a Cloudflare Worker-compatible Sites artifact.

```bash
npm run package:sites
```

This runs the production build, prepares:

- `dist/server/index.js`
- `dist/client/**`
- `dist/.openai/hosting.json`

Then it writes the deployable archive to:

```text
/tmp/localpilot-ai-karen-demo-sites.tar.gz
```

Current remote deployment status: Sites provisioning is blocked until Sites is enabled for this workspace. When it is enabled, create the Sites project, save a version from the archive, and deploy that version.

## Backend Setup (Phase 4+)

The Python backend requires one third-party dependency for token encryption:

```bash
pip install -r backend/requirements.txt
```

To run the full stack (frontend + backend):

```bash
npm run dev:full
```

### Token encryption (optional for local dev)

Facebook Page tokens are encrypted at rest using Fernet symmetric encryption.

- **Local dev (no key set):** The backend runs in a clearly-labeled insecure mode — tokens are kept in memory only and lost on restart. The demo still works.
- **Production:** Set `LOCALPILOT_ENV=production` and `LOCALPILOT_TOKEN_KEY` — the backend refuses to handle tokens without the key.

Generate a dev key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Then export it:

```bash
export LOCALPILOT_TOKEN_KEY="<paste key>"
```

Never commit the key. The `.gitignore` should exclude any local key files.

## Structure

- `index.html`: Vite HTML entry
- `src/main.jsx`: React routes, landing page, fake login, and app demo
- `src/styles.css`: responsive visual system and app layout
- `package.json`: Vite/React scripts and dependencies
- `assets/`: generated local business imagery
- `docs/`: market research, CEO/CTO plan, landing page brief, visual options, and QA notes
- `scripts/`: Sites build and package helpers

## Product Wedge

This is not a generic social scheduler. The strongest differentiation is local-business strategy plus platform-native content, including Xiaohongshu/小红书-native planning and local ROI tracking for calls, bookings, DMs, coupon scans, saves, and map clicks.
