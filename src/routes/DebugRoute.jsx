import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { loadDebugPublishJobs } from "../api/publishingClient.js";
import { getStatusLabel, summarizeDebugJob } from "../publishing/workflow.js";

const statusClass = (status = "draft") => `debug-jobs-status debug-jobs-status--${status.replaceAll("_", "-")}`;

const formatPlatform = (platform = "") => (platform ? platform[0].toUpperCase() + platform.slice(1) : "Unknown");

const display = (value, fallback = "Not recorded") => value || fallback;

const eventKey = (event, index) => event.id || `${event.status}-${event.timestamp}-${index}`;

const attemptKey = (attempt, index) => attempt.id || `${attempt.attemptNumber}-${attempt.traceId}-${index}`;

const mediaKey = (media, index) => media.id || `${media.kind}-${index}`;

function RedactedDiagnostics({ rows, labelledBy }) {
  if (!rows?.length) {
    return (
      <div className="redacted-diagnostics-empty" aria-labelledby={labelledBy || undefined}>
        <strong>No redacted diagnostics</strong>
        <p>The latest attempt did not return support-facing diagnostic details.</p>
      </div>
    );
  }

  return (
    <dl className="redacted-diagnostics-list" aria-labelledby={labelledBy || undefined}>
      {rows.map((row) => (
        <div key={`${row.label}-${row.value}`}>
          <dt>{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function DebugRoute() {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [copyStatus, setCopyStatus] = useState("");

  const selectedJob = useMemo(
    () => jobs.find((job) => job.id === selectedJobId) || jobs[0] || null,
    [jobs, selectedJobId],
  );

  const loadJobs = async () => {
    setStatus("loading");
    setError("");
    try {
      const payload = await loadDebugPublishJobs();
      const nextJobs = (Array.isArray(payload?.publishJobs) ? payload.publishJobs : []).map(summarizeDebugJob);
      setJobs(nextJobs);
      setSelectedJobId((currentId) =>
        currentId && nextJobs.some((job) => job.id === currentId) ? currentId : nextJobs[0]?.id || "",
      );
      setStatus("ready");
    } catch (caught) {
      setStatus("error");
      setError(caught instanceof Error ? caught.message : "Publishing status could not load.");
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const copyTraceId = async (traceId) => {
    if (!traceId) {
      return;
    }
    try {
      await navigator.clipboard.writeText(traceId);
      setCopyStatus("Trace ID copied.");
    } catch {
      setCopyStatus("Trace ID copy failed.");
    }
    window.setTimeout(() => setCopyStatus(""), 1800);
  };

  return (
    <div className="app-shell debug-jobs-shell">
      <aside className="app-sidebar debug-jobs-sidebar" aria-label="Operator diagnostics">
        <Link className="app-brand debug-jobs-brand" to="/">
          <span>LocalPilot AI</span>
        </Link>
        <div className="workspace-switcher">
          <span>Operator route</span>
          <strong>Publishing diagnostics</strong>
          <small>Direct URL only</small>
        </div>
        <div className="sidebar-card">
          <span>Read-only support view</span>
          <p>Inspect backend-backed fake publish attempts, trace IDs, and redacted provider diagnostics.</p>
        </div>
        <Link className="secondary-action debug-jobs-back" to="/app">
          Back to workspace
        </Link>
      </aside>

      <main className="app-main debug-jobs-main">
        <header className="app-topbar">
          <div>
            <p className="app-kicker">Hidden operator diagnostics</p>
            <h1>Publish job debug</h1>
            <p className="topbar-summary">
              Read-only support records for fake publish jobs, attempts, trace IDs, and redacted provider diagnostics.
            </p>
          </div>
          <div className="topbar-actions">
            <button className="secondary-action" type="button" onClick={loadJobs}>
              Reload workflow
            </button>
          </div>
        </header>

        <section className="debug-jobs-grid">
          <section className="primary-panel debug-jobs-table-panel" aria-label="Publish job operations table">
            <div className="panel-head">
              <div>
                <p className="app-kicker">Operations table</p>
                <h2>Backend publish jobs</h2>
              </div>
              <span className="debug-jobs-count">{jobs.length} jobs</span>
            </div>

            {status === "error" && (
              <div className="debug-jobs-state">
                <strong>Publishing status could not load.</strong>
                <p>{error}</p>
                <button className="secondary-action" type="button" onClick={loadJobs}>
                  Reload workflow
                </button>
              </div>
            )}

            {status === "loading" && (
              <div className="debug-jobs-state">
                <strong>Loading backend records.</strong>
                <p>LocalPilot is loading support diagnostics from the backend debug endpoint.</p>
              </div>
            )}

            {status === "ready" && jobs.length === 0 && (
              <div className="debug-jobs-state">
                <strong>No publish jobs yet</strong>
                <p>Approve a platform draft to create a backend-backed publish job and timeline.</p>
              </div>
            )}

            {jobs.length > 0 && (
              <div className="debug-jobs-table-wrap">
                <table className="debug-jobs-table">
                  <thead>
                    <tr>
                      <th scope="col">Merchant</th>
                      <th scope="col">Platform</th>
                      <th scope="col">Job status</th>
                      <th scope="col">Attempt count</th>
                      <th scope="col">Latest trace ID</th>
                      <th scope="col">Error class</th>
                      <th scope="col">Updated timestamp</th>
                      <th scope="col">Next action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <tr
                        className={selectedJob?.id === job.id ? "selected" : ""}
                        key={job.id}
                        onClick={() => setSelectedJobId(job.id)}
                      >
                        <td data-label="Merchant">
                          <button type="button" onClick={() => setSelectedJobId(job.id)}>
                            {display(job.merchant.name, "Unknown merchant")}
                          </button>
                        </td>
                        <td data-label="Platform">{formatPlatform(job.platform)}</td>
                        <td data-label="Job status">
                          <span className={statusClass(job.currentState)}>{job.statusLabel}</span>
                        </td>
                        <td data-label="Attempt count">{job.attemptCount}</td>
                        <td data-label="Latest trace ID">
                          <span className="debug-jobs-mono">{display(job.latestTraceId)}</span>
                        </td>
                        <td data-label="Error class">{display(job.errorClass, "none")}</td>
                        <td data-label="Updated timestamp">{display(job.updatedAt)}</td>
                        <td data-label="Next action">{display(job.nextAction, "none")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <aside className="insights-panel debug-jobs-detail" aria-label="Selected publish job details">
            {selectedJob ? (
              <>
                <section className="insight-card debug-jobs-detail-head">
                  <div>
                    <span>{formatPlatform(selectedJob.platform)}</span>
                    <h2>{display(selectedJob.merchant.name, "Unknown merchant")}</h2>
                    <p>
                      {selectedJob.statusLabel} · {selectedJob.attemptCount} attempts · next action {selectedJob.nextAction}
                    </p>
                  </div>
                  <button
                    className="secondary-action"
                    type="button"
                    onClick={() => copyTraceId(selectedJob.latestTraceId)}
                  >
                    Copy trace ID
                  </button>
                  {copyStatus && <small className="inline-pending">{copyStatus}</small>}
                </section>

                <section className="insight-card debug-jobs-section">
                  <div className="compact-head">
                    <h2>Approval snapshot summary</h2>
                    <span>v{selectedJob.approvalSnapshotSummary.versionNumber}</span>
                  </div>
                  <dl className="debug-jobs-meta">
                    <div>
                      <dt>Approver</dt>
                      <dd>
                        {display(selectedJob.approver.name)} · {display(selectedJob.approver.email)}
                      </dd>
                    </div>
                    <div>
                      <dt>Draft version</dt>
                      <dd>
                        {display(selectedJob.draftVersion.id)} · v{selectedJob.draftVersion.versionNumber || 1}
                      </dd>
                    </div>
                    <div>
                      <dt>Approved timestamp</dt>
                      <dd>{display(selectedJob.approvalSnapshotSummary.approvedAt)}</dd>
                    </div>
                    <div>
                      <dt>Idempotency suffix</dt>
                      <dd>{display(selectedJob.approvalSnapshotSummary.idempotencyKeySuffix)}</dd>
                    </div>
                    <div>
                      <dt>Token boundary ref</dt>
                      <dd>
                        {display(selectedJob.tokenBoundaryRef.id)} · {display(selectedJob.tokenBoundaryRef.visibility, "redacted")}
                      </dd>
                    </div>
                  </dl>
                </section>

                <section className="insight-card debug-jobs-section">
                  <div className="compact-head">
                    <h2>Attempts</h2>
                    <span>{selectedJob.attempts.length}</span>
                  </div>
                  <div className="debug-jobs-attempts">
                    {selectedJob.attempts.map((attempt, index) => (
                      <article key={attemptKey(attempt, index)}>
                        <header>
                          <strong>Attempt {attempt.attemptNumber || index + 1}</strong>
                          <span className={statusClass(attempt.status)}>{attempt.statusLabel || getStatusLabel(attempt.status)}</span>
                        </header>
                        <dl className="debug-jobs-meta">
                          <div>
                            <dt>Trace ID</dt>
                            <dd className="debug-jobs-mono">{display(attempt.traceId)}</dd>
                          </div>
                          <div>
                            <dt>Request digest</dt>
                            <dd className="debug-jobs-mono">{display(attempt.requestDigest)}</dd>
                          </div>
                          <div>
                            <dt>Error class</dt>
                            <dd>{display(attempt.errorClass, "none")}</dd>
                          </div>
                          <div>
                            <dt>Next action</dt>
                            <dd>{display(attempt.nextAction, "none")}</dd>
                          </div>
                          <div>
                            <dt>Started</dt>
                            <dd>{display(attempt.startedAt)}</dd>
                          </div>
                          <div>
                            <dt>Finished</dt>
                            <dd>{display(attempt.finishedAt)}</dd>
                          </div>
                        </dl>
                        <RedactedDiagnostics rows={attempt.diagnostics} />
                      </article>
                    ))}
                  </div>
                </section>

                <section className="insight-card debug-jobs-section">
                  <div className="compact-head">
                    <h2>Append-only events</h2>
                    <span>{selectedJob.events.length}</span>
                  </div>
                  <div className="debug-jobs-events">
                    {selectedJob.events.map((event, index) => (
                      <article key={eventKey(event, index)}>
                        <time dateTime={event.timestamp}>{display(event.timestamp)}</time>
                        <strong>{event.statusLabel}</strong>
                        <p>{event.summary}</p>
                        <small>
                          {event.sourceActor} · Attempt {event.attemptNumber || "none"}
                        </small>
                      </article>
                    ))}
                  </div>
                </section>

                <section className="insight-card debug-jobs-section">
                  <div className="compact-head">
                    <h2>Media refs</h2>
                    <span>{selectedJob.mediaRefs.length}</span>
                  </div>
                  <ul className="debug-jobs-media">
                    {selectedJob.mediaRefs.map((media, index) => (
                      <li key={mediaKey(media, index)}>
                        <strong>{display(media.id, "media ref")}</strong>
                        <span>
                          {display(media.kind, "asset")} · {display(media.storageMode, "storage")}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="insight-card debug-jobs-section">
                  <h2 id="latest-redacted-diagnostics">Redacted provider diagnostics</h2>
                  <RedactedDiagnostics labelledBy="latest-redacted-diagnostics" rows={selectedJob.diagnostics} />
                </section>
              </>
            ) : (
              <section className="insight-card debug-jobs-section">
                <h2>No job selected</h2>
                <p>Select a publish job row to inspect attempts, events, and redacted diagnostics.</p>
              </section>
            )}
          </aside>
        </section>
      </main>
    </div>
  );
}
