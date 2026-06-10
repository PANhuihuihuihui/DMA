const API_ROOT = "/api/v1";

const parseJson = async (response) => {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error("Publishing API returned invalid JSON.");
  }
};

const requestJson = async (path, options = {}) => {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const payload = await parseJson(response);

  if (!response.ok) {
    const message = payload?.error?.message || payload?.message || `Publishing API request failed with ${response.status}.`;
    throw new Error(message);
  }

  return payload;
};

export const loadPublishingWorkflow = () => requestJson("/workflow");

export const approveDraftVersion = (draftId, approval) =>
  requestJson(`/drafts/${encodeURIComponent(draftId)}/approve`, {
    method: "POST",
    body: JSON.stringify(approval),
  });

export const queueFakePublish = (approvalId) =>
  requestJson(`/approvals/${encodeURIComponent(approvalId)}/publish`, {
    method: "POST",
  });

export const loadPublishJob = (jobId) => requestJson(`/publish-jobs/${encodeURIComponent(jobId)}`);

export const retryPublishJob = (jobId) =>
  requestJson(`/publish-jobs/${encodeURIComponent(jobId)}/retry`, {
    method: "POST",
  });

export const loadDebugPublishJobs = () => requestJson("/debug/publish-jobs");
