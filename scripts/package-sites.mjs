import { access, mkdir, stat } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(root, "dist");
const archivePath = process.env.SITES_ARCHIVE_PATH || "/tmp/localpilot-ai-karen-demo-sites.tar.gz";

const requiredFiles = [
  join(dist, "server", "index.js"),
  join(dist, "client", "index.html"),
  join(dist, ".openai", "hosting.json"),
];

await Promise.all(requiredFiles.map((file) => access(file)));
await mkdir(dirname(archivePath), { recursive: true });

await new Promise((resolve, reject) => {
  const tar = spawn("tar", ["-C", root, "-czf", archivePath, "dist"], {
    stdio: "inherit",
  });

  tar.on("error", reject);
  tar.on("close", (code) => {
    if (code === 0) {
      resolve();
      return;
    }

    reject(new Error(`tar exited with code ${code}`));
  });
});

const archive = await stat(archivePath);
if (archive.size === 0) {
  throw new Error(`Archive was created but is empty: ${archivePath}`);
}

console.log(`Sites archive ready: ${archivePath} (${Math.round(archive.size / 1024 / 1024)} MB)`);
