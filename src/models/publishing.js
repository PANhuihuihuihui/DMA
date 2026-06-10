const asArray = (value) => (Array.isArray(value) ? value : []);

const asObject = (value) => (value && typeof value === "object" && !Array.isArray(value) ? value : {});

const text = (value, fallback = "") => (typeof value === "string" && value ? value : fallback);

const number = (value, fallback = 0) => (Number.isFinite(Number(value)) ? Number(value) : fallback);

const normalizeMediaRef = (media = {}) => {
  const source = asObject(media);
  return {
    mediaAssetId: text(source.mediaAssetId || source.id),
    storageMode: text(source.storageMode),
    storageRef: text(source.storageRef),
    kind: text(source.kind),
    mimeType: text(source.mimeType),
    altText: text(source.altText),
    checksum: text(source.checksum),
    createdAt: text(source.createdAt),
  };
};

const normalizeBoundaryRef = (boundary = {}) => {
  const source = asObject(boundary);
  return {
    id: text(source.id),
    provider: text(source.provider),
    connectedChannelId: text(source.connectedChannelId),
    storageMode: text(source.storageMode),
    rotation: asObject(source.rotation),
    credentialFingerprint: text(source.credentialFingerprint),
    createdAt: text(source.createdAt),
    updatedAt: text(source.updatedAt),
  };
};

const normalizeConnectedChannelRef = (channel = {}) => {
  const source = asObject(channel);
  return {
    id: text(source.id),
    merchantId: text(source.merchantId),
    provider: text(source.provider),
    platform: text(source.platform || source.provider),
    displayName: text(source.displayName),
    providerChannelId: text(source.providerChannelId),
    status: text(source.status),
    tokenBoundaryRef: normalizeBoundaryRef(source.tokenBoundaryRef),
    createdAt: text(source.createdAt),
    updatedAt: text(source.updatedAt),
  };
};

const normalizeDraftVersion = (version = {}) => {
  const source = asObject(version);
  return {
    id: text(source.id),
    draftId: text(source.draftId),
    versionNumber: number(source.versionNumber, 1),
    platform: text(source.platform),
    status: text(source.status, "needs_review"),
    caption: text(source.caption),
    body: text(source.body),
    cta: text(source.cta),
    providerPayloadSummary: asObject(source.providerPayloadSummary),
    disclosureSettingsRef: asObject(source.disclosureSettingsRef),
    mediaRefs: asArray(source.mediaRefs).map(normalizeMediaRef),
    createdAt: text(source.createdAt),
  };
};

const normalizePlatformDraft = (draft = {}) => {
  const source = asObject(draft);
  const versions = asArray(source.versions).map(normalizeDraftVersion);
  const currentVersion = source.currentVersion
    ? normalizeDraftVersion(source.currentVersion)
    : versions.find((version) => version.id === source.currentVersionId) || versions.at(-1) || normalizeDraftVersion();

  return {
    id: text(source.id),
    campaignId: text(source.campaignId),
    merchantId: text(source.merchantId),
    connectedChannelId: text(source.connectedChannelId),
    platform: text(source.platform),
    status: text(source.status, currentVersion.status || "needs_review"),
    currentVersion,
    versions,
    createdAt: text(source.createdAt),
    updatedAt: text(source.updatedAt),
  };
};

const normalizeCampaign = (campaign = {}) => {
  const source = asObject(campaign);
  return {
    id: text(source.id),
    merchantId: text(source.merchant_id || source.merchantId),
    createdByUserId: text(source.created_by_user_id || source.createdByUserId),
    title: text(source.title),
    offer: text(source.offer),
    goal: text(source.goal),
    audience: text(source.audience),
    status: text(source.status),
    createdAt: text(source.created_at || source.createdAt),
    updatedAt: text(source.updated_at || source.updatedAt),
  };
};

export const normalizeApprovalSnapshot = (snapshot = {}) => {
  const source = asObject(snapshot);
  return {
    platform: text(source.platform),
    draftId: text(source.draftId),
    draftVersionId: text(source.draftVersionId),
    versionNumber: number(source.versionNumber, 1),
    caption: text(source.caption),
    body: text(source.body),
    cta: text(source.cta),
    mediaRefs: asArray(source.mediaRefs).map(normalizeMediaRef),
    connectedChannelRef: normalizeConnectedChannelRef(source.connectedChannelRef),
    tokenBoundaryRef: normalizeBoundaryRef(source.tokenBoundaryRef),
    providerPayloadSummary: asObject(source.providerPayloadSummary),
    disclosureSettingsRef: asObject(source.disclosureSettingsRef),
    approver: {
      name: text(source.approver?.name),
      email: text(source.approver?.email),
    },
    approvedAt: text(source.approvedAt),
    createdAt: text(source.createdAt),
    idempotencyKey: text(source.idempotencyKey),
  };
};

const normalizeApproval = (approval = {}) => {
  const source = asObject(approval);
  return {
    id: text(source.id),
    draftId: text(source.draftId),
    draftVersionId: text(source.draftVersionId),
    connectedChannelId: text(source.connectedChannelId),
    status: text(source.status),
    snapshot: normalizeApprovalSnapshot(source.snapshot),
    idempotencyKey: text(source.idempotencyKey),
    createdAt: text(source.createdAt),
  };
};

export const normalizeWorkflow = (workflow = {}) => {
  const source = asObject(workflow);
  return {
    status: text(source.status),
    merchants: asArray(source.merchants).map((merchant) => asObject(merchant)),
    users: asArray(source.users).map((user) => asObject(user)),
    businessProfiles: asArray(source.businessProfiles).map((profile) => asObject(profile)),
    campaigns: asArray(source.campaigns).map(normalizeCampaign),
    connectedChannels: asArray(source.connectedChannels).map(normalizeConnectedChannelRef),
    platformDrafts: asArray(source.platformDrafts).map(normalizePlatformDraft),
    approvals: asArray(source.approvals).map(normalizeApproval),
  };
};
