const asArray = (value) => (Array.isArray(value) ? value : []);

const asObject = (value) => (value && typeof value === "object" && !Array.isArray(value) ? value : {});

const text = (value, fallback = "") => (typeof value === "string" && value ? value : fallback);

const number = (value, fallback = 0) => (Number.isFinite(Number(value)) ? Number(value) : fallback);

const normalizeGenerationModel = (model = {}) => {
  const source = asObject(model);
  return {
    id: text(source.id),
    providerKey: text(source.providerKey),
    modelKey: text(source.modelKey),
    capability: text(source.capability),
    displayName: text(source.displayName),
    creditCost: number(source.creditCost, 0),
    readinessStatus: text(source.readinessStatus),
    settingsSchema: asObject(source.settingsSchema),
    limits: asObject(source.limits),
    createdAt: text(source.createdAt),
    updatedAt: text(source.updatedAt),
  };
};

const normalizeGenerationAttempt = (attempt = {}) => {
  const source = asObject(attempt);
  return {
    id: text(source.id),
    generationJobId: text(source.generationJobId),
    attemptNumber: number(source.attemptNumber, 0),
    status: text(source.status),
    diagnostics: asObject(source.diagnostics),
    createdAt: text(source.createdAt),
    updatedAt: text(source.updatedAt),
  };
};

const normalizeGenerationOutput = (output = {}) => {
  const source = asObject(output);
  return {
    id: text(source.id),
    generationJobId: text(source.generationJobId),
    outputKind: text(source.outputKind),
    storageRef: text(source.storageRef),
    previewRef: text(source.previewRef),
    metadata: asObject(source.metadata),
    status: text(source.status),
    createdAt: text(source.createdAt),
    updatedAt: text(source.updatedAt),
  };
};

export const normalizeGenerationJob = (job = {}) => {
  const source = asObject(job);
  const attempts = asArray(source.attempts).map(normalizeGenerationAttempt);
  const outputs = asArray(source.outputs).map(normalizeGenerationOutput);

  return {
    id: text(source.id),
    merchantId: text(source.merchantId),
    modelId: text(source.modelId),
    modelDisplayName: text(source.modelDisplayName),
    creditCost: number(source.creditCost, 0),
    model: normalizeGenerationModel(source.model),
    providerKey: text(source.providerKey),
    modelKey: text(source.modelKey),
    capability: text(source.capability),
    prompt: text(source.prompt),
    request: asObject(source.request),
    settings: asObject(source.settings),
    status: text(source.status),
    reservedCredits: number(source.reservedCredits, 0),
    failureReason: text(source.failureReason),
    attempts,
    outputs,
    workflowType: text(source.workflowType),
    carouselPresetId: text(source.carouselPresetId),
    carouselStage: text(source.slideRoles ? "slides" : ""),
    completedSlides: asArray(source.slideCompositions).length,
    slideRoles: asArray(source.slideRoles),
    sourceKind: text(source.sourceKind),
    sourcePreview: asObject(source.sourcePreview),
    sourceHealth: text(source.sourceHealth),
    creativeId: text(source.creativeId),
    mediaAssetIds: asArray(source.mediaAssetIds),
    slideCompositions: asArray(source.slideCompositions),
    thumbnail: text(source.thumbnail),
    createdAt: text(source.createdAt),
    updatedAt: text(source.updatedAt),
  };
};

export const normalizeGenerationJobsList = (payload = {}) => {
  const source = asObject(payload);
  return asArray(source.jobs).map(normalizeGenerationJob);
};

export const normalizeGenerationCatalog = (payload = {}) => {
  const source = asObject(payload);
  return {
    merchantId: text(source.merchantId),
    models: asArray(source.models).map(normalizeGenerationModel),
  };
};

export const normalizeCreditSummary = (credits = {}) => {
  const source = asObject(credits);
  return {
    merchantId: text(source.merchantId),
    planName: text(source.planName),
    monthlyCredits: number(source.monthlyCredits, 0),
    availableCredits: number(source.availableCredits, 0),
    reservedCredits: number(source.reservedCredits, 0),
    ledgerEntries: number(source.ledgerEntries, 0),
    createdAt: text(source.createdAt),
    updatedAt: text(source.updatedAt),
  };
};
