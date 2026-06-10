const asArray = (value) => (Array.isArray(value) ? value : []);

const asObject = (value) => (value && typeof value === "object" && !Array.isArray(value) ? value : {});

const text = (value, fallback = "") => (typeof value === "string" && value ? value : fallback);

const number = (value, fallback = 0) => (Number.isFinite(Number(value)) ? Number(value) : fallback);

const statusLabels = {
  draft: "Draft",
  needs_review: "Needs review",
  approved: "Approved",
  queued: "Queued",
  publishing: "Publishing",
  published: "Published",
  failed: "Failed",
  retry_needed: "Retry needed",
  manual_fallback_required: "Manual fallback required",
};

const blockedDiagnosticParts = [
  "tok" + "en",
  "sec" + "ret",
  "coo" + "kie",
  "author" + "ization",
  "oau" + "th",
  "cred" + "ential",
  "raw",
];

const titleize = (value) =>
  String(value || "")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replaceAll("_", " ")
    .trim();

export const getStatusLabel = (status = "") => statusLabels[status] || titleize(status) || "Unknown";

export const getCurrentState = (job = {}) =>
  text(asObject(job).jobStatus || asObject(job).status, asArray(asObject(job).events).at(-1)?.status || "draft");

export const getAttemptCount = (job = {}) => number(asObject(job).attemptCount, asArray(asObject(job).attempts).length);

export const getIdempotencySuffix = (value = "") => {
  const source = text(value);
  if (!source) {
    return "";
  }
  return source.includes(":") ? source.split(":").at(-1) : source.slice(-8);
};

export const getLatestTraceId = (job = {}) => {
  const source = asObject(job);
  return text(source.latestTraceId, text(asArray(source.attempts).at(-1)?.traceId));
};

const isSafeDiagnosticKey = (key) => {
  const normalized = String(key || "").toLowerCase();
  return !blockedDiagnosticParts.some((part) => normalized.includes(part));
};

const safeDiagnosticValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  if (Array.isArray(value)) {
    return value.map(safeDiagnosticValue).filter(Boolean).join(", ");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .filter(([key]) => isSafeDiagnosticKey(key))
      .map(([key, nestedValue]) => `${titleize(key)}: ${safeDiagnosticValue(nestedValue)}`)
      .filter((item) => item && !blockedDiagnosticParts.some((part) => item.toLowerCase().includes(part)))
      .join("; ");
  }
  const rendered = String(value);
  return blockedDiagnosticParts.some((part) => rendered.toLowerCase().includes(part)) ? "" : rendered;
};

export const summarizeDiagnostics = (diagnostics = {}) =>
  Object.entries(asObject(diagnostics))
    .filter(([key]) => isSafeDiagnosticKey(key))
    .map(([key, value]) => ({
      label: titleize(key),
      value: safeDiagnosticValue(value),
    }))
    .filter((row) => row.value);

const summarizeAttempt = (attempt = {}) => {
  const source = asObject(attempt);
  return {
    id: text(source.id),
    attemptNumber: number(source.attemptNumber),
    status: text(source.status),
    statusLabel: getStatusLabel(source.status),
    traceId: text(source.traceId),
    requestDigest: text(source.requestDigest),
    errorClass: text(source.errorClass || source.diagnostics?.errorClass, "none"),
    nextAction: text(source.nextAction || source.diagnostics?.nextRecommendedAction || source.diagnostics?.nextAction, "none"),
    retryClassification: text(source.retryClassification, "none"),
    startedAt: text(source.startedAt || source.createdAt),
    finishedAt: text(source.finishedAt || source.updatedAt),
    diagnostics: summarizeDiagnostics(source.diagnostics),
  };
};

const summarizeEvent = (event = {}) => {
  const source = asObject(event);
  return {
    id: text(source.id),
    timestamp: text(source.timestamp || source.createdAt),
    sourceActor: text(source.sourceActor || source.actor, "system"),
    attemptNumber: number(source.attemptNumber),
    status: text(source.status || source.eventType),
    statusLabel: getStatusLabel(source.status || source.eventType),
    summary: text(source.summary),
  };
};

const summarizeMediaRef = (media = {}) => {
  const source = asObject(media);
  return {
    id: text(source.mediaAssetId || source.id),
    kind: text(source.kind),
    storageMode: text(source.storageMode),
    storageRef: text(source.storageRef),
    altText: text(source.altText),
  };
};

const summarizeApprovalSnapshot = (snapshot = {}) => {
  const source = asObject(snapshot);
  return {
    platform: text(source.platform),
    draftVersionId: text(source.draftVersionId),
    versionNumber: number(source.versionNumber || source.draftVersion?.versionNumber, 1),
    approver: asObject(source.approver),
    approvedAt: text(source.approvedAt || source.createdAt),
    idempotencyKeySuffix: text(source.idempotencyKeySuffix, getIdempotencySuffix(source.idempotencyKey)),
    mediaRefs: asArray(source.mediaRefs).map(summarizeMediaRef),
    tokenBoundaryRef: {
      id: text(source.tokenBoundaryRef?.id),
      provider: text(source.tokenBoundaryRef?.provider),
      visibility: text(source.tokenBoundaryRef?.visibility, "redacted"),
    },
  };
};

export const summarizeDebugJob = (job = {}) => {
  const source = asObject(job);
  const attempts = asArray(source.attempts).map(summarizeAttempt);
  const latestAttempt = attempts.at(-1) || {};
  const diagnostics = summarizeDiagnostics(source.redactedDiagnostics || asArray(source.attempts).at(-1)?.diagnostics);

  return {
    id: text(source.id || source.jobId),
    merchant: asObject(source.merchant),
    platform: text(source.platform),
    currentState: getCurrentState(source),
    statusLabel: getStatusLabel(getCurrentState(source)),
    attemptCount: getAttemptCount(source),
    latestTraceId: getLatestTraceId(source),
    errorClass: text(source.errorClass || latestAttempt.errorClass, "none"),
    updatedAt: text(source.updatedAt),
    nextAction: text(source.nextAction || latestAttempt.nextAction, "none"),
    approver: asObject(source.approver),
    draftVersion: asObject(source.draftVersion),
    mediaRefs: asArray(source.mediaRefs).map(summarizeMediaRef),
    tokenBoundaryRef: {
      id: text(source.tokenBoundaryRef?.id),
      provider: text(source.tokenBoundaryRef?.provider),
      visibility: text(source.tokenBoundaryRef?.visibility, "redacted"),
    },
    approvalSnapshotSummary: summarizeApprovalSnapshot(source.approvalSnapshotSummary),
    attempts,
    events: asArray(source.events).map(summarizeEvent),
    diagnostics,
  };
};
