"""
MiniMax image-01 image generation adapter.

provider_key: "minimax"
capability:   "image"
registry_key: "minimax:image"

API contract (synchronous — result available immediately from submit):
  POST https://api.minimaxi.chat/v1/image_generation

Because MiniMax image generation is synchronous, submit() encodes the
completed result in the returned provider_job_id ("sync:{json}") so
poll() can return "succeeded" on the first call without any extra I/O.
"""
import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

_MINIMAX_BASE = "https://api.minimaxi.chat"


def _minimax_api_key() -> str:
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not key:
        raise EnvironmentError("MINIMAX_API_KEY is not set")
    return key


def _post(path: str, body: dict) -> dict:
    url = f"{_MINIMAX_BASE}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {_minimax_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"MiniMax {path} returned HTTP {exc.code}: {body_text[:400]}"
        ) from exc


class MiniMaxImageAdapter:
    """
    MiniMax image-01 synchronous image generation adapter.

    submit() calls the API, encodes the result into the returned provider_job_id
    so poll() can resolve immediately without a second network call.
    """

    def submit(self, model_key: str, prompt: str, request: dict, settings: dict) -> str:
        """
        Call MiniMax image generation synchronously. Encodes the full result in
        the returned provider_job_id as "sync:{json}" so poll() is instant.
        """
        payload: dict = {
            "model": model_key,
            "prompt": prompt,
        }

        aspect_ratio = settings.get("aspectRatio") or request.get("aspectRatio")
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio

        n = int(settings.get("slideCount") or request.get("n") or 1)
        if n > 1:
            payload["n"] = n

        logger.info(
            "MiniMaxImageAdapter.submit model=%s prompt_len=%d n=%d",
            model_key, len(prompt), n,
        )

        response = _post("/v1/image_generation", payload)
        base_id = response.get("id") or "minimax-image"

        items = response.get("data") or []
        if not items:
            raise RuntimeError(f"MiniMax image_generation returned no data: {response}")

        outputs = []
        for item in items:
            image_url = item.get("url") or ""
            b64 = item.get("b64_json") or ""
            storage_ref = image_url if image_url else f"data:image/jpeg;base64,{b64}"
            outputs.append(
                {
                    "kind": "image",
                    "storageRef": storage_ref,
                    "previewRef": storage_ref,
                    "metadata": {
                        "providerJobId": base_id,
                        "index": item.get("index", 0),
                        "model": model_key,
                    },
                }
            )

        encoded = json.dumps({"id": base_id, "outputs": outputs}, separators=(",", ":"))
        return f"sync:{encoded}"

    def poll(self, provider_job_id: str) -> dict:
        """
        MiniMax image generation is synchronous; submit() encoded the result.
        Any provider_job_id that starts with "sync:" resolves immediately.
        """
        if provider_job_id.startswith("sync:"):
            try:
                payload = json.loads(provider_job_id[5:])
            except json.JSONDecodeError as exc:
                return {
                    "status": "failed",
                    "failureReason": f"corrupt sync payload: {exc}",
                    "diagnostics": {},
                }
            return {
                "status": "succeeded",
                "outputs": payload.get("outputs", []),
                "diagnostics": {"providerJobId": payload.get("id"), "providerStatus": "completed"},
            }

        return {
            "status": "failed",
            "failureReason": f"unexpected provider_job_id format: {provider_job_id[:80]!r}",
            "diagnostics": {},
        }

    def cancel(self, provider_job_id: str) -> None:
        """MiniMax image generation is synchronous; nothing to cancel."""
        logger.info("MiniMaxImageAdapter.cancel: synchronous job, nothing to cancel (%s)", provider_job_id[:40])
