from backend.app import store
from backend.app.contracts import json_loads


CTA_COPY = "Queue fake publish"


def queue_fake_publish(conn, approval_id):
    approval = store.get_approval(conn, approval_id)
    job = store.create_publish_job(conn, approval)
    if store.next_attempt_number(conn, job["id"]) > 1:
        conn.commit()
        return {
            "status": "ok",
            "ctaCopy": CTA_COPY,
            "job": store.serialize_publish_job(conn, job),
        }

    snapshot = json_loads(approval["snapshot_json"], {})
    store.append_publish_event(
        conn,
        job["id"],
        "approved",
        "Approved snapshot accepted for fake publish.",
        "merchant",
        1,
    )
    store.append_publish_event(
        conn,
        job["id"],
        "queued",
        "Fake publish job queued from the approved snapshot.",
        "system",
        1,
    )
    store.update_publish_job_status(conn, job["id"], "publishing")
    store.append_publish_event(
        conn,
        job["id"],
        "publishing",
        "Fake publisher started deterministic local attempt.",
        "fake_publisher",
        1,
    )

    attempt = run_fake_attempt(conn, job["id"], snapshot)
    terminal_status = attempt["terminalStatus"]
    store.update_publish_job_status(conn, job["id"], terminal_status)
    store.append_publish_event(
        conn,
        job["id"],
        attempt["attemptStatus"],
        attempt["summary"],
        "fake_publisher",
        1,
    )
    if terminal_status == "retry_needed":
        store.append_publish_event(
            conn,
            job["id"],
            "retry_needed",
            "Fake TikTok publishing requires a retryable follow-up attempt.",
            "fake_publisher",
            1,
        )

    conn.commit()
    return {
        "status": "ok",
        "ctaCopy": CTA_COPY,
        "job": store.get_serialized_publish_job(conn, job["id"]),
    }


def run_fake_attempt(conn, job_id, snapshot):
    platform = snapshot.get("platform")
    if platform == "facebook":
        outcome = {
            "attemptStatus": "published",
            "terminalStatus": "published",
            "retryClassification": "none",
            "summary": "Facebook fake publish completed without a provider network call.",
            "diagnostics": {
                "provider": "facebook",
                "mode": "fake",
                "result": "published",
                "nextAction": "none",
            },
        }
    elif platform == "tiktok":
        outcome = {
            "attemptStatus": "failed",
            "terminalStatus": "retry_needed",
            "retryClassification": "automatic_retry_needed",
            "summary": "TikTok fake publish failed deterministically and is retryable.",
            "diagnostics": {
                "provider": "tiktok",
                "mode": "fake",
                "result": "retry_needed",
                "errorClass": "platform_transient",
                "nextAction": "retry_publish",
            },
        }
    else:
        outcome = {
            "attemptStatus": "failed",
            "terminalStatus": "manual_fallback_required",
            "retryClassification": "manual_review",
            "summary": "Unsupported fake platform requires manual fallback.",
            "diagnostics": {
                "provider": platform or "unknown",
                "mode": "fake",
                "result": "manual_fallback_required",
                "errorClass": "unsupported_platform",
                "nextAction": "manual_fallback",
            },
        }

    store.create_publish_attempt(conn, job_id, snapshot, outcome)
    return outcome
