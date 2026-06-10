import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

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

const getJson = async (url) => {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(`${url} failed with ${response.status}: ${JSON.stringify(payload)}`);
  }
  return payload;
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

const assertDebugRow = (row) => {
  const required = [
    "merchant",
    "platform",
    "jobStatus",
    "attemptCount",
    "latestTraceId",
    "errorClass",
    "updatedAt",
    "nextAction",
    "approver",
    "draftVersion",
    "mediaRefs",
    "tokenBoundaryRef",
    "approvalSnapshotSummary",
    "attempts",
    "events",
    "redactedDiagnostics",
  ];
  const missing = required.filter((key) => !(key in row));
  if (missing.length) {
    throw new Error(`Debug row missing fields: ${missing.join(", ")}`);
  }
  if (!row.latestTraceId?.startsWith("trace_")) {
    throw new Error(`Debug row has invalid trace ID: ${row.latestTraceId}`);
  }
  if (row.tokenBoundaryRef.visibility !== "redacted") {
    throw new Error("Debug row exposed an unredacted token boundary ref");
  }
  if ("secretRef" in row.tokenBoundaryRef || "credentialFingerprint" in row.tokenBoundaryRef) {
    throw new Error("Debug row exposed token boundary internals");
  }
};

const tempDir = await mkdtemp(join(tmpdir(), "localpilot-debug-route-"));
const dbPath = join(tempDir, "workflow.sqlite");
const port = 8794;
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
  const facebook = await approveAndPublish(baseUrl, "facebook");
  const tiktok = await approveAndPublish(baseUrl, "tiktok");
  if (facebook.job.status !== "published") {
    throw new Error(`Facebook fake publish ended as ${facebook.job.status}`);
  }
  if (tiktok.job.status !== "retry_needed") {
    throw new Error(`TikTok fake publish ended as ${tiktok.job.status}`);
  }

  const debugBeforeRetry = await getJson(`${baseUrl}/api/v1/debug/publish-jobs`);
  assertNoForbiddenTerms("debug before retry", debugBeforeRetry);
  if (debugBeforeRetry.publishJobs.length !== 2) {
    throw new Error(`Expected two debug rows, got ${debugBeforeRetry.publishJobs.length}`);
  }
  debugBeforeRetry.publishJobs.forEach(assertDebugRow);

  const retryPayload = await postJson(`${baseUrl}/api/v1/publish-jobs/${tiktok.job.id}/retry`, {
    diagnosticsFixture: forbiddenDiagnosticsFixture(),
  });
  assertNoForbiddenTerms("retry payload", retryPayload);

  const debugAfterRetry = await getJson(`${baseUrl}/api/v1/debug/publish-jobs`);
  assertNoForbiddenTerms("debug after retry", debugAfterRetry);
  debugAfterRetry.publishJobs.forEach(assertDebugRow);

  const retryRow = debugAfterRetry.publishJobs.find((row) => row.platform === "tiktok");
  if (retryRow.jobStatus !== "published" || retryRow.attemptCount !== 2) {
    throw new Error(`Retry debug row did not publish with two attempts: ${JSON.stringify(retryRow)}`);
  }

  const output = {
    ok: true,
    statuses: Object.fromEntries(debugAfterRetry.publishJobs.map((row) => [row.platform, row.jobStatus])),
    attempts: Object.fromEntries(debugAfterRetry.publishJobs.map((row) => [row.platform, row.attemptCount])),
    latestTraceIds: Object.fromEntries(debugAfterRetry.publishJobs.map((row) => [row.platform, row.latestTraceId])),
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
