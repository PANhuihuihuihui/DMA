import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn } from "node:child_process";

const forbiddenTerms = [
  "access" + "_token",
  "refresh" + "_token",
  "author" + "ization",
  "coo" + "kie",
  "client" + "_secret",
  "api" + "_key",
  "oauth" + "_payload",
  "provider" + "_raw",
  "facebook.com",
  "graph.facebook.com",
  "tiktok.com",
  "postiz",
  "browser_session",
  "selenium",
];

const assertNoForbiddenTerms = (label, payload) => {
  const rendered = JSON.stringify(payload).toLowerCase();
  const found = forbiddenTerms.filter((term) => rendered.includes(term));
  if (found.length) {
    throw new Error(`${label} exposed forbidden terms: ${found.join(", ")}`);
  }
};

const waitForHealth = async (baseUrl, attempts = 40) => {
  for (let index = 0; index < attempts; index += 1) {
    try {
      const response = await fetch(`${baseUrl}/api/v1/health`);
      if (response.ok) {
        return response.json();
      }
    } catch {
      // Server startup is expected to take a short moment.
    }
    await new Promise((resolve) => setTimeout(resolve, 125));
  }
  throw new Error("Backend health check did not become ready");
};

const postJson = async (url, body = {}) => {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`${url} failed with ${response.status}`);
  }
  return response.json();
};

const approveAndPublish = async (baseUrl, platform) => {
  const workflowResponse = await fetch(`${baseUrl}/api/v1/workflow`);
  const workflow = await workflowResponse.json();
  assertNoForbiddenTerms(`${platform} workflow`, workflow);

  const draft = workflow.platformDrafts.find((item) => item.platform === platform);
  if (!draft?.currentVersion?.id) {
    throw new Error(`Smoke workflow did not include a ${platform} draft version`);
  }

  const approval = await postJson(`${baseUrl}/api/v1/drafts/${draft.id}/approve`, {
    draftVersionId: draft.currentVersion.id,
    confirmation: "APPROVE_EXACT_VERSION",
    approver: { name: "Smoke Owner", email: "owner@example.com" },
  });
  assertNoForbiddenTerms(`${platform} approval`, approval);

  const published = await postJson(`${baseUrl}/api/v1/approvals/${approval.approval.id}/publish`);
  assertNoForbiddenTerms(`${platform} fake publish`, published);
  if (published.ctaCopy !== "Queue fake publish") {
    throw new Error(`${platform} fake publish did not include CTA copy`);
  }

  return published.job;
};

const tempDir = await mkdtemp(join(tmpdir(), "localpilot-fake-publish-"));
const dbPath = join(tempDir, "workflow.sqlite");
const port = 8792;
const baseUrl = `http://127.0.0.1:${port}`;

const child = spawn(
  "python3",
  ["-m", "backend.app.server", "--host", "127.0.0.1", "--port", String(port), "--db", dbPath],
  { stdio: ["ignore", "pipe", "pipe"] },
);

let stderr = "";
child.stderr.on("data", (chunk) => {
  stderr += chunk.toString();
});

try {
  await waitForHealth(baseUrl);
  const facebookJob = await approveAndPublish(baseUrl, "facebook");
  const tiktokJob = await approveAndPublish(baseUrl, "tiktok");

  if (facebookJob.status !== "published") {
    throw new Error(`Facebook fake publish ended as ${facebookJob.status}`);
  }
  if (tiktokJob.status !== "retry_needed") {
    throw new Error(`TikTok fake publish ended as ${tiktokJob.status}`);
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        facebook: {
          jobId: facebookJob.id,
          status: facebookJob.status,
          eventStatuses: facebookJob.events.map((event) => event.status),
        },
        tiktok: {
          jobId: tiktokJob.id,
          status: tiktokJob.status,
          eventStatuses: tiktokJob.events.map((event) => event.status),
        },
      },
      null,
      2,
    ),
  );
} finally {
  child.kill("SIGTERM");
  await new Promise((resolve) => child.once("close", resolve));
  await rm(tempDir, { recursive: true, force: true });
  if (child.exitCode && child.exitCode !== 0 && stderr) {
    console.error(stderr);
  }
}
