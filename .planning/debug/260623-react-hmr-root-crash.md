---
debug_id: 260623-react-hmr-root-crash
status: resolved
created: 2026-06-23
---

# React HMR Root Crash

## Symptom

- Browser warning: `You are calling ReactDOMClient.createRoot() on a container that has already been passed to createRoot() before.`
- Runtime crash: `NotFoundError: Failed to execute 'removeChild' on 'Node': The node to be removed is not a child of this node.`
- Vite CSS hot reload reports failed reload after the crash.

## Initial Hypothesis

- `src/main.jsx` calls `createRoot(document.getElementById("root"))` at module scope every time Vite re-evaluates the module.
- The imperative `TranslationLayer` mutates text nodes under `#root`, which can amplify HMR/delete reconciliation failures if the root is recreated.

## Fix Plan

- Reuse a single React root during Vite HMR.
- Preserve the root through HMR dispose instead of unmounting during a hot update.
- Run build and browser smoke after the patch.

## Resolution

- Added a guarded React root bootstrap in `src/main.jsx`.
- Stores the React root on the `#root` DOM element and in `import.meta.hot.data`.
- Vite HMR dispose now carries the existing root into the next module evaluation instead of unmounting it mid-update.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.

## Recurrence - 2026-06-23

- User reported the same duplicate `createRoot()` warning plus `removeChild` crash during Vite reload.
- Additional root cause found: `src/routes/AppRoutes.jsx` imports `AppDemo` and `LandingPage` back from `../main.jsx`, while `main.jsx` imports `AppRoutes`, creating a circular entrypoint dependency.
- Fix plan: make routes receive page elements from `main.jsx` and store the React root in a `window` WeakMap in addition to HMR data and DOM expando state.

## Recurrence Resolution

- Removed the `AppRoutes.jsx` import from `../main.jsx`; route elements are now passed from the entrypoint.
- Added a browser-global `WeakMap` root registry so Vite HMR reuses the existing React root even when module hot data is unavailable.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- `PATH=/opt/homebrew/bin:$PATH npm run build` passed.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed with no browser console errors or page errors.
