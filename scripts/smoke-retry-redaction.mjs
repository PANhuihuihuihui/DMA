import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn } from "node:child_process";

const secretFields = [
  "access" + "_token",
  "refresh" + "_token",
  "author" + "ization",
  "coo" + "kie",
  "client" + "_secret",
  "api" + "_key",
  "oauth" + "_payload",
  "provider" + "_raw",
];

const secretValues = [
  "lp-secret-alpha",
  "lp-secret-beta",
  "lp-secret-gamma",
  "lp-secret-delta",
  "lp-secret-epsilon",
  "lp-secret-zeta",
  "lp-secret-eta",
  "lp-secret-theta",
];

const forbiddenDiagnosticsFixture = () => ({
  [secretFields[0]]: secretValues[0],
  nested: {
    [secretFields[1]]: secretValues[1],
    headers: {
      [secretFields[2]]: `Bearer ${secretValues[2]}`,
      [secretFields[3]]: `session=${secretValues[3]}`,
    },
  },
  provider: {
    [secretFields[4]]: secretValues[4],
    [secretFields[5]]: secretValues[5],
    [secretFields[6]]: { raw: secretValues[6] },
    [secretFields[7]]: { body: secretValues[7] },
  },
  safe: {
    provider: "fake",
    errorClass: "platform_transient",
    nextAction: "retry_publish",
  },
});

const forbiddenTerms = [
  ...secretFields,
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
  const leakedValues = secretValues.filter((value) => rendered.includes(value));
  if (leakedValues.length) {
    throw new Error(`${label} exposed secret fixture values`);
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
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(`${url} failed with ${response.status}: ${JSON.stringify(payload)}`);
  }
  return payload;
};

const getJson = async (url) => {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(`${url} failed with ${response.status}: ${JSON.stringify(payload)}`);
  }
  return payload;
};

const approveAndPublish = async (baseUrl, platform) => {
  const workflow = await getJson(`${baseUrl}/api/v1/workflow`);
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

  return { approval: approval.approval, job: published.job };
};

const tempDir = await mkdtemp(join(tmpdir(), "localpilot-retry-redaction-"));
const dbPath = join(tempDir, "workflow.sqlite");
const port = 8793;
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
  const { approval, job } = await approveAndPublish(baseUrl, "tiktok");
  if (job.status !== "retry_needed") {
    throw new Error(`TikTok fake publish ended as ${job.status}`);
  }

  const retryPayload = await postJson(`${baseUrl}/api/v1/publish-jobs/${job.id}/retry`, {
    diagnosticsFixture: forbiddenDiagnosticsFixture(),
  });
  assertNoForbiddenTerms("retry payload", retryPayload);

  const fetched = await getJson(`${baseUrl}/api/v1/publish-jobs/${job.id}`);
  assertNoForbiddenTerms("retry fetched job", fetched);

  const attempts = fetched.job.attempts.map((attempt) => attempt.attemptNumber);
  if (fetched.job.status !== "published" || attempts.join(",") !== "1,2") {
    throw new Error(`Retry did not publish with two attempts: ${JSON.stringify({ status: fetched.job.status, attempts })}`);
  }
  if (fetched.job.approvalSnapshot.idempotencyKey !== approval.idempotencyKey) {
    throw new Error("Retry changed the approved snapshot idempotency key");
  }
  if (fetched.job.attempts[0].traceId === fetched.job.attempts[1].traceId) {
    throw new Error("Retry attempt reused the first attempt trace ID");
  }

  const output = {
    ok: true,
    jobId: fetched.job.id,
    status: fetched.job.status,
    attempts,
    eventStatuses: fetched.job.events.map((event) => event.status),
    idempotencyKeySuffix: fetched.job.approvalSnapshot.idempotencyKey.slice(-8),
  };
  assertNoForbiddenTerms("smoke stdout", output);
  console.log(JSON.stringify(output, null, 2));
} finally {
  child.kill("SIGTERM");
  await new Promise((resolve) => child.once("close", resolve));
  await rm(tempDir, { recursive: true, force: true });
  if (child.exitCode && child.exitCode !== 0 && stderr) {
    console.error(stderr);
  }
}
