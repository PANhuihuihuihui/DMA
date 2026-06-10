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
    if terminal_status == "published":
        store.record_publish_outcome(conn, job["id"], attempt["attempt"]["id"], snapshot)
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


def retry_fake_publish(conn, job_id, diagnostics_fixture=None):
    job = store.get_publish_job(conn, job_id)
    if job["status"] not in {"failed", "retry_needed"}:
        if job["status"] == "published":
            raise store.StoreError(409, "Publish job is already published; retry would duplicate the approved outcome.")
        raise store.StoreError(409, "Publish job is not in a retryable state.")

    approval = store.get_approval(conn, job["approval_id"])
    snapshot = json_loads(approval["snapshot_json"], {})
    attempt_number = store.next_attempt_number(conn, job["id"])

    store.append_publish_event(
        conn,
        job["id"],
        "queued",
        "Retry accepted for the approved snapshot.",
        "merchant",
        attempt_number,
    )
    store.update_publish_job_status(conn, job["id"], "publishing")
    store.append_publish_event(
        conn,
        job["id"],
        "publishing",
        "Fake publisher started deterministic retry attempt.",
        "fake_publisher",
        attempt_number,
    )

    attempt = run_fake_retry_attempt(conn, job["id"], snapshot, diagnostics_fixture)
    if attempt["terminalStatus"] == "published":
        store.record_publish_outcome(conn, job["id"], attempt["attempt"]["id"], snapshot)
    store.update_publish_job_status(conn, job["id"], attempt["terminalStatus"])
    store.append_publish_event(
        conn,
        job["id"],
        attempt["attemptStatus"],
        attempt["summary"],
        "fake_publisher",
        attempt_number,
    )
    if attempt["terminalStatus"] == "retry_needed":
        store.append_publish_event(
            conn,
            job["id"],
            "retry_needed",
            "Fake retry remains retryable.",
            "fake_publisher",
            attempt_number,
        )

    conn.commit()
    return {
        "status": "ok",
        "ctaCopy": "Retry publish",
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
                "provider": "fake",
                "providerDisplayName": "fake",
                "platform": "facebook",
                "mode": "fake",
                "result": "published",
                "errorClass": "none",
                "nextRecommendedAction": "none",
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
                "provider": "fake",
                "providerDisplayName": "fake",
                "platform": "tiktok",
                "mode": "fake",
                "result": "retry_needed",
                "errorClass": "platform_transient",
                "nextRecommendedAction": "retry_publish",
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
                "provider": "fake",
                "providerDisplayName": "fake",
                "platform": platform or "unknown",
                "mode": "fake",
                "result": "manual_fallback_required",
                "errorClass": "unsupported_platform",
                "nextRecommendedAction": "manual_fallback",
                "nextAction": "manual_fallback",
            },
        }

    attempt = store.create_publish_attempt(conn, job_id, snapshot, outcome)
    outcome["attempt"] = attempt
    return outcome


def run_fake_retry_attempt(conn, job_id, snapshot, diagnostics_fixture=None):
    platform = snapshot.get("platform") or "unknown"
    provider_diagnostics = diagnostics_fixture or {}
    outcome = {
        "attemptStatus": "published",
        "terminalStatus": "published",
        "retryClassification": "manual_retry",
        "summary": f"{platform.title()} fake retry completed with an idempotent local outcome.",
        "diagnostics": {
            "provider": "fake",
            "providerDisplayName": "fake",
            "platform": platform,
            "mode": "fake",
            "result": "published",
            "errorClass": "none",
            "providerDiagnostics": provider_diagnostics,
            "nextRecommendedAction": "none",
            "nextAction": "none",
        },
    }
    attempt = store.create_publish_attempt(conn, job_id, snapshot, outcome)
    outcome["attempt"] = attempt
    return outcome
