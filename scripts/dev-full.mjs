import { spawn } from "node:child_process";

const apiPort = "8787";
const apiUrl = `http://127.0.0.1:${apiPort}`;
const webUrl = "http://127.0.0.1:5173";

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

console.log(`LocalPilot API: ${apiUrl}/api/v1/health`);
console.log(`LocalPilot web: ${webUrl}/`);

start("api", "python3", [
  "-m",
  "backend.app.server",
  "--port",
  apiPort,
  "--db",
  ".localpilot-dev/backend.sqlite",
]);

start("web", "npm", ["run", "dev:web", "--", "--port", "5173"]);
