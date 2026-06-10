from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_token_boundary(provider, connected_channel_id, secret_ref):
    now = utc_now()
    fingerprint = sha256(f"{provider}:{connected_channel_id}:{secret_ref}".encode("utf-8")).hexdigest()
    return {
        "id": f"tb_{uuid4().hex[:16]}",
        "provider": provider,
        "connectedChannelId": connected_channel_id,
        "storageMode": "external_secret_ref",
        "secretRef": secret_ref,
        "credentialFingerprint": f"sha256:{fingerprint[:24]}",
        "rotation": {
            "status": "active",
            "rotatedAt": now,
            "nextRotationDueAt": None,
        },
        "createdAt": now,
        "updatedAt": now,
    }


def serialize_token_boundary_ref(boundary):
    rotation = boundary.get("rotation") or {}
    return {
        "id": boundary["id"],
        "provider": boundary["provider"],
        "connectedChannelId": boundary["connectedChannelId"],
        "storageMode": boundary["storageMode"],
        "visibility": "redacted",
        "rotation": {
            "status": rotation.get("status", "active"),
            "nextRotationDueAt": rotation.get("nextRotationDueAt"),
        },
        "updatedAt": boundary.get("updatedAt"),
    }
