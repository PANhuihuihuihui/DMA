import React from "react";

import { normalizeApprovalSnapshot } from "../models/publishing.js";

const formatValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "Not set";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
};

const idSuffix = (value) => (value ? value.slice(-8) : "pending");

const renderSummaryRows = (summary) =>
  Object.entries(summary || {}).map(([key, value]) => (
    <span key={key}>
      <strong>{key}</strong>
      <em>{formatValue(value)}</em>
    </span>
  ));

export function ApprovalSnapshot({ snapshot }) {
  const approval = normalizeApprovalSnapshot(snapshot);

  if (!approval.draftVersionId) {
    return (
      <section className="approval-snapshot-panel approval-snapshot-empty" aria-label="Approval snapshot">
        <div className="approval-snapshot-head">
          <div>
            <span>Backend snapshot</span>
            <h3>No approved snapshot yet</h3>
          </div>
          <strong>Awaiting approval</strong>
        </div>
        <p>Approve this exact platform draft to freeze the backend payload used for publishing.</p>
      </section>
    );
  }

  return (
    <section className="approval-snapshot-panel" aria-label={`${approval.platform} approval snapshot`}>
      <div className="approval-snapshot-head">
        <div>
          <span>Frozen approval snapshot</span>
          <h3>
            {approval.platform} draft v{approval.versionNumber}
          </h3>
        </div>
        <strong>View snapshot</strong>
      </div>

      <dl className="approval-snapshot-meta">
        <div>
          <dt>Approver</dt>
          <dd>
            {approval.approver.name}
            {approval.approver.email ? ` (${approval.approver.email})` : ""}
          </dd>
        </div>
        <div>
          <dt>Approved</dt>
          <dd>{approval.approvedAt || approval.createdAt}</dd>
        </div>
        <div>
          <dt>Idempotency suffix</dt>
          <dd>{idSuffix(approval.idempotencyKey)}</dd>
        </div>
        <div>
          <dt>Target ref</dt>
          <dd>{approval.connectedChannelRef.displayName || approval.connectedChannelRef.providerChannelId}</dd>
        </div>
      </dl>

      <div className="approval-snapshot-copy">
        <div>
          <span>Caption</span>
          <p>{approval.caption}</p>
        </div>
        <div>
          <span>Body</span>
          <p>{approval.body}</p>
        </div>
        <div>
          <span>CTA</span>
          <p>{approval.cta}</p>
        </div>
      </div>

      <div className="approval-snapshot-grid">
        <article>
          <span>Media refs</span>
          <ul>
            {approval.mediaRefs.map((media) => (
              <li key={media.mediaAssetId || media.storageRef}>
                <strong>{media.kind || "media"}</strong>
                <em>{media.storageRef}</em>
                <small>{media.mimeType}</small>
              </li>
            ))}
          </ul>
        </article>
        <article>
          <span>Provider payload summary</span>
          <div className="approval-snapshot-pairs">{renderSummaryRows(approval.providerPayloadSummary)}</div>
        </article>
        <article>
          <span>Disclosure/settings ref</span>
          <div className="approval-snapshot-pairs">{renderSummaryRows(approval.disclosureSettingsRef)}</div>
        </article>
        <article>
          <span>Token boundary ref</span>
          <div className="approval-snapshot-pairs">
            <span>
              <strong>ID</strong>
              <em>{approval.tokenBoundaryRef.id}</em>
            </span>
            <span>
              <strong>Provider</strong>
              <em>{approval.tokenBoundaryRef.provider}</em>
            </span>
            <span>
              <strong>Storage</strong>
              <em>{approval.tokenBoundaryRef.storageMode}</em>
            </span>
            <span>
              <strong>Fingerprint</strong>
              <em>{approval.tokenBoundaryRef.credentialFingerprint}</em>
            </span>
          </div>
        </article>
      </div>
    </section>
  );
}
