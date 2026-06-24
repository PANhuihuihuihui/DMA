import fs from "node:fs";
import path from "node:path";
import https from "node:https";
import { URL } from "node:url";

const args = process.argv.slice(2);

function readArg(name, fallback = "") {
  const index = args.indexOf(name);
  if (index === -1) return fallback;
  return args[index + 1] || fallback;
}

function hasFlag(name) {
  return args.includes(name);
}

const sourceUrl = readArg("--url");
const htmlPath = readArg("--html");
const outDir = path.resolve(readArg("--out", ".planning/scribe-reference"));
const skipImages = hasFlag("--skip-images");

if (!sourceUrl && !htmlPath) {
  console.error("Usage: extract_scribe_contact_sheet.mjs (--url URL | --html FILE) --out DIR [--skip-images]");
  process.exit(2);
}

fs.mkdirSync(outDir, { recursive: true });
const stepsDir = path.join(outDir, "steps");
if (!skipImages) {
  fs.mkdirSync(stepsDir, { recursive: true });
}

function decodeEntities(value) {
  return value
    .replace(/&quot;/g, "\"")
    .replace(/&#x27;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\s+/g, " ")
    .trim();
}

function stripTags(value) {
  return decodeEntities(value.replace(/<[^>]*>/g, " "));
}

function request(url, redirects = 0) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const req = https.request(
      {
        hostname: parsed.hostname,
        path: `${parsed.pathname}${parsed.search}`,
        protocol: parsed.protocol,
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36",
          Accept: "*/*",
        },
      },
      (res) => {
        if (
          res.statusCode >= 300 &&
          res.statusCode < 400 &&
          res.headers.location &&
          redirects < 5
        ) {
          res.resume();
          resolve(request(new URL(res.headers.location, url).toString(), redirects + 1));
          return;
        }

        if (res.statusCode !== 200) {
          res.resume();
          reject(new Error(`HTTP ${res.statusCode} for ${url}`));
          return;
        }

        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          resolve({
            body: Buffer.concat(chunks),
            contentType: res.headers["content-type"] || "",
          });
        });
      },
    );
    req.on("error", reject);
    req.end();
  });
}

async function loadHtml() {
  if (htmlPath) {
    return fs.readFileSync(htmlPath, "utf8");
  }
  const response = await request(sourceUrl);
  const cachedPath = path.join(outDir, "source.html");
  fs.writeFileSync(cachedPath, response.body);
  return response.body.toString("utf8");
}

function extensionFor(contentType, src) {
  if (contentType.includes("png")) return "png";
  if (contentType.includes("jpeg") || contentType.includes("jpg")) return "jpg";
  if (contentType.includes("webp")) return "webp";
  if (contentType.includes("gif")) return "gif";
  const ext = path.extname(new URL(src).pathname).replace(".", "");
  return ext || "png";
}

function extractSteps(html) {
  const pattern =
    /<div data-testid="action-instruction"[\s\S]*?<span[^>]*>(\d+)<\/span>[\s\S]*?<div class="text-sm text-slate-900">([\s\S]*?)<\/div>[\s\S]*?<img src="([^"]+)/g;
  const parsed = [];
  let match;
  while ((match = pattern.exec(html))) {
    const [, number, instructionHtml, src] = match;
    parsed.push({
      number: Number(number),
      instruction: stripTags(instructionHtml),
      src: decodeEntities(src),
    });
  }

  const seen = new Set();
  return parsed.filter((step) => {
    if (seen.has(step.number)) return false;
    seen.add(step.number);
    return true;
  });
}

function writeMarkdown(steps) {
  fs.writeFileSync(
    path.join(outDir, "steps.md"),
    [
      "# Scribe Reference Steps",
      "",
      ...steps.map(
        (step) =>
          `## Step ${step.number}\n\n${step.instruction}\n\nImage: ${step.file || step.src}\n`,
      ),
      "",
    ].join("\n"),
  );
}

function writeContactSheet(steps) {
  const cards = steps
    .map(
      (step) => `
        <article class="step-card">
          <div class="step-header">
            <span>Step ${step.number}</span>
            <strong>${step.instruction}</strong>
          </div>
          <img src="${step.file ? `./${step.file}` : step.src}" alt="Scribe step ${step.number}" />
        </article>
      `,
    )
    .join("\n");

  fs.writeFileSync(
    path.join(outDir, "contact-sheet.html"),
    `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Scribe Reference Contact Sheet</title>
    <style>
      :root {
        color-scheme: light;
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #f6f7fb;
        color: #172033;
      }
      body { margin: 0; padding: 36px; }
      h1 { margin: 0 0 8px; font-size: 34px; letter-spacing: -0.04em; }
      .meta { color: #657086; margin-bottom: 28px; }
      .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px; }
      .step-card {
        overflow: hidden;
        border: 1px solid #dfe4ee;
        border-radius: 20px;
        background: white;
        box-shadow: 0 18px 42px rgba(28, 37, 64, 0.12);
      }
      .step-header {
        display: grid;
        grid-template-columns: 76px 1fr;
        gap: 14px;
        padding: 16px 18px;
        border-bottom: 1px solid #edf0f6;
      }
      .step-header span {
        border-radius: 999px;
        background: #eaf1ff;
        color: #24457c;
        font-size: 12px;
        font-weight: 800;
        padding: 7px 10px;
        text-align: center;
      }
      .step-header strong { font-size: 14px; line-height: 1.35; }
      img { display: block; width: 100%; height: auto; background: #f4f6f9; }
    </style>
  </head>
  <body>
    <h1>Scribe Reference Contact Sheet</h1>
    <div class="meta">${steps.length} unique extracted workflow screenshots.</div>
    <main class="grid">${cards}</main>
  </body>
</html>
`,
  );
}

const html = await loadHtml();
const steps = extractSteps(html);
if (!steps.length) {
  throw new Error("No Scribe steps found. The Scribe page markup may have changed.");
}

for (const step of steps) {
  if (skipImages) {
    continue;
  }
  const response = await request(step.src);
  const ext = extensionFor(response.contentType, step.src);
  const fileName = `step-${String(step.number).padStart(2, "0")}.${ext}`;
  fs.writeFileSync(path.join(stepsDir, fileName), response.body);
  step.file = `steps/${fileName}`;
  step.contentType = response.contentType;
  step.bytes = response.body.length;
}

fs.writeFileSync(
  path.join(outDir, "steps.json"),
  `${JSON.stringify({ sourceUrl, htmlPath, steps }, null, 2)}\n`,
);
writeMarkdown(steps);
writeContactSheet(steps);

console.log(JSON.stringify({ ok: true, steps: steps.length, outDir }, null, 2));
