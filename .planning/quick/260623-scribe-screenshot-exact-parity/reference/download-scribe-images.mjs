import fs from "node:fs";
import path from "node:path";
import https from "node:https";
import { URL } from "node:url";

const root = path.resolve(
  ".planning/quick/260623-scribe-screenshot-exact-parity/reference",
);
const htmlPath = "/tmp/localpilot-scribe-workflow.html";
const stepsDir = path.join(root, "steps");

fs.mkdirSync(stepsDir, { recursive: true });

const html = fs.readFileSync(htmlPath, "utf8");

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
          Accept: "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
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
          const nextUrl = new URL(res.headers.location, url).toString();
          resolve(request(nextUrl, redirects + 1));
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

function extensionFor(contentType, src) {
  if (contentType.includes("png")) return "png";
  if (contentType.includes("jpeg") || contentType.includes("jpg")) return "jpg";
  if (contentType.includes("webp")) return "webp";
  if (contentType.includes("gif")) return "gif";
  const ext = path.extname(new URL(src).pathname).replace(".", "");
  return ext || "png";
}

const stepPattern =
  /<div data-testid="action-instruction"[\s\S]*?<span[^>]*>(\d+)<\/span>[\s\S]*?<div class="text-sm text-slate-900">([\s\S]*?)<\/div>[\s\S]*?<img src="([^"]+)/g;

const parsedSteps = [];
let match;
while ((match = stepPattern.exec(html))) {
  const [, number, instructionHtml, src] = match;
  parsedSteps.push({
    number: Number(number),
    instruction: stripTags(instructionHtml),
    src: decodeEntities(src),
  });
}

const seenStepNumbers = new Set();
const steps = parsedSteps.filter((step) => {
  if (seenStepNumbers.has(step.number)) return false;
  seenStepNumbers.add(step.number);
  return true;
});

if (steps.length === 0) {
  throw new Error("No Scribe steps found in downloaded HTML.");
}

for (const step of steps) {
  const response = await request(step.src);
  const ext = extensionFor(response.contentType, step.src);
  const fileName = `step-${String(step.number).padStart(2, "0")}.${ext}`;
  const filePath = path.join(stepsDir, fileName);
  fs.writeFileSync(filePath, response.body);
  step.file = `steps/${fileName}`;
  step.contentType = response.contentType;
  step.bytes = response.body.length;
}

const workflowMap = [
  "1. Open Create New.",
  "2. Choose the creator-style video format.",
  "3. Describe the video or generate ideas from a goal.",
  "4. Continue into an idea selection screen.",
  "5. Choose Motivational as the style.",
  "6. Pick an AI actor.",
  "7. Pick a scene/template.",
  "8. Review and generate.",
  "9. Open generated creative output.",
  "10. Publish or schedule the post.",
];

fs.writeFileSync(
  path.join(root, "steps.json"),
  `${JSON.stringify({ source: htmlPath, steps }, null, 2)}\n`,
);

fs.writeFileSync(
  path.join(root, "steps.md"),
  [
    "# Scribe Reference Steps",
    "",
    ...steps.map(
      (step) =>
        `## Step ${step.number}\n\n${step.instruction}\n\nImage: ${step.file}\n`,
    ),
    "## Product Workflow Map",
    "",
    ...workflowMap,
    "",
  ].join("\n"),
);

const cards = steps
  .map(
    (step) => `
      <article class="step-card">
        <div class="step-header">
          <span>Step ${step.number}</span>
          <strong>${step.instruction}</strong>
        </div>
        <img src="./${step.file}" alt="Scribe step ${step.number}" />
      </article>
    `,
  )
  .join("\n");

fs.writeFileSync(
  path.join(root, "contact-sheet.html"),
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

      body {
        margin: 0;
        padding: 36px;
      }

      h1 {
        margin: 0 0 8px;
        font-size: 34px;
        letter-spacing: -0.04em;
      }

      .meta {
        color: #657086;
        margin-bottom: 28px;
      }

      .grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 22px;
      }

      .step-card {
        background: white;
        border: 1px solid #dfe4ee;
        border-radius: 20px;
        box-shadow: 0 18px 42px rgba(28, 37, 64, 0.12);
        overflow: hidden;
      }

      .step-header {
        display: grid;
        grid-template-columns: 76px 1fr;
        gap: 14px;
        align-items: start;
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

      .step-header strong {
        font-size: 14px;
        line-height: 1.35;
      }

      img {
        display: block;
        width: 100%;
        height: auto;
        background: #f4f6f9;
      }
    </style>
  </head>
  <body>
    <h1>Scribe Reference Contact Sheet</h1>
    <div class="meta">${steps.length} extracted workflow screenshots from the supplied Scribe page.</div>
    <main class="grid">
      ${cards}
    </main>
  </body>
</html>
`,
);

console.log(`Extracted ${steps.length} Scribe reference screenshots to ${stepsDir}`);
