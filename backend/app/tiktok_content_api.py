"""Small, transport-injectable boundary for TikTok Content Posting API v2.

The client returns only normalized provider facts; callers must never persist raw
responses, bearer tokens, or upload URLs.
"""
import json
from urllib import error, request

from backend.app import store

API_BASE = "https://open.tiktokapis.com"


class TikTokContentApi:
    def __init__(self, transport=None, api_base=API_BASE, timeout=15):
        self.transport = transport
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def _request(self, method, path, token, body=None):
        url = f"{self.api_base}{path}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        try:
            if self.transport:
                payload = self.transport(method=method, url=url, headers=headers, body=body)
            else:
                payload = self._http(method, url, headers, body)
        except store.StoreError:
            raise
        except (OSError, TimeoutError) as exc:
            raise store.StoreError(502, "TikTok Content Posting API is unavailable.") from exc
        except Exception as exc:
            raise store.StoreError(502, "TikTok Content Posting API request failed.") from exc
        return self._envelope(payload)

    def _http(self, method, url, headers, body):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = request.Request(url, data=data, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8") or "{}")
        except error.HTTPError as exc:
            exc.close()
            raise store.StoreError(exc.code, "TikTok Content Posting API rejected the request.") from exc
        except json.JSONDecodeError as exc:
            raise store.StoreError(502, "TikTok Content Posting API returned malformed JSON.") from exc

    def _envelope(self, payload):
        if not isinstance(payload, dict):
            raise store.StoreError(502, "TikTok Content Posting API returned malformed JSON.")
        error_info = payload.get("error") or {}
        code = error_info.get("code")
        if code and code not in {"ok", "OK", 0, "0"}:
            status = int(error_info.get("http_status") or 502)
            if str(code).lower() in {"access_token_invalid", "access_token_expired", "unauthorized"}:
                status = 401
            elif str(code).lower() in {"scope_not_authorized", "permission_denied"}:
                status = 403
            elif str(code).lower() in {"rate_limit_exceeded", "rate_limited"}:
                status = 429
            exc = store.StoreError(status, "TikTok Content Posting API rejected the request.")
            exc.tiktok_error_code = str(code)
            raise exc
        data = payload.get("data")
        if not isinstance(data, dict):
            raise store.StoreError(502, "TikTok Content Posting API returned malformed JSON.")
        return data

    def creator_info(self, token):
        return self._request("POST", "/v2/post/publish/creator_info/query/", token, {})

    def init_inbox_video(self, token, source_info):
        return self._request("POST", "/v2/post/publish/inbox/video/init/", token, {"source_info": source_info})

    def init_direct_post_video(self, token, post_info, source_info):
        return self._request("POST", "/v2/post/publish/video/init/", token, {"post_info": post_info, "source_info": source_info})

    def fetch_status(self, token, publish_id):
        return self._request("POST", "/v2/post/publish/status/fetch/", token, {"publish_id": publish_id})


def normalized_creator_info(data, version, fetched_at):
    options = data.get("privacy_level_options") or []
    if not isinstance(options, list) or not options:
        raise store.StoreError(502, "TikTok creator settings were malformed.")
    return {
        "version": version,
        "fetchedAt": fetched_at,
        "creatorNickname": data.get("creator_nickname") or "TikTok creator",
        "privacyLevelOptions": [str(item) for item in options],
        "commentDisabled": bool(data.get("comment_disabled", False)),
        "duetDisabled": bool(data.get("duet_disabled", False)),
        "stitchDisabled": bool(data.get("stitch_disabled", False)),
        "maxVideoPostDurationSec": int(data.get("max_video_post_duration_sec") or 600),
        "disclosureRequiredForCommercial": bool(data.get("commercial_content_toggle", False)),
    }


def normalized_publish_id(data):
    publish_id = data.get("publish_id")
    if not isinstance(publish_id, str) or not publish_id:
        raise store.StoreError(502, "TikTok did not return a publish ID.")
    return publish_id
