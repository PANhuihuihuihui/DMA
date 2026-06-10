import React, { useMemo, useState } from "react";

import { retryPublishJob } from "../api/publishingClient.js";
import { RETRYABLE_PUBLISH_STATUSES, normalizePublishJob } from "../models/publishing.js";

const statusTone = (status = "") => (status === "failed" ? "failed" : "retry-needed");

export function RetryPublishControl({ job, platform, onRetryAccepted }) {
  const normalizedJob = useMemo(() => normalizePublishJob(job), [job]);
  const [confirming, setConfirming] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const status = normalizedJob.currentStatus || normalizedJob.status;
  const nextAttempt = Math.max(0, ...normalizedJob.attempts.map((attempt) => attempt.attemptNumber)) + 1;

  if (!normalizedJob.id || !RETRYABLE_PUBLISH_STATUSES.includes(status)) {
    return null;
  }

  const confirmRetry = async () => {
    setPending(true);
    setError("");
    try {
      const payload = await retryPublishJob(normalizedJob.id);
      const nextJob = normalizePublishJob(payload?.job);
      await Promise.resolve(onRetryAccepted?.(nextJob.id ? nextJob : normalizedJob));
      setConfirming(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Retry request failed.");
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={`publish-timeline-retry publish-timeline-retry--${statusTone(status)}`}>
      <button
        className="secondary-action publish-timeline-retry-button"
        type="button"
        disabled={pending}
        onClick={() => setConfirming(true)}
      >
        Retry publish
      </button>

      {confirming && (
        <div className="publish-timeline-retry-confirm" role="group" aria-label={`${platform} retry confirmation`}>
          <strong>Retry publish</strong>
          <p>
            Retry this publish job? LocalPilot will create attempt #{nextAttempt} for the approved draft snapshot.
            Idempotency prevents duplicate published outcomes.
          </p>
          {pending && <small className="inline-pending">Creating attempt #{nextAttempt}...</small>}
          {error && <small className="publish-timeline-retry-error">{error}</small>}
          <div>
            <button
              className="primary-action"
              type="button"
              disabled={pending}
              onClick={confirmRetry}
            >
              Confirm retry
            </button>
            <button
              className="secondary-action"
              type="button"
              disabled={pending}
              onClick={() => {
                setConfirming(false);
                setError("");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
