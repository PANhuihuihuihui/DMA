/**
 * dev-full.mjs — minimal LocalPilot dev orchestrator.
 *
 * Port selection:
 *   - API: 8790 (not 8787) to avoid clashing with headroom-ai on 8787.
 *   - Web: 5173 (Vite default).
 * Override via env: LOCALPILOT_API_PORT, LOCALPILOT_WEB_PORT.
 *
 * Differences from dev-safe.mjs:
 *   dev-full.mjs is a minimal pass-through. dev-safe.mjs adds pre-flight
 *   port reaping, readiness probes, and graceful shutdown. Use dev:safe.
 */
import { spawn } from "node:child_process";

const API_PORT = process.env.LOCALPILOT_API_PORT || "8790";
const WEB_PORT = process.env.LOCALPILOT_WEB_PORT || "5173";

const children = [];
let shuttingDown = false;

const start = (name, command, args) => {
  const child = spawn(command, args, {
    stdio: "inherit",
    env: process.env,
  });
  child.on("exit", (code, signal) => {
    if (!shuttingDown) {
      shuttingDown = true;
      console.error(`${name} exited with ${signal || code}`);
      stopAll();
      process.exit(code || 1);
    }
  });
  children.push(child);
  return child;
};

const stopAll = () => {
  for (const child of children) {
    if (!child.killed) {
      child.kill("SIGTERM");
    }
  }
};

process.on("SIGINT", () => {
  shuttingDown = true;
  stopAll();
});

process.on("SIGTERM", () => {
  shuttingDown = true;
  stopAll();
});

console.log(`LocalPilot API: http://127.0.0.1:${API_PORT}/api/v1/health`);
console.log(`LocalPilot web: http://127.0.0.1:${WEB_PORT}/`);

start("api", "python3", [
  "-m",
  "backend.app.server",
  "--port",
  API_PORT,
  "--db",
  ".localpilot-dev/backend.sqlite",
]);

start("web", "npm", ["run", "dev:web", "--", "--port", WEB_PORT]);
