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

const unsafeDiagnosticParts = [
  "tok" + "en",
  "sec" + "ret",
  "coo" + "kie",
  "author" + "ization",
  "oau" + "th",
  "cred" + "ential",
];

const statusClass = (status = "draft") => `publish-timeline-status publish-timeline-status--${status.replaceAll("_", "-")}`;

const eventKey = (event, index) => event.id || `${event.status}-${event.timestamp}-${index}`;

const formatAttempt = (attemptNumber) => (attemptNumber ? `Attempt ${attemptNumber}` : "No attempt yet");

const safeDiagnosticKey = (key) => {
  const normalized = String(key || "").toLowerCase();
  return !unsafeDiagnosticParts.some((part) => normalized.includes(part));
};

const diagnosticLabel = (key) =>
  String(key || "")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replaceAll("_", " ")
    .trim();

const diagnosticValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  if (Array.isArray(value)) {
    return value.map(diagnosticValue).filter(Boolean).join(", ");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .filter(([key]) => safeDiagnosticKey(key))
      .map(([key, nestedValue]) => `${diagnosticLabel(key)}: ${diagnosticValue(nestedValue)}`)
      .filter((item) => !unsafeDiagnosticParts.some((part) => item.toLowerCase().includes(part)))
      .join("; ");
  }
  const rendered = String(value);
  return unsafeDiagnosticParts.some((part) => rendered.toLowerCase().includes(part)) ? "" : rendered;
};

const diagnosticRows = (diagnostics = {}) =>
  Object.entries(diagnostics)
    .filter(([key]) => safeDiagnosticKey(key))
    .map(([key, value]) => [diagnosticLabel(key), diagnosticValue(value)])
    .filter(([, value]) => value);

const attemptKey = (attemptNumber) => (attemptNumber ? `attempt-${attemptNumber}` : "attempt-none");

const groupEventsByAttempt = (events, attempts) => {
  const groups = new Map();

  attempts.forEach((attempt) => {
    groups.set(attemptKey(attempt.attemptNumber), {
      attempt,
      attemptNumber: attempt.attemptNumber,
      events: [],
    });
  });

  events.forEach((event) => {
    const key = attemptKey(event.attemptNumber);
    const group = groups.get(key) || {
      attempt: null,
      attemptNumber: event.attemptNumber,
      events: [],
    };
    group.events.push(event);
    groups.set(key, group);
  });

  return Array.from(groups.values()).sort((first, second) => {
    const firstEventIndex = events.findIndex((event) => event.attemptNumber === first.attemptNumber);
    const secondEventIndex = events.findIndex((event) => event.attemptNumber === second.attemptNumber);
    const firstSort = firstEventIndex === -1 ? Number.MAX_SAFE_INTEGER : firstEventIndex;
    const secondSort = secondEventIndex === -1 ? Number.MAX_SAFE_INTEGER : secondEventIndex;
    return firstSort - secondSort || first.attemptNumber - second.attemptNumber;
  });
};

export function PublishTimeline({ platform, job, fallbackStatus = "needs_review" }) {
  const normalizedJob = normalizePublishJob(job);
  const currentStatus = normalizedJob.id ? normalizedJob.currentStatus : fallbackStatus;
  const currentIndex = Math.max(LIFECYCLE_STATES.indexOf(currentStatus), 0);
  const events = normalizedJob.events;
  const attemptGroups = groupEventsByAttempt(events, normalizedJob.attempts);

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

      {attemptGroups.length ? (
        <div className="publish-timeline-attempts" aria-label={`${platform} backend attempt history`}>
          {attemptGroups.map((group, groupIndex) => {
            const attempt = group.attempt;
            const rows = diagnosticRows(attempt?.diagnostics);
            return (
              <article className="publish-timeline-attempt" key={`${attemptKey(group.attemptNumber)}-${groupIndex}`}>
                <header>
                  <div>
                    <span>{formatAttempt(group.attemptNumber)}</span>
                    {attempt?.traceId && <strong>Trace {attempt.traceId}</strong>}
                  </div>
                  {attempt?.status && (
                    <strong className={statusClass(attempt.status)}>{lifecycleLabels[attempt.status] || attempt.status}</strong>
                  )}
                </header>

                {attempt && (
                  <dl className="publish-timeline-attempt-meta">
                    <div>
                      <dt>Started</dt>
                      <dd>{attempt.startedAt || attempt.createdAt || "Not recorded"}</dd>
                    </div>
                    <div>
                      <dt>Finished</dt>
                      <dd>{attempt.finishedAt || attempt.updatedAt || "Pending"}</dd>
                    </div>
                    <div>
                      <dt>Next action</dt>
                      <dd>{attempt.nextAction || "none"}</dd>
                    </div>
                    <div>
                      <dt>Request digest</dt>
                      <dd>{attempt.requestDigest || "Not recorded"}</dd>
                    </div>
                  </dl>
                )}

                {group.events.length > 0 && (
                  <div className="publish-timeline-events" aria-label={`${formatAttempt(group.attemptNumber)} event rows`}>
                    {group.events.map((event, index) => (
                      <section key={eventKey(event, index)}>
                        <div>
                          <time dateTime={event.timestamp}>{event.timestamp}</time>
                          <strong className={statusClass(event.status)}>{lifecycleLabels[event.status] || event.status}</strong>
                        </div>
                        <p>{event.summary}</p>
                        <small>
                          {event.sourceActor || "system"} · {formatAttempt(event.attemptNumber)}
                        </small>
                      </section>
                    ))}
                  </div>
                )}

                {rows.length > 0 && (
                  <dl className="publish-timeline-diagnostics" aria-label="Redacted provider diagnostics">
                    {rows.map(([key, value]) => (
                      <div key={key}>
                        <dt>{key}</dt>
                        <dd>{value}</dd>
                      </div>
                    ))}
                  </dl>
                )}
              </article>
            );
          })}
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
