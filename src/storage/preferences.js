const ALLOWED_KEYS = new Set([
  "localpilot-language",
  "localpilot-demo-session",
  "localpilot-demo-active-module",
  "localpilot-demo-selected-channel",
  "localpilot-demo-selected-post",
  "localpilot-demo-selected-inbox",
  "localpilot-demo-selected-walkthrough",
]);

const DEMO_WORKSPACE_PREFERENCE_KEYS = [
  "localpilot-demo-active-module",
  "localpilot-demo-selected-channel",
  "localpilot-demo-selected-post",
  "localpilot-demo-selected-inbox",
  "localpilot-demo-selected-walkthrough",
];

const canUseStorage = () => typeof window !== "undefined" && Boolean(window.localStorage);

const assertAllowedPreference = (key) => {
  if (!ALLOWED_KEYS.has(key)) {
    throw new Error(`Unsupported LocalPilot preference key: ${key}`);
  }
};

export const readPreference = (key, fallback = null) => {
  assertAllowedPreference(key);
  if (!canUseStorage()) {
    return fallback;
  }

  try {
    const value = window.localStorage.getItem(key);
    return value === null ? fallback : value;
  } catch {
    return fallback;
  }
};

export const writePreference = (key, value) => {
  assertAllowedPreference(key);
  if (!canUseStorage()) {
    return false;
  }

  try {
    if (value === null || value === undefined) {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, String(value));
    }
    return true;
  } catch {
    return false;
  }
};

export const clearDemoWorkspacePreferences = () => {
  DEMO_WORKSPACE_PREFERENCE_KEYS.forEach((key) => writePreference(key, null));
};
