import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { createReviewFeedback, loadReviewPackage } from "../api/publishingClient.js";

const emptyReview = {
  reviewLink: {},
  creative: {},
  brandKit: {},
  calendarSlot: null,
  feedback: [],
};

const safeReviewText = (value, fallback = "") => {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map(safeReviewText).filter(Boolean).join(" ");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, nestedValue]) => `${key}: ${safeReviewText(nestedValue)}`)
      .filter(Boolean)
      .join(" · ");
  }
  return fallback;
};

export function ReviewRoute() {
  const { token = "" } = useParams();
  const [review, setReview] = useState(emptyReview);
  const [status, setStatus] = useState("loading");
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    authorName: "Karen Li",
    body: "Looks good. Please keep the call CTA and same-week offer clear.",
  });
  const [pendingType, setPendingType] = useState("");

  useEffect(() => {
    let active = true;
    setStatus("loading");
    setMessage("");
    loadReviewPackage(token)
      .then((payload) => {
        if (!active) return;
        setReview({ ...emptyReview, ...payload });
        setStatus("ready");
      })
      .catch((error) => {
        if (!active) return;
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "Review link could not be loaded.");
      });
    return () => {
      active = false;
    };
  }, [token]);

  const submitFeedback = async (feedbackType) => {
    setPendingType(feedbackType);
    setMessage("");
    try {
      const payload = await createReviewFeedback(token, {
        authorName: form.authorName,
        authorRole: "owner",
        feedbackType,
        body: form.body,
      });
      setReview({ ...emptyReview, ...payload.review });
      setMessage(feedbackType === "change_request" ? "Change request sent." : "Approval note sent.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Feedback could not be sent.");
    } finally {
      setPendingType("");
    }
  };

  const creative = review.creative || {};
  const brandColors = Array.isArray(review.brandKit?.colors) ? review.brandKit.colors : [];
  const feedback = Array.isArray(review.feedback) ? review.feedback : [];

  return (
    <main className="review-page">
      <section className="review-shell">
        <header className="review-header">
          <div>
            <p className="app-kicker">Client review link</p>
            <h1>Review this post inside LocalPilot</h1>
            <p>
              Predis-style shared approval link for owner comments, change requests, and final approval notes.
              No access token, ad account, or internal workspace login is needed for this demo review.
            </p>
          </div>
          <Link to="/app?module=approval-queue">Back to workspace</Link>
        </header>

        {status === "error" && (
          <section className="review-state-card">
            <span>Review unavailable</span>
            <h2>{message}</h2>
            <p>Ask the LocalPilot operator to generate a fresh review link from the Approval Queue.</p>
          </section>
        )}

        {status === "loading" && (
          <section className="review-state-card">
            <span>Loading</span>
            <h2>Preparing the review package...</h2>
            <p>LocalPilot is loading the creative, schedule, proof hook, and feedback thread from the backend.</p>
          </section>
        )}

        {status === "ready" && (
          <div className="review-grid">
            <article className="review-creative-card">
              <span>{safeReviewText(creative.platform, "Social post").replaceAll("_", " ")}</span>
              <h2>{safeReviewText(creative.title, "Social post")}</h2>
              <p>{safeReviewText(creative.caption)}</p>
              <div className="review-brand-strip">
                {brandColors.slice(0, 4).map((color) => (
                  <i key={color} style={{ background: color }} />
                ))}
              </div>
              <dl>
                <div>
                  <dt>Format</dt>
                  <dd>{safeReviewText(creative.format)}</dd>
                </div>
                <div>
                  <dt>CTA</dt>
                  <dd>{safeReviewText(creative.cta)}</dd>
                </div>
                <div>
                  <dt>Schedule</dt>
                  <dd>{safeReviewText(review.calendarSlot?.slotLabel || creative.scheduleSlot)}</dd>
                </div>
                <div>
                  <dt>Proof hook</dt>
                  <dd>{safeReviewText(creative.proofHook)}</dd>
                </div>
              </dl>
            </article>

            <aside className="review-feedback-card">
              <span>Approval feedback</span>
              <h2>Leave a note for this exact post</h2>
              <label>
                Reviewer name
                <input
                  value={form.authorName}
                  onChange={(event) => setForm((current) => ({ ...current, authorName: event.target.value }))}
                />
              </label>
              <label>
                Feedback
                <textarea
                  value={form.body}
                  onChange={(event) => setForm((current) => ({ ...current, body: event.target.value }))}
                />
              </label>
              <div className="review-actions">
                <button
                  type="button"
                  disabled={pendingType === "approval_note"}
                  onClick={() => submitFeedback("approval_note")}
                >
                  Send approval note
                </button>
                <button
                  type="button"
                  disabled={pendingType === "change_request"}
                  onClick={() => submitFeedback("change_request")}
                >
                  Request changes
                </button>
              </div>
              {message && <p className="review-message">{message}</p>}
            </aside>

            <section className="review-thread">
              <div>
                <p className="app-kicker">Feedback thread</p>
                <h2>{feedback.length} comments attached to this review</h2>
              </div>
              <div className="review-thread-list">
                {feedback.map((item) => (
                  <article key={item.id}>
                    <span>{safeReviewText(item.feedbackType).replaceAll("_", " ")}</span>
                    <strong>{safeReviewText(item.authorName)}</strong>
                    <p>{safeReviewText(item.body)}</p>
                    <small>{safeReviewText(item.status)}</small>
                  </article>
                ))}
              </div>
            </section>
          </div>
        )}
      </section>
    </main>
  );
}
