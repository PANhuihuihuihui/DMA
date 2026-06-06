import { copyFile, mkdir, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(root, "dist");
const serverDir = join(dist, "server");
const openAiDir = join(dist, ".openai");

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

    const response = await env.ASSETS.fetch(request);
    if (response.status !== 404) {
      return response;
    }

    const accept = request.headers.get("accept") || "";
    if (accept.includes("text/html")) {
      return fallbackToIndex(request, env);
    }

    return response;
  },
};
`;

await rm(join(dist, "assets"), { recursive: true, force: true });
await rm(join(dist, "index.html"), { force: true });
await mkdir(serverDir, { recursive: true });
await mkdir(openAiDir, { recursive: true });
await writeFile(join(serverDir, "index.js"), workerSource);
await copyFile(join(root, ".openai", "hosting.json"), join(openAiDir, "hosting.json"));
