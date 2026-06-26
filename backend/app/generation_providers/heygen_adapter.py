"""
HeyGen v2 UGC avatar video adapter.

provider_key: "heygen"
capability:   "avatar_video"
registry_key: "heygen:avatar_video"

API contract:
  submit  -> POST /v2/video/generate
  poll    -> GET  /v1/video_status.get?video_id={id}
"""
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

_HEYGEN_BASE = "https://api.heygen.com"


def _heygen_api_key() -> str:
    key = os.environ.get("HEYGEN_API_KEY", "").strip()
    if not key:
        raise EnvironmentError("HEYGEN_API_KEY is not set")
    return key


def _post(path: str, body: dict) -> dict:
    url = f"{_HEYGEN_BASE}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "X-Api-Key": _heygen_api_key(),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HeyGen {path} returned HTTP {exc.code}: {body_text[:400]}"
        ) from exc


def _get(path: str, params: dict | None = None) -> dict:
    url = f"{_HEYGEN_BASE}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"X-Api-Key": _heygen_api_key()},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HeyGen {path} returned HTTP {exc.code}: {body_text[:400]}"
        ) from exc


class HeyGenAvatarAdapter:
    """HeyGen v2 UGC avatar video generation adapter (async submit/poll)."""

    def submit(self, model_key: str, prompt: str, request: dict, settings: dict) -> str:
        """
        Submit an avatar video generation job. Returns the HeyGen video_id.
        """
        avatar_id = settings.get("avatarId") or request.get("avatar") or "avatar_default"
        script_text = settings.get("script") or request.get("script") or prompt
        voiceover = settings.get("voiceover") or request.get("voiceover") or {}

        voice_id = (
            voiceover.get("voiceId")
            if isinstance(voiceover, dict)
            else "en-US-AriaNeural"
        )

        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script_text,
                        "voice_id": voice_id or "en-US-AriaNeural",
                    },
                    "background": {"type": "color", "value": "#f0f0f0"},
                }
            ],
            "dimension": {"width": 1080, "height": 1920},
        }

        logger.info("HeyGenAvatarAdapter.submit avatar_id=%s script_len=%d", avatar_id, len(script_text))
        response = _post("/v2/video/generate", payload)
        data = response.get("data") or {}
        video_id = data.get("video_id")
        if not video_id:
            raise RuntimeError(f"HeyGen /v2/video/generate response missing video_id: {response}")
        return video_id

    def poll(self, provider_job_id: str) -> dict:
        """
        Poll job status. Returns normalized dict with:
          status: "running" | "succeeded" | "failed"
          outputs: list  (on succeeded)
          failureReason: str  (on failed)
          diagnostics: dict
        """
        response = _get("/v1/video_status.get", {"video_id": provider_job_id})
        data = response.get("data") or {}
        raw_status = data.get("status", "")

        if raw_status in ("pending", "processing", "waiting"):
            return {"status": "running", "diagnostics": {"providerStatus": raw_status}}

        if raw_status == "completed":
            video_url = data.get("video_url") or ""
            thumbnail_url = data.get("thumbnail_url") or ""
            outputs = [
                {
                    "kind": "avatar_video",
                    "storageRef": video_url,
                    "previewRef": thumbnail_url or video_url,
                    "metadata": {
                        "providerJobId": provider_job_id,
                        "rawStatus": raw_status,
                        "durationSeconds": data.get("duration"),
                    },
                }
            ]
            return {"status": "succeeded", "outputs": outputs, "diagnostics": {"providerStatus": raw_status}}

        reason = data.get("error") or f"provider status={raw_status!r}"
        return {
            "status": "failed",
            "failureReason": reason,
            "diagnostics": {"providerStatus": raw_status, "providerData": str(data)[:400]},
        }

    def cancel(self, provider_job_id: str) -> None:
        """HeyGen has no cancel endpoint; log and ignore."""
        logger.info("HeyGenAvatarAdapter.cancel: no cancel endpoint for %s", provider_job_id)
