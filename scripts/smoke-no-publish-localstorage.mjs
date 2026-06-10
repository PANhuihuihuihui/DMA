import { readdir, readFile } from "node:fs/promises";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(fileURLToPath(import.meta.url), "..", "..");
const sourceRoot = join(root, "src");
const preferenceBoundary = "src/storage/preferences.js";

const allowedPreferenceKeys = new Set([
  "localpilot-language",
  "localpilot-demo-session",
  "localpilot-demo-active-module",
  "localpilot-demo-selected-channel",
  "localpilot-demo-selected-post",
  "localpilot-demo-selected-inbox",
  "localpilot-demo-selected-walkthrough",
]);

const publishStorageKeys = [
  "localpilot-demo-input",
  "localpilot-demo-plans",
  "localpilot-export-package",
];

const splitTerm = (...parts) => parts.join("");
const splitPattern = (...parts) => parts.join("[_-]?");

const forbiddenWritePatterns = [
  { label: "approval snapshot", pattern: /approval[-_\s]?snapshot/i },
  { label: "media asset record", pattern: /media[-_\s]?(asset|ref|record)/i },
  { label: "publish job", pattern: /publish[-_\s]?job/i },
  { label: "publish attempt", pattern: /publish[-_\s]?attempt/i },
  { label: "publish event", pattern: /publish[-_\s]?event/i },
  { label: "diagnostics", pattern: /diagnostic/i },
  { label: "token boundary", pattern: /token[-_\s]?boundary/i },
  { label: "provider credential", pattern: new RegExp(splitPattern("cred", "ential"), "i") },
  { label: "provider token", pattern: new RegExp(splitPattern("provider", "token"), "i") },
  { label: "access token", pattern: new RegExp(splitPattern("access", "token"), "i") },
  { label: "refresh token", pattern: new RegExp(splitPattern("refresh", "token"), "i") },
  { label: "API key", pattern: new RegExp(splitPattern("api", "key"), "i") },
  { label: "client secret", pattern: new RegExp(splitPattern("client", "secret"), "i") },
  { label: "OAuth payload", pattern: new RegExp(splitPattern("oau", "th", "payload"), "i") },
  { label: "authorization header", pattern: new RegExp(splitTerm("author", "ization"), "i") },
  { label: "cookie payload", pattern: new RegExp(splitTerm("coo", "kie"), "i") },
  { label: "secret reference", pattern: /secret[-_\s]?ref/i },
  { label: "bearer value", pattern: /bearer/i },
];

const sourceExtensions = new Set([".js", ".jsx"]);

const stripComments = (source) => {
  let output = "";
  let state = "code";
  let escaped = false;

  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    const next = source[index + 1];

    if (state === "lineComment") {
      if (char === "\n") {
        state = "code";
        output += char;
      } else {
        output += " ";
      }
      continue;
    }

    if (state === "blockComment") {
      if (char === "*" && next === "/") {
        output += "  ";
        index += 1;
        state = "code";
      } else {
        output += char === "\n" ? "\n" : " ";
      }
      continue;
    }

    if (state === "single" || state === "double" || state === "template") {
      output += char;
      if (escaped) {
        escaped = false;
        continue;
      }
      if (char === "\\") {
        escaped = true;
        continue;
      }
      if (
        (state === "single" && char === "'") ||
        (state === "double" && char === "\"") ||
        (state === "template" && char === "`")
      ) {
        state = "code";
      }
      continue;
    }

    if (char === "/" && next === "/") {
      output += "  ";
      index += 1;
      state = "lineComment";
      continue;
    }

    if (char === "/" && next === "*") {
      output += "  ";
      index += 1;
      state = "blockComment";
      continue;
    }

    if (char === "'") {
      state = "single";
    } else if (char === "\"") {
      state = "double";
    } else if (char === "`") {
      state = "template";
    }

    output += char;
  }

  return output;
};

const walk = async (directory) => {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...await walk(fullPath));
    } else if (sourceExtensions.has(entry.name.slice(entry.name.lastIndexOf(".")))) {
      files.push(fullPath);
    }
  }

  return files;
};

const extractLine = (source, index) => source.slice(0, index).split("\n").length;

const firstStringArg = (args) => {
  const match = args.match(/^\s*["'`]([^"'`]+)["'`]/);
  return match?.[1] || "";
};

const findForbiddenPattern = (value) =>
  forbiddenWritePatterns.find(({ pattern }) => pattern.test(value)) || null;

const violations = [];
const sourceFiles = await walk(sourceRoot);

for (const file of sourceFiles) {
  const relativePath = relative(root, file);
  const source = await readFile(file, "utf8");
  const code = stripComments(source);
  const isPreferenceBoundary = relativePath === preferenceBoundary;

  for (const key of allowedPreferenceKeys) {
    if (isPreferenceBoundary && !code.includes(`"${key}"`)) {
      violations.push(`${relativePath}: allowed preference key missing from boundary: ${key}`);
    }
  }

  for (const key of publishStorageKeys) {
    if (isPreferenceBoundary && code.includes(key)) {
      violations.push(`${relativePath}: publish-critical key must not be allowlisted: ${key}`);
    }
  }

  const localStorageCall = /\b(?:window\s*\.\s*)?localStorage\s*\.\s*(getItem|setItem|removeItem|clear)\s*\(([^)]*)\)/g;
  let localStorageMatch = localStorageCall.exec(code);
  while (localStorageMatch) {
    const [, method, args] = localStorageMatch;
    const line = extractLine(code, localStorageMatch.index);
    if (!isPreferenceBoundary) {
      violations.push(`${relativePath}:${line}: direct localStorage.${method} must use the preference boundary`);
    }

    if (method !== "getItem") {
      const key = firstStringArg(args);
      const forbidden = findForbiddenPattern(args);
      if (publishStorageKeys.includes(key) || forbidden) {
        violations.push(
          `${relativePath}:${line}: forbidden browser storage write${forbidden ? ` (${forbidden.label})` : ""}`,
        );
      }
    }

    localStorageMatch = localStorageCall.exec(code);
  }

  const preferenceCall = /\b(readPreference|writePreference)\s*\(\s*(["'`])([^"'`]+)\2/g;
  let preferenceMatch = preferenceCall.exec(code);
  while (preferenceMatch) {
    const [, helper, , key] = preferenceMatch;
    const line = extractLine(code, preferenceMatch.index);
    const forbidden = findForbiddenPattern(key);
    if (!allowedPreferenceKeys.has(key)) {
      violations.push(`${relativePath}:${line}: ${helper} uses non-allowlisted key: ${key}`);
    }
    if (helper === "writePreference" && (publishStorageKeys.includes(key) || forbidden)) {
      violations.push(
        `${relativePath}:${line}: ${helper} writes forbidden publish-critical key${forbidden ? ` (${forbidden.label})` : ""}`,
      );
    }
    preferenceMatch = preferenceCall.exec(code);
  }
}

if (violations.length) {
  console.error("Browser storage boundary smoke failed:");
  violations.forEach((violation) => console.error(`- ${violation}`));
  process.exit(1);
}

console.log(
  `Browser storage boundary smoke passed: ${sourceFiles.length} frontend files scanned; only allowlisted preferences use localStorage.`,
);
