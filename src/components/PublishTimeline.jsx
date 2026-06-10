import React from "react";

import { LIFECYCLE_STATES, normalizePublishJob } from "../models/publishing.js";

const lifecycleLabels = {
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

const terminalStates = new Set(["published", "failed", "manual_fallback_required"]);

const statusClass = (status) => `publish-timeline-status publish-timeline-status--${status.replaceAll("_", "-")}`;

const eventKey = (event, index) => event.id || `${event.status}-${event.timestamp}-${index}`;

const formatAttempt = (attemptNumber) => (attemptNumber ? `Attempt ${attemptNumber}` : "No attempt yet");

export function PublishTimeline({ platform, job, fallbackStatus = "needs_review" }) {
  const normalizedJob = normalizePublishJob(job);
  const currentStatus = normalizedJob.id ? normalizedJob.currentStatus : fallbackStatus;
  const currentIndex = Math.max(LIFECYCLE_STATES.indexOf(currentStatus), 0);
  const events = normalizedJob.events;

  return (
    <section className="publish-timeline-panel" aria-label={`${platform} fake publish timeline`}>
      <div className="publish-timeline-head">
        <div>
          <span>Backend-backed workflow</span>
          <h3>{platform} fake publish timeline</h3>
        </div>
        <strong className={statusClass(currentStatus)}>{lifecycleLabels[currentStatus] || currentStatus}</strong>
      </div>

      <ol className="publish-timeline-steps" aria-label={`${platform} lifecycle states`}>
        {LIFECYCLE_STATES.map((state, index) => {
          const isCurrent = state === currentStatus;
          const isComplete = normalizedJob.id && index < currentIndex && !terminalStates.has(state);
          return (
            <li
              className={`${isCurrent ? "current" : ""} ${isComplete ? "complete" : ""}`}
              key={state}
            >
              <span aria-hidden="true" />
              <strong>{lifecycleLabels[state]}</strong>
            </li>
          );
        })}
      </ol>

      {events.length ? (
        <div className="publish-timeline-events" aria-label={`${platform} backend event history`}>
          {events.map((event, index) => (
            <article key={eventKey(event, index)}>
              <div>
                <time dateTime={event.timestamp}>{event.timestamp}</time>
                <strong className={statusClass(event.status)}>{lifecycleLabels[event.status] || event.status}</strong>
              </div>
              <p>{event.summary}</p>
              <small>
                {event.sourceActor || "system"} · {formatAttempt(event.attemptNumber)}
              </small>
            </article>
          ))}
        </div>
      ) : (
        <div className="publish-timeline-empty">
          <strong>No publish jobs yet</strong>
          <p>Approve a platform draft to create a backend-backed publish job and timeline.</p>
        </div>
      )}
    </section>
  );
}
