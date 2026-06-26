"""
OpenAI Sora 2 text-to-video adapter.

provider_key: "openai"
capability:   "video"
registry_key: "openai:video"

API contract:
  submit  -> POST /v1/video/generations
  poll    -> GET  /v1/video/generations/{id}
"""
import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

_OPENAI_BASE = "https://api.openai.com"


def _openai_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise EnvironmentError("OPENAI_API_KEY is not set")
    return key


def _post(path: str, body: dict) -> dict:
    url = f"{_OPENAI_BASE}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {_openai_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenAI {path} returned HTTP {exc.code}: {body_text[:400]}"
        ) from exc


def _get(path: str) -> dict:
    url = f"{_OPENAI_BASE}{path}"
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {_openai_api_key()}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenAI {path} returned HTTP {exc.code}: {body_text[:400]}"
        ) from exc


class OpenAIVideoAdapter:
    """Sora 2 video generation adapter (async submit/poll)."""

    def submit(self, model_key: str, prompt: str, request: dict, settings: dict) -> str:
        """
        Submit a video generation job. Returns the provider job ID.
        """
        payload = {
            "model": model_key,
            "prompt": prompt,
        }
        aspect_ratio = settings.get("aspectRatio") or request.get("aspectRatio")
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        duration = settings.get("durationSeconds") or request.get("durationSeconds")
        if duration:
            payload["duration"] = int(duration)

        logger.info("OpenAIVideoAdapter.submit model=%s prompt_len=%d", model_key, len(prompt))
        response = _post("/v1/video/generations", payload)
        job_id = response.get("id")
        if not job_id:
            raise RuntimeError(f"OpenAI video generation response missing 'id': {response}")
        return job_id

    def poll(self, provider_job_id: str) -> dict:
        """
        Poll job status. Returns dict with keys:
          status: "running" | "succeeded" | "failed"
          outputs: list of {kind, storageRef, previewRef, metadata}  (on succeeded)
          failureReason: str  (on failed)
          diagnostics: dict
        """
        response = _get(f"/v1/video/generations/{provider_job_id}")
        raw_status = response.get("status", "")

        if raw_status in ("queued", "in_progress", "processing"):
            return {"status": "running", "diagnostics": {"providerStatus": raw_status}}

        if raw_status == "completed":
            video_url = response.get("url") or (
                (response.get("output") or {}).get("url") or ""
            )
            outputs = [
                {
                    "kind": "video",
                    "storageRef": video_url,
                    "previewRef": video_url,
                    "metadata": {"providerJobId": provider_job_id, "rawStatus": raw_status},
                }
            ]
            return {"status": "succeeded", "outputs": outputs, "diagnostics": {"providerStatus": raw_status}}

        return {
            "status": "failed",
            "failureReason": response.get("error", {}).get("message") or f"provider status={raw_status!r}",
            "diagnostics": {"providerStatus": raw_status, "providerResponse": str(response)[:400]},
        }

    def cancel(self, provider_job_id: str) -> None:
        """Cancel a running generation (best-effort)."""
        try:
            _post(f"/v1/video/generations/{provider_job_id}/cancel", {})
        except Exception as exc:
            logger.warning("OpenAIVideoAdapter.cancel failed for %s: %s", provider_job_id, exc)
