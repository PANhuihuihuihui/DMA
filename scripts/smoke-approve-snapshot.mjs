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
];

const assertNoForbiddenTerms = (label, payload) => {
  const rendered = JSON.stringify(payload).toLowerCase();
  const found = forbiddenTerms.filter((term) => rendered.includes(term));
  if (found.length) {
    throw new Error(`${label} exposed forbidden fields: ${found.join(", ")}`);
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

const tempDir = await mkdtemp(join(tmpdir(), "localpilot-approval-"));
const dbPath = join(tempDir, "workflow.sqlite");
const port = 8791;
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
  const workflowResponse = await fetch(`${baseUrl}/api/v1/workflow`);
  const workflow = await workflowResponse.json();
  assertNoForbiddenTerms("workflow", workflow);

  const draft = workflow.platformDrafts.find((item) => item.platform === "facebook");
  if (!draft?.currentVersion?.id) {
    throw new Error("Smoke workflow did not include a Facebook draft version");
  }

  const approvalResponse = await fetch(`${baseUrl}/api/v1/drafts/${draft.id}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      draftVersionId: draft.currentVersion.id,
      confirmation: "APPROVE_EXACT_VERSION",
      approver: { name: "Smoke Owner", email: "owner@example.com" },
    }),
  });

  if (!approvalResponse.ok) {
    throw new Error(`Approval failed with ${approvalResponse.status}`);
  }

  const approval = await approvalResponse.json();
  assertNoForbiddenTerms("approval", approval);

  const snapshot = approval.approval?.snapshot;
  if (!snapshot?.mediaRefs?.length || !snapshot?.tokenBoundaryRef?.id || !snapshot?.idempotencyKey) {
    throw new Error("Approval snapshot is missing media refs, token boundary ref, or idempotency key");
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        platform: snapshot.platform,
        draftVersionId: snapshot.draftVersionId,
        mediaRefs: snapshot.mediaRefs.length,
        tokenBoundaryRef: snapshot.tokenBoundaryRef.id,
        idempotencyKey: snapshot.idempotencyKey,
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
