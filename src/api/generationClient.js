const API_ROOT = "/api/v1";

const parseJson = async (response) => {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error("Generation API returned invalid JSON.");
  }
};

const requestJson = async (path, options = {}) => {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const payload = await parseJson(response);

  if (!response.ok) {
    const message = payload?.error?.message || payload?.message || `Generation API request failed with ${response.status}.`;
    throw new Error(message);
  }

  return payload;
};

export const loadGenerationModels = () => requestJson("/generation/models");

export const loadGenerationCredits = () => requestJson("/generation/credits");

export const loadGenerationJobs = () => requestJson("/generation/jobs");

export const launchGenerationJob = (payload) =>
  requestJson("/generation/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const retryGenerationJob = (jobId) =>
  requestJson(`/generation/jobs/${encodeURIComponent(jobId)}/retry`, {
    method: "POST",
  });
