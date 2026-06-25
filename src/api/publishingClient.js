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
    credentials: "include",
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

export const loadPhase3Workspace = () => requestJson("/phase3/workspace");

export const loadReviewPackage = (token) => requestJson(`/reviews/${encodeURIComponent(token)}`);

export const createReviewFeedback = (token, payload) =>
  requestJson(`/reviews/${encodeURIComponent(token)}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3ContentBatch = (payload) =>
  requestJson("/phase3/content-batches", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3ContentSource = (payload) =>
  requestJson("/phase3/content-sources", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3CreatorStyleVideoWorkflow = (payload) =>
  requestJson("/phase3/creator-style-video-workflows", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const generatePhase3CreatorStyleVideo = (workflowId, payload) =>
  requestJson(`/phase3/creator-style-video-workflows/${encodeURIComponent(workflowId)}/generate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3AiAssistantReply = (payload) =>
  requestJson("/phase3/ai-assistant/replies", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3ContentBatchFromReply = (replyId) =>
  requestJson(`/phase3/ai-assistant/replies/${encodeURIComponent(replyId)}/content-batch`, {
    method: "POST",
  });

export const createPhase3CompetitorSource = (payload) =>
  requestJson("/phase3/competitor-sources", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3TemplateImport = (payload) =>
  requestJson("/phase3/template-imports", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3ApprovalFeedback = (payload) =>
  requestJson("/phase3/approval-feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3ReviewNotification = (payload) =>
  requestJson("/phase3/review-notifications", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updatePhase3BrandKit = (payload) =>
  requestJson("/phase3/brand-kit", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const recordPhase3ProofEvent = (payload) =>
  requestJson("/phase3/proof-events", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updatePhase3Creative = (creativeId, payload) =>
  requestJson(`/phase3/creatives/${encodeURIComponent(creativeId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const createPhase3IdeaVariants = (creativeId, payload) =>
  requestJson(`/phase3/creatives/${encodeURIComponent(creativeId)}/idea-variants`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3LanguageVariants = (creativeId, payload) =>
  requestJson(`/phase3/creatives/${encodeURIComponent(creativeId)}/language-variants`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3BulkVariations = (creativeId, payload) =>
  requestJson(`/phase3/creatives/${encodeURIComponent(creativeId)}/bulk-variations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const createPhase3UgcVoiceoverPackage = (creativeId, payload) =>
  requestJson(`/phase3/creatives/${encodeURIComponent(creativeId)}/ugc-voiceover-package`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const applyPhase3IdeaVariant = (variantId) =>
  requestJson(`/phase3/idea-variants/${encodeURIComponent(variantId)}/apply`, {
    method: "POST",
  });

export const updatePhase3CalendarSlot = (slotId, payload) =>
  requestJson(`/phase3/calendar-slots/${encodeURIComponent(slotId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const updatePhase3MediaAsset = (assetId, payload) =>
  requestJson(`/phase3/media-assets/${encodeURIComponent(assetId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const createPhase3MediaVariant = (assetId, payload) =>
  requestJson(`/phase3/media-assets/${encodeURIComponent(assetId)}/variants`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updatePhase3MediaLayerLayout = (assetId, payload) =>
  requestJson(`/phase3/media-assets/${encodeURIComponent(assetId)}/layer-layout`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const renderPhase3MediaAsset = (assetId, payload) =>
  requestJson(`/phase3/media-assets/${encodeURIComponent(assetId)}/render`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const approveDraftVersion = (draftId, approval) =>
  requestJson(`/drafts/${encodeURIComponent(draftId)}/approve`, {
    method: "POST",
    body: JSON.stringify(approval),
  });

export const queueFakePublish = (approvalId) =>
  requestJson(`/approvals/${encodeURIComponent(approvalId)}/publish`, {
    method: "POST",
  });

export const publishFacebookPost = (approvalId, payload) =>
  requestJson(`/approvals/${encodeURIComponent(approvalId)}/publish-facebook`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const publishTiktokPost = (approvalId, payload = {}) =>
  requestJson(`/approvals/${encodeURIComponent(approvalId)}/publish-tiktok`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const loadPublishJob = (jobId) => requestJson(`/publish-jobs/${encodeURIComponent(jobId)}`);

export const retryPublishJob = (jobId) =>
  requestJson(`/publish-jobs/${encodeURIComponent(jobId)}/retry`, {
    method: "POST",
  });

export const loadDebugPublishJobs = () => requestJson("/debug/publish-jobs");

export const loadAdminPublishJobs = () => requestJson("/admin/publish-jobs");

export const loadAdminPublishJob = (jobId) => requestJson(`/admin/publish-jobs/${encodeURIComponent(jobId)}`);

export const retryAdminPublishJob = (jobId, payload = {}) =>
  requestJson(`/admin/publish-jobs/${encodeURIComponent(jobId)}/retry`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const markAdminSupportPath = (jobId, note) =>
  requestJson(`/admin/publish-jobs/${encodeURIComponent(jobId)}/mark-support`, {
    method: "POST",
    body: JSON.stringify({ note }),
  });

export const loadAdminPublishJobEvidence = (jobId) =>
  requestJson(`/admin/publish-jobs/${encodeURIComponent(jobId)}/evidence`);

export const loadChannelHealth = (platform) =>
  requestJson(`/channels/health${platform ? `?platform=${encodeURIComponent(platform)}` : ""}`);

export const disconnectChannel = (channelId) =>
  requestJson(`/channels/${encodeURIComponent(channelId)}/disconnect`, {
    method: "POST",
  });

export const reconnectChannel = (channelId) =>
  requestJson(`/channels/${encodeURIComponent(channelId)}/reconnect`, {
    method: "POST",
  });

export const loadTiktokCreatorInfo = (channelId) =>
  requestJson(`/tiktok/creator-info${channelId ? `?channelId=${encodeURIComponent(channelId)}` : ""}`);

export const refreshTiktokCreatorInfo = (channelId) =>
  requestJson("/tiktok/creator-info/refresh", {
    method: "POST",
    body: JSON.stringify({ channelId }),
  });

export const loadTiktokMediaPolicy = () => requestJson("/tiktok/media-policy");

export const loadFacebookConnection = () => requestJson("/facebook/connection");

export const crawlWebsite = (url) =>
  requestJson("/onboarding/crawl", {
    method: "POST",
    body: JSON.stringify({ url }),
  });

export const loadOnboardingProfile = () => requestJson("/onboarding/profile");

export const updateOnboardingProfile = (updates) =>
  requestJson("/onboarding/profile", {
    method: "PATCH",
    body: JSON.stringify(updates),
  });

export const confirmOnboardingProfile = () =>
  requestJson("/onboarding/profile/confirm", {
    method: "POST",
  });

export const loadFacebookPages = (connectSession) =>
  requestJson(`/facebook/pages?connectSession=${encodeURIComponent(connectSession)}`);

export const selectFacebookPage = (connectSession, pageId) =>
  requestJson("/facebook/pages/select", {
    method: "POST",
    body: JSON.stringify({ connectSession, pageId }),
  });

export const switchFacebookPage = (pageId) =>
  requestJson("/facebook/pages/switch", {
    method: "POST",
    body: JSON.stringify({ pageId }),
  });

export const googleLogin = (credential) =>
  requestJson("/auth/google", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });

export const devLogin = () =>
  requestJson("/auth/google", {
    method: "POST",
    body: JSON.stringify({ devLogin: true }),
  });

export const logout = () =>
  requestJson("/auth/logout", {
    method: "POST",
  });

export const loadSession = () => requestJson("/auth/session");
