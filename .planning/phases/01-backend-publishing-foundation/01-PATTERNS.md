# Phase 01: Backend Publishing Foundation - Pattern Map

**Mapped:** 2026-06-10
**Files analyzed:** 22 file groups
**Analogs found:** 14 / 22

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `package.json` | config | request-response/build | `package.json` | exact |
| backend app entry, e.g. `backend/app/main.py` | config | request-response | `scripts/prepare-sites-dist.mjs` | no backend analog |
| backend config, e.g. `backend/app/config.py` | config | request-response | `scripts/package-sites.mjs` | partial |
| backend API routes, e.g. `backend/app/api/v1/*.py` | route/controller | request-response CRUD | none | no analog |
| backend domain models, e.g. `backend/app/models/*.py` | model | CRUD/event-driven | `src/main.jsx` plan objects | partial |
| backend schemas/contracts, e.g. `backend/app/schemas/*.py` | model | transform | `normalizeCampaignInput`, `normalizePlan` in `src/main.jsx` | partial |
| backend repository/storage, e.g. `backend/app/storage/*.py` | service | CRUD | `loadStoredPlans` in `src/main.jsx` | partial |
| backend fake publisher, e.g. `backend/app/publishing/fake_publisher.py` | service | event-driven | `approvePlan`, `exportPackage` in `src/main.jsx` | partial |
| backend diagnostics/redaction, e.g. `backend/app/diagnostics/*.py` | service/utility | transform | none | no analog |
| backend tests, e.g. `backend/tests/*` | test | CRUD/event-driven | none | no analog |
| `src/api/publishingClient.js` | service | request-response | `scripts/package-sites.mjs` validation/error style | partial |
| `src/models/publishing.js` | model | transform | `normalizeCampaignInput`, `buildPlansFromInput`, `normalizePlan` | exact role |
| `src/routes/AppRoutes.jsx` or route module | route | request-response | `App` route tree in `src/main.jsx` | exact role |
| `src/components/AppShell.jsx` | component | request-response UI state | `AppDemo` shell JSX in `src/main.jsx` | exact role |
| `src/components/ApprovalSnapshot.jsx` | component | request-response | channel detail + approval queue in `src/main.jsx` | role-match |
| `src/components/PublishTimeline.jsx` | component | event-driven display | calendar selected post/status patterns in `src/main.jsx` | role-match |
| `src/components/RetryPublishControl.jsx` | component | event-driven | approval buttons/toasts in `src/main.jsx` | role-match |
| `src/routes/DebugRoute.jsx` | component/route | request-response | `AppDemo` panels + insights panel in `src/main.jsx` | role-match |
| `src/publishing/workflow.js` | utility/service | event-driven transform | `createInitialPlans`, `approvePlan`, `regeneratePlan` | role-match |
| `src/storage/preferences.js` | utility | file-I/O/browser storage | `LanguageProvider`, `loadStoredPlans`, AppDemo effects | exact role |
| `src/styles.css` | config/component styles | request-response UI | existing app CSS groups | exact |
| build/package scripts if backend output is added | config | file-I/O | `scripts/prepare-sites-dist.mjs`, `scripts/package-sites.mjs` | exact role |

## Pattern Assignments

### Backend API Boundary (config/route/controller, request-response)

**Analog:** No backend analog exists. Use project style from Node ESM scripts and keep the backend deliberately isolated.

**Import/config pattern** (`scripts/prepare-sites-dist.mjs` lines 1-8):
```javascript
import { copyFile, mkdir, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(root, "dist");
const serverDir = join(dist, "server");
const openAiDir = join(dist, ".openai");
```

**Route contract source:** create `/api/v1` endpoints from `01-RESEARCH.md`: campaigns, drafts, approve, publish, retry, job detail, and debug publish jobs. There is no Express/FastAPI pattern in this repo; planner should create a backend scaffold and tests before wiring UI.

**Error handling pattern** (`scripts/package-sites.mjs` lines 16-18, 24-32, 35-38):
```javascript
await Promise.all(requiredFiles.map((file) => access(file)));
await mkdir(dirname(archivePath), { recursive: true });

tar.on("error", reject);
tar.on("close", (code) => {
  if (code === 0) {
    resolve();
    return;
  }

  reject(new Error(`tar exited with code ${code}`));
});

const archive = await stat(archivePath);
if (archive.size === 0) {
  throw new Error(`Archive was created but is empty: ${archivePath}`);
}
```

### Backend Publishing Models And Schemas (model, CRUD/event-driven)

**Analog:** `src/main.jsx` channel/campaign objects.

**Campaign input fields** (`src/main.jsx` lines 1572-1585):
```javascript
const normalizeCampaignInput = (input = defaultCampaignInput) => {
  const inferredType = input?.businessType && businessTemplates[input.businessType]
    ? input.businessType
    : inferBusinessType(input?.business);
  const template = businessTemplates[inferredType] || businessTemplates[defaultCampaignInput.businessType];

  return {
    business: input?.business || template.business,
    businessType: inferredType,
    offer: input?.offer || template.offer,
    goal: input?.goal || template.goal,
    audience: input?.audience || template.audience,
  };
};
```

**Platform draft seed shape** (`src/main.jsx` lines 1443-1467):
```javascript
const channelPlans = [
  {
    name: "TikTok",
    role: "Demand capture through a fast local hook",
    format: "22s vertical video",
    tone: "green",
    asset: restaurant,
    postAngle: "Owner-led short video with a fast before/after payoff and a clear local offer.",
    publishingMode: "Schedule video after owner approval",
    scheduleSlot: "Monday 9:00 AM",
    assets: ["22s vertical cut", "cover text", "coupon code", "first comment"],
    trackingEvents: ["coupon scan", "profile tap", "map click"],
    riskNote: "Keep claim simple and make the offer window visible in the first caption line.",
    nativeCreative: {
      hook: "POV: your weekday lunch break finally got upgraded.",
      caption: "Fresh plate, fast service, and a lunch special worth saving. Show this post at checkout today.",
      cover: "Lunch under 15 minutes",
      cta: "Show coupon in-store",
    },
    kpi: "Coupon scans + map clicks",
    ownerAction: "Approve video cut and coupon wording",
    checklist: ["Hook in first 2 seconds", "Owner voiceover approved", "Coupon code attached"],
  },
];
```

**Planner note:** backend schema must extend this UI shape with immutable draft versions, approval snapshot, connected-channel placeholder, provider payload, disclosure/settings placeholder, approver, timestamps, idempotency key, jobs, attempts, and events.

### Backend Repository/Seed Data (service, CRUD)

**Analog:** browser persistence helpers in `src/main.jsx`.

**Safe read/default pattern** (`src/main.jsx` lines 1657-1665):
```javascript
const loadStoredPlans = (input = defaultCampaignInput) => {
  try {
    const stored = JSON.parse(window.localStorage.getItem("localpilot-demo-plans") || "null");
    return Array.isArray(stored) && stored.length
      ? stored.map((plan, index) => normalizePlan(plan, index, input))
      : createInitialPlans(input);
  } catch {
    return createInitialPlans(input);
  }
};
```

**Transform before persistence pattern** (`src/main.jsx` lines 1628-1655):
```javascript
const createInitialPlans = (input = defaultCampaignInput) =>
  buildPlansFromInput(input).map((plan) => ({
    ...plan,
    status: "Needs review",
    checklist: plan.checklist.map((item) =>
      typeof item === "string" ? { text: item, done: false } : { ...item, done: false },
    ),
  }));

const normalizePlan = (plan, index, input = defaultCampaignInput) => {
  const base = buildPlansFromInput(input)[index] || buildPlansFromInput(input)[0];
  return {
    ...base,
    ...plan,
    nativeCreative: {
      ...base.nativeCreative,
      ...(plan?.nativeCreative || {}),
    },
    status: plan?.status || "Needs review",
  };
};
```

### Fake Publishing Lifecycle (service, event-driven)

**Analog:** local approval/export handlers in `AppDemo`; these are behavioral analogs only and must be replaced by backend events.

**Current local mutation pattern** (`src/main.jsx` lines 2264-2307):
```javascript
const updatePlan = (index, updater) => {
  setPlans((currentPlans) =>
    currentPlans.map((plan, planIndex) => (planIndex === index ? updater(plan) : plan)),
  );
};

const approvePlan = (index) => {
  updatePlan(index, (plan) => ({ ...plan, status: "Approved" }));
  showAppToast(`${plans[index].name} approved.`);
};

const exportPackage = () => {
  const payload = {
    campaignInput,
    plans,
    packageReadiness,
    approvedCount,
    checklistDone,
    exportedAt: new Date().toISOString(),
  };
  window.localStorage.setItem("localpilot-export-package", JSON.stringify(payload));
  showAppToast("Ready-to-post package saved locally.");
};
```

**Planner note:** copy the update-by-id shape, but backend service must append attempts/events rather than overwrite history. Every retry creates a new attempt and uses idempotency tied to approved version and channel target.

### Frontend API Client (service, request-response)

**Analog:** no network API client exists. Follow repo JavaScript style and defensive failure style from scripts.

**Package script validation pattern** (`scripts/package-sites.mjs` lines 10-17):
```javascript
const requiredFiles = [
  join(dist, "server", "index.js"),
  join(dist, "client", "index.html"),
  join(dist, ".openai", "hosting.json"),
];

await Promise.all(requiredFiles.map((file) => access(file)));
await mkdir(dirname(archivePath), { recursive: true });
```

**Apply to:** `src/api/publishingClient.js`. Use plain exported async functions, relative API URLs, JSON parsing, explicit error messages, and no token/secret storage in browser code.

### Frontend Models (model/utility, transform)

**Analog:** `src/main.jsx` plan builders.

**Build backend-compatible drafts from campaign input** (`src/main.jsx` lines 1587-1625):
```javascript
const buildPlansFromInput = (input = defaultCampaignInput) => {
  const normalizedInput = normalizeCampaignInput(input);
  const template = businessTemplates[normalizedInput.businessType] || businessTemplates.restaurant;

  return channelPlans.map((plan) => {
    const [hook, cta, kpi] = template.byChannel[plan.name] || template.byChannel.TikTok;
    const isRed = plan.name === "Xiaohongshu";
    const isGoogle = plan.name === "Google Local";

    return {
      ...plan,
      kpi,
      nativeCreative: {
        ...plan.nativeCreative,
        hook,
        caption: isRed
          ? `${normalizedInput.offer}，适合${template.label}客户收藏和咨询。关键词: 本地推荐 / ${normalizedInput.business}`
          : `${normalizedInput.business} is promoting ${normalizedInput.offer}. Built to ${normalizedInput.goal}.`,
        cover: isRed ? `${template.label}推荐` : isGoogle ? `${normalizedInput.offer} near me` : normalizedInput.offer,
        cta,
      },
      status: "Needs review",
    };
  });
};
```

**Apply to:** `src/models/publishing.js` and `src/publishing/workflow.js`. Preserve camelCase, plain objects, and safe defaults; add explicit version/status fields that mirror backend contracts.

### Router And Hidden Debug Route (route, request-response)

**Analog:** `App` route tree in `src/main.jsx`.

**Route pattern** (`src/main.jsx` lines 2964-2975):
```jsx
function App() {
  return (
    <LanguageProvider>
      <TranslationLayer />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/app" element={<AppDemo />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </LanguageProvider>
  );
}
```

**Apply to:** add `/app/debug` as a direct-URL route. Keep it outside `modules` and the normal sidebar nav.

### App Shell And Workspace Components (component, request-response)

**Analog:** `AppDemo` shell.

**Shell/navigation pattern** (`src/main.jsx` lines 2344-2372):
```jsx
return (
  <div className="app-shell">
    <aside className="app-sidebar" aria-label="App navigation">
      <Link className="app-brand" to="/">
        <Brand />
      </Link>
      <div className="workspace-switcher">
        <span>Workspace</span>
        <strong>{session?.workspace || "Northstar Local Growth"}</strong>
        <small>8 client locations</small>
      </div>
      <nav className="app-nav" aria-label="Demo sections">
        {modules.map((module) => (
          <button
            className={`app-nav-item ${activeModule === module ? "active" : ""}`}
            type="button"
            key={module}
            onClick={() => selectModule(module)}
          >
            {module}
          </button>
        ))}
      </nav>
    </aside>
```

**Topbar action pattern** (`src/main.jsx` lines 2374-2407):
```jsx
<main className="app-main">
  <header className="app-topbar">
    <div>
      <p className="app-kicker">Agency demo workspace</p>
      <h1>{config.title}</h1>
      {config.summary && <p className="topbar-summary">{config.summary}</p>}
    </div>
    <div className="topbar-actions">
      <LanguageToggle compact />
      <button className="primary-action" type="button" onClick={topbarPrimaryAction.handler}>
        {topbarPrimaryAction.label}
      </button>
      <button className="secondary-action" type="button" onClick={topbarSecondaryAction.handler}>
        {topbarSecondaryAction.label}
      </button>
    </div>
  </header>
```

### Approval Snapshot And Draft Detail (component, request-response)

**Analog:** channel detail and approval queue.

**Selected platform pattern** (`src/main.jsx` lines 2497-2537):
```jsx
<div className="channel-tabs" role="tablist" aria-label="Channel plans">
  {plans.map((plan, index) => (
    <button
      className={safeSelectedChannel === index ? "active" : ""}
      type="button"
      role="tab"
      aria-selected={safeSelectedChannel === index}
      key={plan.name}
      onClick={() => setSelectedChannel(index)}
    >
      <span>{plan.name}</span>
      <small>{plan.kpi}</small>
      <em>{plan.status}</em>
    </button>
  ))}
</div>

<section className={`channel-breakdown ${channel.tone}`}>
  <div className="channel-heading">
    <div>
      <span>{channel.format}</span>
      <h3>{channel.name}: {channel.role}</h3>
    </div>
    <button className="primary-action" type="button" onClick={() => approvePlan(safeSelectedChannel)}>
      {channel.status === "Approved" ? "Approved" : "Approve plan"}
    </button>
```

**Metadata grid pattern** (`src/main.jsx` lines 2539-2584):
```jsx
<dl className="creative-spec">
  <div>
    <dt>Post angle</dt>
    <dd>{channel.postAngle}</dd>
  </div>
  <div>
    <dt>Caption</dt>
    <dd>{channel.nativeCreative.caption}</dd>
  </div>
  <div>
    <dt>CTA</dt>
    <dd>{channel.nativeCreative.cta}</dd>
  </div>
</dl>

<div className="delivery-meta-grid">
  <article>
    <span>Publishing mode</span>
    <strong>{channel.publishingMode}</strong>
    <small>{channel.scheduleSlot}</small>
  </article>
</div>
```

**Apply to:** `ApprovalSnapshot.jsx`. Add immutable fields from UI-SPEC: platform, draft version, approver, approved timestamp, idempotency suffix, target placeholder, caption/body, CTA, media refs, provider payload summary, disclosure/settings placeholder.

### Status Timeline And Retry UI (component, event-driven)

**Analog:** calendar selected post + status pill.

**Selected status/action pattern** (`src/main.jsx` lines 2700-2724):
```jsx
<article className="selected-post selected-post--calendar">
  <div className="selected-post-copy">
    <span className="status-pill">{selectedPlan.status}</span>
    <h3>
      {selectedPlan.name}: {selectedPlan.publishingMode}
    </h3>
    <p>{selectedPlan.nativeCreative.caption}</p>
    <div className="calendar-actions">
      <button type="button" onClick={() => approvePlan(safeSelectedPost)}>
        Approve slot
      </button>
      <button type="button" onClick={() => requestChanges(safeSelectedPost)}>
        Request edit
      </button>
    </div>
    <div className="selected-checklist">
      <span>Before publishing</span>
```

**Apply to:** `PublishTimeline.jsx` and `RetryPublishControl.jsx`. Use stable rows/steps, append events, disable only affected controls during API writes, and show `Retry publish` only for `failed` or `retry_needed`.

### Hidden Debug Route (component/route, request-response)

**Analog:** insights panel and approval list.

**Panel/list pattern** (`src/main.jsx` lines 2887-2940):
```jsx
<aside className="insights-panel" aria-label="Insights and approvals">
  <section className="insight-card readiness-card">
    <div className="panel-head compact-head">
      <h2>Package readiness</h2>
      <span>{packageReadiness}%</span>
    </div>
  </section>
  <section className="insight-card">
    <div className="panel-head compact-head">
      <h2>Approval queue</h2>
      <span>{pendingPlans.length} pending</span>
    </div>
    <div className="approval-list">
      {plans.map((plan, index) =>
        plan.status === "Approved" ? null : (
          <article key={plan.name}>
            <strong>{plan.name} plan</strong>
            <small>{plan.status} · KPI: {plan.kpi}</small>
            <button type="button" onClick={() => approvePlan(index)}>
              Approve
            </button>
          </article>
        ),
      )}
    </div>
  </section>
</aside>
```

**Apply to:** `/app/debug` operations table plus detail panel. Add class prefix `.debug-jobs-*`; show trace IDs, error classes, redacted diagnostics, next action, timestamps, approver, draft version.

### Preference Storage (utility, browser file-I/O)

**Analog:** language and selected-index localStorage.

**Guarded preference read/write** (`src/main.jsx` lines 932-957):
```javascript
function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    try {
      return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) || "en";
    } catch {
      return "en";
    }
  });

  useEffect(() => {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    try {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    } catch {
      // Local persistence is a convenience for the demo, not a hard requirement.
    }
  }, [language]);
}
```

**Allowed Phase 1 localStorage pattern** (`src/main.jsx` lines 2200-2218):
```javascript
useEffect(() => {
  window.localStorage.setItem("localpilot-demo-active-module", moduleSlug(activeModule));
}, [activeModule]);

useEffect(() => {
  window.localStorage.setItem("localpilot-demo-selected-channel", String(safeSelectedChannel));
}, [safeSelectedChannel]);

useEffect(() => {
  window.localStorage.setItem("localpilot-demo-selected-post", String(safeSelectedPost));
}, [safeSelectedPost]);
```

**Planner note:** keep only language/module/selection preferences. Remove or ignore publish-critical localStorage keys: `localpilot-demo-input`, `localpilot-demo-plans`, and `localpilot-export-package`.

### Styles For New Workflow UI (component styles, request-response)

**Analog:** app CSS tokens, panels, controls, channel/status classes.

**Token pattern** (`src/styles.css` lines 1-18):
```css
:root {
  --ink: #111827;
  --muted: #5f6977;
  --soft: #f2f0ea;
  --line: rgba(17, 24, 39, 0.11);
  --green: #15825c;
  --green-dark: #0f6648;
  --coral: #d86f3d;
  --blue: #3258d8;
  --red: #c84b45;
  --paper: #ffffff;
  --wash: #f7f3eb;
  --shadow: 0 18px 48px rgba(17, 24, 39, 0.11);
}
```

**App shell/control pattern** (`src/styles.css` lines 1108-1129, 1285-1323):
```css
.app-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  min-height: 100vh;
  overflow-x: hidden;
}

.app-sidebar {
  position: sticky;
  top: 0;
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  gap: 18px;
  height: 100vh;
  padding: 22px;
}

.primary-action,
.secondary-action,
.icon-action {
  min-height: 42px;
  border-radius: 10px;
  font-weight: 760;
  padding: 0 16px;
}
```

**Status/tab pattern** (`src/styles.css` lines 1562-1608, 1905-1957):
```css
.channel-tabs {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.channel-tabs button.active {
  border-color: rgba(21, 130, 92, 0.4);
  background: #e7f3ed;
  box-shadow: inset 0 0 0 1px rgba(21, 130, 92, 0.18);
}

.status-pill {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 8px 10px;
  background: #e1f3ea;
  color: var(--green-dark);
  font-size: 12px;
  font-weight: 780;
}
```

**Responsive pattern** (`src/styles.css` lines 2422-2495, 2621-2697):
```css
@media (max-width: 1320px) {
  .app-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1180px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .app-sidebar {
    position: static;
    height: auto;
    grid-template-rows: auto;
  }
}

@media (max-width: 640px) {
  .channel-tabs,
  .campaign-builder,
  .delivery-meta-grid,
  .insights-panel {
    grid-template-columns: 1fr;
  }
}
```

### Build And Package Integration (config, file-I/O)

**Analog:** existing Node scripts.

**Generated worker pattern** (`scripts/prepare-sites-dist.mjs` lines 10-43):
```javascript
const workerSource = `const fallbackToIndex = async (request, env) => {
  const url = new URL(request.url);
  url.pathname = "/index.html";
  url.search = "";
  return env.ASSETS.fetch(new Request(url, request));
};

export default {
  async fetch(request, env) {
    if (!env.ASSETS) {
      return new Response("Static assets binding is not configured.", { status: 500 });
    }
  },
};
`;

await rm(join(dist, "assets"), { recursive: true, force: true });
await mkdir(serverDir, { recursive: true });
await writeFile(join(serverDir, "index.js"), workerSource);
await copyFile(join(root, ".openai", "hosting.json"), join(openAiDir, "hosting.json"));
```

**Apply to:** if Phase 1 changes dev/build commands, preserve `npm run build` and `npm run package:sites` behavior. Add backend commands without breaking static packaging.

## Shared Patterns

### Imports And Module Style
**Source:** `src/main.jsx` lines 1-10; `scripts/*.mjs` lines 1-4  
**Apply to:** all frontend and Node files  
Use package imports first, relative CSS/assets after, no aliases unless explicitly configured.

### User-Visible Status
**Source:** `src/main.jsx` lines 2220-2223 and `src/styles.css` lines 1094-1105  
**Apply to:** approval, fake publish, retry, reload actions  
Use `showAppToast(message)` for success feedback; use inline panels for API failures per UI-SPEC.

### LocalStorage Boundary
**Source:** `src/main.jsx` lines 932-957 and 2185-2218  
**Apply to:** `src/storage/preferences.js`, App workflow migration  
Keep preference writes guarded and focused. Do not store publish-critical records, tokens, OAuth payloads, credentials, attempts, jobs, diagnostics, or approval snapshots in browser localStorage.

### Route Visibility
**Source:** `src/main.jsx` lines 1023-1036 and 2969-2972  
**Apply to:** `/app/debug`  
Do not add debug/admin to `modules`; route it directly in router only.

### Redaction/Security
**Source:** no code analog; phase requirements and UI-SPEC  
**Apply to:** backend diagnostics endpoint and debug UI  
Only expose trace IDs, statuses, error classes, redacted provider diagnostics, next action, timestamps, approver, and draft version. Never expose tokens, cookies, OAuth payloads, authorization headers, app secrets, refresh tokens, or raw provider credentials.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| backend app/routes/controllers | route/controller | request-response CRUD | Repo is frontend-only; no backend server or API routes exist. |
| backend database models/migrations | model/migration | CRUD | No database, ORM, migration tool, or persistence layer exists. |
| backend fake publishing adapter | service | event-driven | Current approval is local state only; no jobs/attempts/events. |
| backend diagnostics/redaction | service/utility | transform | No diagnostics or redaction utilities exist. |
| backend lifecycle/idempotency tests | test | event-driven/CRUD | No test framework or tests exist. |
| frontend API client | service | request-response | No browser `fetch` API client exists. |

## Metadata

**Analog search scope:** `src/main.jsx`, `src/styles.css`, `package.json`, `scripts/*.mjs`, `.planning/codebase/*.md`, phase artifacts  
**Files scanned:** 12 required files plus `AGENTS.md` and project skill directories  
**Pattern extraction date:** 2026-06-10
