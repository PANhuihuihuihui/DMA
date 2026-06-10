import copy
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.token_boundary import serialize_token_boundary_ref


LIFECYCLE_STATUSES = [
    "draft",
    "needs_review",
    "approved",
    "queued",
    "publishing",
    "published",
    "failed",
    "retry_needed",
    "manual_fallback_required",
]

FORBIDDEN_TERMS = [
    "access" + "_token",
    "refresh" + "_token",
    "author" + "ization",
    "coo" + "kie",
    "client" + "_secret",
    "api" + "_key",
    "oauth" + "_payload",
    "provider" + "_raw",
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_id(prefix):
    return f"{prefix}_{uuid4().hex[:16]}"


def redact(value):
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if any(term in normalized for term in FORBIDDEN_TERMS):
                redacted[key] = "[redacted]"
            else:
                redacted[key] = redact(item)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and any(term in value.lower() for term in FORBIDDEN_TERMS):
        return "[redacted]"
    return value


def json_loads(value, fallback=None):
    if value is None:
        return copy.deepcopy(fallback)
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return copy.deepcopy(fallback)


def json_dumps(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def idempotency_key(platform, draft_version_id, connected_channel_id):
    digest = hashlib.sha256(f"{platform}:{draft_version_id}:{connected_channel_id}".encode("utf-8")).hexdigest()
    return f"lp:{platform}:{digest[:32]}"


def request_digest(value):
    return "sha256:" + hashlib.sha256(json_dumps(redact(value)).encode("utf-8")).hexdigest()


def trace_id():
    return new_id("trace")


def serialize_media_asset(row):
    return {
        "mediaAssetId": row["id"],
        "storageMode": row["storage_mode"],
        "storageRef": row["storage_ref"],
        "kind": row["kind"],
        "mimeType": row["mime_type"],
        "altText": row["alt_text"],
        "checksum": row["checksum"],
        "createdAt": row["created_at"],
    }


def serialize_draft_version(row, media_assets):
    return {
        "id": row["id"],
        "draftId": row["draft_id"],
        "versionNumber": row["version_number"],
        "platform": row["platform"],
        "status": row["status"],
        "caption": row["caption"],
        "body": row["body"],
        "cta": row["cta"],
        "providerPayloadSummary": redact(json_loads(row["provider_payload_summary"], {})),
        "disclosureSettingsRef": json_loads(row["disclosure_settings_ref"], {}),
        "mediaRefs": [serialize_media_asset(media) for media in media_assets],
        "createdAt": row["created_at"],
    }


def serialize_connected_channel(row, token_boundary):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "provider": row["provider"],
        "platform": row["platform"],
        "displayName": row["display_name"],
        "providerChannelId": row["provider_channel_id"],
        "status": row["status"],
        "tokenBoundaryRef": serialize_token_boundary_ref(token_boundary),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def build_approval_snapshot(draft, version, media_assets, channel, token_boundary, approver, approved_at=None):
    approved_at = approved_at or utc_now()
    media_refs = [serialize_media_asset(media) for media in media_assets]
    connected_channel_ref = {
        "id": channel["id"],
        "provider": channel["provider"],
        "platform": channel["platform"],
        "displayName": channel["display_name"],
        "providerChannelId": channel["provider_channel_id"],
    }
    key = idempotency_key(draft["platform"], version["id"], channel["id"])
    return redact(
        {
            "platform": draft["platform"],
            "draftId": draft["id"],
            "draftVersionId": version["id"],
            "versionNumber": version["version_number"],
            "caption": version["caption"],
            "body": version["body"],
            "cta": version["cta"],
            "mediaRefs": media_refs,
            "connectedChannelRef": connected_channel_ref,
            "tokenBoundaryRef": serialize_token_boundary_ref(token_boundary),
            "providerPayloadSummary": json_loads(version["provider_payload_summary"], {}),
            "disclosureSettingsRef": json_loads(version["disclosure_settings_ref"], {}),
            "approver": {
                "name": approver["name"],
                "email": approver["email"],
            },
            "approvedAt": approved_at,
            "createdAt": approved_at,
            "idempotencyKey": key,
        }
    )


def safe_diagnostics(value):
    return redact(value or {})
