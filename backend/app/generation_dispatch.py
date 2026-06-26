"""
Async generation dispatch engine.

Exports two functions called by server.py:
  start_async_dispatch(db_path, job_id)
  retry_generation_job(db_path, merchant_id, job_id, dispatch)

The dispatch loop owns job/attempt status transitions and credit settle/release.
Provider adapters live in backend/app/generation_providers/ and are registered
in _PROVIDER_REGISTRY below.
"""
import logging
import threading
import time
from contextlib import closing

from backend.app.contracts import json_dumps, json_loads, new_id, utc_now
from backend.app import store
from backend.app.generation_providers import ADAPTER_REGISTRY as _ADAPTER_REGISTRY

logger = logging.getLogger(__name__)

# Registry: "{provider_key}:{capability}" -> adapter class.
# provider_key alone is not unique — "openai" covers both image and video models.
# Populated from generation_providers package.
_PROVIDER_REGISTRY: dict = _ADAPTER_REGISTRY

# Exponential backoff settings for polling.
_POLL_MIN_INTERVAL = 2.0
_POLL_MAX_INTERVAL = 30.0
_POLL_BACKOFF_FACTOR = 2.0

# Maximum wall-clock seconds a single dispatch attempt may run before being
# marked failed (safety valve for hung providers).
_MAX_ATTEMPT_SECONDS = 900


def _load_job_row(conn, job_id):
    row = conn.execute(
        "select * from generation_jobs where id = ?", (job_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"generation job not found: {job_id}")
    return row


def _load_active_attempt(conn, job_id):
    """Return the most recent non-terminal attempt row, or None."""
    return conn.execute(
        """
        select * from generation_attempts
        where generation_job_id = ?
        order by attempt_number desc, created_at desc
        limit 1
        """,
        (job_id,),
    ).fetchone()


def _update_job_status(conn, job_id, status, failure_reason=None):
    now = utc_now()
    conn.execute(
        "update generation_jobs set status = ?, failure_reason = ?, updated_at = ? where id = ?",
        (status, failure_reason, now, job_id),
    )
    conn.commit()


def _update_attempt_status(conn, attempt_id, status, diagnostics=None):
    now = utc_now()
    conn.execute(
        "update generation_attempts set status = ?, diagnostics_json = ?, updated_at = ? where id = ?",
        (status, json_dumps(diagnostics or {}), now, attempt_id),
    )
    conn.commit()


def _insert_output(conn, job_id, output_kind, storage_ref, preview_ref, metadata):
    now = utc_now()
    output_id = new_id("generation_output")
    conn.execute(
        """
        insert into generation_outputs
          (id, generation_job_id, output_kind, storage_ref, preview_ref, metadata_json, status, created_at, updated_at)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            output_id,
            job_id,
            output_kind,
            storage_ref,
            preview_ref,
            json_dumps(metadata or {}),
            "ready",
            now,
            now,
        ),
    )
    conn.commit()
    return output_id


def _run_dispatch(db_path: str, job_id: str) -> None:
    """Worker executed in a background thread per job dispatch."""
    try:
        _dispatch_job(db_path, job_id)
    except Exception:
        logger.exception("generation_dispatch: unhandled error for job %s", job_id)
        try:
            with closing(store.connect(db_path)) as conn:
                job = _load_job_row(conn, job_id)
                if job["status"] not in ("succeeded", "failed"):
                    _release_on_failure(conn, job, "internal dispatch error")
        except Exception:
            logger.exception("generation_dispatch: failed to release credits for job %s", job_id)


def _release_on_failure(conn, job, reason: str) -> None:
    _update_job_status(conn, job["id"], "failed", failure_reason=reason)
    attempt = _load_active_attempt(conn, job["id"])
    if attempt and attempt["status"] not in ("succeeded", "failed"):
        _update_attempt_status(conn, attempt["id"], "failed", {"failureReason": reason})
    if job["reserved_credits"] and job["reserved_credits"] > 0:
        store.release_generation_credits(conn, job["merchant_id"], job["id"], job["reserved_credits"])
        conn.commit()


def _dispatch_job(db_path: str, job_id: str) -> None:
    with closing(store.connect(db_path)) as conn:
        job = _load_job_row(conn, job_id)
        if job["status"] in ("succeeded", "failed"):
            logger.info("generation_dispatch: job %s already terminal (%s), skipping", job_id, job["status"])
            return

        provider_key = job["provider_key"]
        capability = job["capability"]
        registry_key = f"{provider_key}:{capability}"
        adapter_cls = _PROVIDER_REGISTRY.get(registry_key)
        if adapter_cls is None:
            _release_on_failure(conn, job, f"no adapter registered for {registry_key!r}")
            return

        attempt = _load_active_attempt(conn, job_id)
        if attempt is None:
            _release_on_failure(conn, job, "no attempt record found")
            return

        _update_job_status(conn, job_id, "running")
        _update_attempt_status(conn, attempt["id"], "running")

        request_payload = json_loads(job["request_json"], {})
        settings = json_loads(job["settings_json"], {})

    adapter = adapter_cls()
    start_time = time.monotonic()

    try:
        provider_job_id = adapter.submit(
            model_key=job["model_key"],
            prompt=job["prompt"],
            request=request_payload,
            settings=settings,
        )
    except Exception as exc:
        logger.exception("generation_dispatch: submit failed for job %s", job_id)
        with closing(store.connect(db_path)) as conn:
            job = _load_job_row(conn, job_id)
            _release_on_failure(conn, job, f"submit error: {exc}")
        return

    # Poll with exponential backoff until terminal or timeout.
    interval = _POLL_MIN_INTERVAL
    while True:
        if time.monotonic() - start_time > _MAX_ATTEMPT_SECONDS:
            with closing(store.connect(db_path)) as conn:
                job = _load_job_row(conn, job_id)
                _release_on_failure(conn, job, "generation timed out")
            return

        time.sleep(interval)
        interval = min(interval * _POLL_BACKOFF_FACTOR, _POLL_MAX_INTERVAL)

        try:
            result = adapter.poll(provider_job_id)
        except Exception as exc:
            logger.warning("generation_dispatch: poll error for job %s: %s", job_id, exc)
            continue

        status = result.get("status")
        if status == "running":
            continue

        if status == "succeeded":
            outputs = result.get("outputs") or []
            with closing(store.connect(db_path)) as conn:
                job = _load_job_row(conn, job_id)
                for output in outputs:
                    _insert_output(
                        conn,
                        job_id,
                        output.get("kind", "video"),
                        output.get("storageRef", ""),
                        output.get("previewRef", ""),
                        output.get("metadata", {}),
                    )
                attempt_row = _load_active_attempt(conn, job_id)
                if attempt_row:
                    _update_attempt_status(conn, attempt_row["id"], "succeeded", result.get("diagnostics"))
                _update_job_status(conn, job_id, "succeeded")
                store.settle_generation_credits(conn, job["merchant_id"], job_id, job["reserved_credits"])
            logger.info("generation_dispatch: job %s succeeded", job_id)
            return

        # Any other status is treated as failure.
        reason = result.get("failureReason") or f"provider status={status!r}"
        with closing(store.connect(db_path)) as conn:
            job = _load_job_row(conn, job_id)
            attempt_row = _load_active_attempt(conn, job_id)
            if attempt_row:
                _update_attempt_status(conn, attempt_row["id"], "failed", result.get("diagnostics"))
            _release_on_failure(conn, job, reason)
        logger.info("generation_dispatch: job %s failed: %s", job_id, reason)
        return


def start_async_dispatch(db_path: str, job_id: str) -> None:
    """Spawn a background thread to run the generation job. Non-blocking."""
    t = threading.Thread(
        target=_run_dispatch,
        args=(db_path, job_id),
        daemon=True,
        name=f"gen-dispatch-{job_id}",
    )
    t.start()


def retry_generation_job(db_path: str, merchant_id: str, job_id: str, dispatch: bool = True) -> dict:
    """
    Create a new attempt for an existing job and optionally dispatch it.
    Returns the serialized job + credits summary (same shape as create_generation_job).
    """
    with closing(store.connect(db_path)) as conn:
        job = store.get_generation_job(conn, merchant_id, job_id)
        if job["status"] not in ("failed",):
            raise store.StoreError(409, f"Job cannot be retried in status={job['status']!r}.")

        now = utc_now()
        existing_attempts = conn.execute(
            "select count(*) from generation_attempts where generation_job_id = ?",
            (job_id,),
        ).fetchone()[0]
        attempt_id = new_id("generation_attempt")
        conn.execute(
            """
            insert into generation_attempts
              (id, generation_job_id, attempt_number, status, diagnostics_json, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (attempt_id, job_id, existing_attempts + 1, "queued", "{}", now, now),
        )
        _update_job_status(conn, job_id, "queued")
        result = {
            "job": store.serialize_generation_job(conn, store.get_generation_job(conn, merchant_id, job_id)),
            "credits": store.get_generation_credit_summary(conn, merchant_id),
        }

    if dispatch:
        start_async_dispatch(db_path, job_id)

    return result


def dispatch_generation_job(
    db_path: str,
    job_id: str,
    adapter_registry: dict | None = None,
    poll_interval_seconds: float = 2.0,
) -> dict:
    """
    Synchronous carousel-generation dispatch for testing and Phase 11 compatibility.

    adapter_registry: {(provider_key, capability): adapter_instance}
    Returns the serialized job dict (includes carousel handoff fields when the
    capability is 'image' and workflowType is 'carousel').
    """
    with closing(store.connect(db_path)) as conn:
        job_row = _load_job_row(conn, job_id)
        merchant_id = job_row["merchant_id"]
        provider_key = job_row["provider_key"]
        capability = job_row["capability"]

        registry = adapter_registry or {}
        adapter = registry.get((provider_key, capability))
        if adapter is None:
            raise ValueError(
                f"dispatch_generation_job: no adapter for ({provider_key!r}, {capability!r})"
            )

        model_row = conn.execute(
            "select * from generation_model_catalog where id = ?",
            (job_row["model_catalog_id"],),
        ).fetchone()

        _update_job_status(conn, job_id, "running")
        attempt = _load_active_attempt(conn, job_id)
        if attempt:
            _update_attempt_status(conn, attempt["id"], "running")

    # Call the legacy carousel adapter synchronously — no polling.
    result = adapter.submit(job_row, model_row, db_path)

    job_status = result.get("job_status", "failed")

    with closing(store.connect(db_path)) as conn:
        job_row = _load_job_row(conn, job_id)
        now = utc_now()

        if job_status == "succeeded":
            output_rows = []
            for out in result.get("outputs") or []:
                storage_ref = out.get("storage_ref") or out.get("storageRef") or ""
                preview_ref = out.get("preview_ref") or out.get("previewRef") or ""
                metadata = dict(out.get("metadata") or {})
                output_id = _insert_output(conn, job_id, out.get("output_kind", "image"), storage_ref, preview_ref, metadata)
                output_row = conn.execute(
                    "select * from generation_outputs where id = ?", (output_id,)
                ).fetchone()
                output_rows.append(output_row)

            request_payload = json_loads(job_row["request_json"], {})
            if request_payload.get("workflowType") == "carousel" and output_rows:
                brand_row = store.get_latest_brand_kit_row(conn, merchant_id)
                slide_roles = list(request_payload.get("slideRoles") or store.CAROUSEL_SLIDE_ROLES)
                slide_plan = [
                    {
                        "role": slide_roles[i] if i < len(slide_roles) else f"slide_{i+1}",
                        "headline": f"Slide {i+1}",
                        "body": "",
                        "ctaLabel": "Review and publish" if i == len(output_rows) - 1 else "",
                        "imagePrompt": job_row["prompt"],
                    }
                    for i in range(len(output_rows))
                ]
                store.materialize_carousel_package(conn, merchant_id, job_row, brand_row, slide_plan, output_rows)
                conn.commit()

            attempt_row = _load_active_attempt(conn, job_id)
            if attempt_row:
                _update_attempt_status(conn, attempt_row["id"], "succeeded", result.get("diagnostics"))
            _update_job_status(conn, job_id, "succeeded")
            if job_row["reserved_credits"] and job_row["reserved_credits"] > 0:
                store.settle_generation_credits(conn, merchant_id, job_id, job_row["reserved_credits"])
                conn.commit()

            serialized = store.serialize_generation_job(conn, _load_job_row(conn, job_id))
            return serialized
        else:
            reason = result.get("error") or result.get("failureReason") or f"adapter returned status={job_status!r}"
            _release_on_failure(conn, job_row, reason)
            raise RuntimeError(f"dispatch_generation_job failed for {job_id}: {reason}")
