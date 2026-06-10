import sqlite3

from backend.app.contracts import (
    build_approval_snapshot,
    json_dumps,
    json_loads,
    new_id,
    request_digest,
    safe_diagnostics,
    redacted_token_boundary_ref,
    serialize_connected_channel,
    serialize_draft_version,
    summarize_approval_snapshot,
    trace_id,
    utc_now,
)
from backend.app.token_boundary import create_token_boundary


DEMO_MERCHANT_ID = "merchant_northstar"
DEMO_USER_ID = "user_karen"
DEMO_CAMPAIGN_ID = "campaign_lunch_special"
FACEBOOK_DRAFT_ID = "draft_facebook_lunch"
TIKTOK_DRAFT_ID = "draft_tiktok_lunch"
FACEBOOK_CHANNEL_ID = "channel-facebook-page"
TIKTOK_CHANNEL_ID = "channel-tiktok-business"


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    return conn


def initialize_database(conn):
    conn.executescript(
        """
        create table if not exists merchants (
          id text primary key,
          name text not null,
          created_at text not null
        );

        create table if not exists users (
          id text primary key,
          merchant_id text not null references merchants(id),
          name text not null,
          email text not null,
          role text not null,
          created_at text not null
        );

        create table if not exists business_profiles (
          id text primary key,
          merchant_id text not null references merchants(id),
          business_name text not null,
          business_type text not null,
          location text not null,
          audience text not null,
          tone text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists provider_token_boundaries (
          id text primary key,
          provider text not null,
          connected_channel_id text not null,
          storage_mode text not null,
          secret_ref text not null,
          rotation_status text not null,
          rotation_due_at text,
          credential_fingerprint text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists connected_channels (
          id text primary key,
          merchant_id text not null references merchants(id),
          provider text not null,
          platform text not null,
          display_name text not null,
          provider_channel_id text not null,
          status text not null,
          token_boundary_id text not null references provider_token_boundaries(id),
          created_at text not null,
          updated_at text not null
        );

        create table if not exists campaigns (
          id text primary key,
          merchant_id text not null references merchants(id),
          created_by_user_id text not null references users(id),
          title text not null,
          offer text not null,
          goal text not null,
          audience text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists platform_drafts (
          id text primary key,
          campaign_id text not null references campaigns(id),
          merchant_id text not null references merchants(id),
          connected_channel_id text not null references connected_channels(id),
          platform text not null,
          status text not null,
          current_version_id text,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists draft_versions (
          id text primary key,
          draft_id text not null references platform_drafts(id),
          version_number integer not null,
          platform text not null,
          status text not null,
          caption text not null,
          body text not null,
          cta text not null,
          provider_payload_summary text not null,
          disclosure_settings_ref text not null,
          created_at text not null,
          unique(draft_id, version_number)
        );

        create table if not exists media_assets (
          id text primary key,
          merchant_id text not null references merchants(id),
          draft_version_id text not null references draft_versions(id),
          storage_mode text not null,
          storage_ref text not null,
          kind text not null,
          mime_type text not null,
          alt_text text not null,
          checksum text not null,
          created_at text not null
        );

        create table if not exists approvals (
          id text primary key,
          draft_id text not null references platform_drafts(id),
          draft_version_id text not null references draft_versions(id),
          connected_channel_id text not null references connected_channels(id),
          approver_name text not null,
          approver_email text not null,
          snapshot_json text not null,
          idempotency_key text not null,
          status text not null,
          created_at text not null,
          unique(draft_version_id, connected_channel_id)
        );

        create table if not exists publish_jobs (
          id text primary key,
          approval_id text references approvals(id),
          platform text,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists publish_attempts (
          id text primary key,
          publish_job_id text references publish_jobs(id),
          attempt_number integer not null,
          status text not null,
          trace_id text not null,
          request_digest text not null,
          diagnostics_json text not null,
          retry_classification text,
          started_at text,
          finished_at text,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists publish_events (
          id text primary key,
          publish_job_id text references publish_jobs(id),
          event_type text not null,
          status text,
          summary text not null,
          actor text not null,
          source_actor text,
          attempt_number integer,
          created_at text not null
        );

        create table if not exists idempotency_keys (
          key text primary key,
          approval_id text references approvals(id),
          created_at text not null
        );

        create table if not exists publish_outcomes (
          id text primary key,
          publish_job_id text not null references publish_jobs(id),
          approval_id text not null references approvals(id),
          attempt_id text not null references publish_attempts(id),
          attempt_number integer not null,
          idempotency_key text not null,
          connected_channel_id text not null,
          draft_version_id text not null,
          platform text not null,
          provider text not null,
          provider_result_ref text not null,
          created_at text not null,
          unique(idempotency_key, connected_channel_id)
        );
        """
    )
    migrate_database(conn)
    conn.commit()


def column_names(conn, table_name):
    return {row["name"] for row in conn.execute(f"pragma table_info({table_name})")}


def migrate_database(conn):
    job_columns = column_names(conn, "publish_jobs")
    if "platform" not in job_columns:
        conn.execute("alter table publish_jobs add column platform text")

    attempt_columns = column_names(conn, "publish_attempts")
    if "retry_classification" not in attempt_columns:
        conn.execute("alter table publish_attempts add column retry_classification text")
    if "started_at" not in attempt_columns:
        conn.execute("alter table publish_attempts add column started_at text")
    if "finished_at" not in attempt_columns:
        conn.execute("alter table publish_attempts add column finished_at text")

    event_columns = column_names(conn, "publish_events")
    if "status" not in event_columns:
        conn.execute("alter table publish_events add column status text")
    if "source_actor" not in event_columns:
        conn.execute("alter table publish_events add column source_actor text")
    if "attempt_number" not in event_columns:
        conn.execute("alter table publish_events add column attempt_number integer")

    conn.execute(
        """
        create table if not exists publish_outcomes (
          id text primary key,
          publish_job_id text not null references publish_jobs(id),
          approval_id text not null references approvals(id),
          attempt_id text not null references publish_attempts(id),
          attempt_number integer not null,
          idempotency_key text not null,
          connected_channel_id text not null,
          draft_version_id text not null,
          platform text not null,
          provider text not null,
          provider_result_ref text not null,
          created_at text not null,
          unique(idempotency_key, connected_channel_id)
        )
        """
    )
    outcome_columns = column_names(conn, "publish_outcomes")
    if "attempt_number" not in outcome_columns:
        conn.execute("alter table publish_outcomes add column attempt_number integer not null default 1")


def row_to_boundary(row):
    return {
        "id": row["id"],
        "provider": row["provider"],
        "connectedChannelId": row["connected_channel_id"],
        "storageMode": row["storage_mode"],
        "secretRef": row["secret_ref"],
        "credentialFingerprint": row["credential_fingerprint"],
        "rotation": {
            "status": row["rotation_status"],
            "nextRotationDueAt": row["rotation_due_at"],
        },
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def insert_boundary(conn, boundary):
    conn.execute(
        """
        insert into provider_token_boundaries (
          id, provider, connected_channel_id, storage_mode, secret_ref,
          rotation_status, rotation_due_at, credential_fingerprint, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            boundary["id"],
            boundary["provider"],
            boundary["connectedChannelId"],
            boundary["storageMode"],
            boundary["secretRef"],
            boundary["rotation"]["status"],
            boundary["rotation"]["nextRotationDueAt"],
            boundary["credentialFingerprint"],
            boundary["createdAt"],
            boundary["updatedAt"],
        ),
    )


def seed_demo_data(conn):
    existing = conn.execute("select count(*) from merchants").fetchone()[0]
    if existing:
        return

    now = utc_now()
    conn.execute("insert into merchants values (?, ?, ?)", (DEMO_MERCHANT_ID, "Northstar Local Growth", now))
    conn.execute(
        "insert into users values (?, ?, ?, ?, ?, ?)",
        (DEMO_USER_ID, DEMO_MERCHANT_ID, "Karen Li", "karen@example.com", "owner", now),
    )
    conn.execute(
        "insert into business_profiles values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "profile_cafe",
            DEMO_MERCHANT_ID,
            "Northstar Cafe",
            "restaurant",
            "Detroit, MI",
            "weekday lunch guests within three miles",
            "warm, local, practical",
            now,
            now,
        ),
    )

    facebook_boundary = create_token_boundary(
        "facebook",
        FACEBOOK_CHANNEL_ID,
        "localpilot/provider/facebook/channel-facebook-page",
    )
    tiktok_boundary = create_token_boundary(
        "tiktok",
        TIKTOK_CHANNEL_ID,
        "localpilot/provider/tiktok/channel-tiktok-business",
    )
    insert_boundary(conn, facebook_boundary)
    insert_boundary(conn, tiktok_boundary)

    conn.execute(
        "insert into connected_channels values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            FACEBOOK_CHANNEL_ID,
            DEMO_MERCHANT_ID,
            "facebook",
            "facebook",
            "Northstar Cafe Page",
            "fb-page-northstar-cafe",
            "connected",
            facebook_boundary["id"],
            now,
            now,
        ),
    )
    conn.execute(
        "insert into connected_channels values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            TIKTOK_CHANNEL_ID,
            DEMO_MERCHANT_ID,
            "tiktok",
            "tiktok",
            "Northstar Cafe TikTok",
            "tt-business-northstar-cafe",
            "connected",
            tiktok_boundary["id"],
            now,
            now,
        ),
    )

    conn.execute(
        "insert into campaigns values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            DEMO_CAMPAIGN_ID,
            DEMO_MERCHANT_ID,
            DEMO_USER_ID,
            "Weekday lunch special",
            "Buy one lunch bowl, get a drink for $1",
            "drive walk-ins and coupon saves",
            "nearby office workers and students",
            "active",
            now,
            now,
        ),
    )

    seed_draft(
        conn,
        draft_id=FACEBOOK_DRAFT_ID,
        channel_id=FACEBOOK_CHANNEL_ID,
        platform="facebook",
        caption="Northstar Cafe is running a weekday lunch special.",
        body="Stop by this week for a fresh lunch bowl and add any house drink for $1. Built for quick breaks near downtown Detroit.",
        cta="Show this post in-store",
        media_asset_id="media_facebook_lunch_bowl",
        storage_ref="localpilot-media/demo/northstar/facebook-lunch-bowl.jpg",
        kind="image",
        mime_type="image/jpeg",
        alt_text="Lunch bowl and iced tea on a cafe table",
        checksum="sha256:facebooklunchbowl",
        provider_summary={
            "surface": "page_feed",
            "postType": "organic_page_post",
            "linkMode": "none",
        },
        disclosure_ref={
            "id": "disclosure_facebook_standard",
            "businessPromotion": True,
            "paidPartnership": False,
        },
        now=now,
    )
    seed_draft(
        conn,
        draft_id=TIKTOK_DRAFT_ID,
        channel_id=TIKTOK_CHANNEL_ID,
        platform="tiktok",
        caption="POV: your weekday lunch break finally got upgraded.",
        body="Fresh bowl, fast service, and a $1 drink add-on at Northstar Cafe this week. Save this before lunch.",
        cta="Save the offer",
        media_asset_id="media_tiktok_lunch_video",
        storage_ref="localpilot-media/demo/northstar/tiktok-lunch-short.mp4",
        kind="video",
        mime_type="video/mp4",
        alt_text="Short vertical video of lunch prep at Northstar Cafe",
        checksum="sha256:tiktoklunchvideo",
        provider_summary={
            "surface": "upload_to_inbox_placeholder",
            "postType": "short_video",
            "durationSeconds": 22,
        },
        disclosure_ref={
            "id": "disclosure_tiktok_organic_business",
            "businessPromotion": True,
            "paidPartnership": False,
            "aiGenerated": False,
        },
        now=now,
    )
    conn.commit()


def seed_draft(
    conn,
    draft_id,
    channel_id,
    platform,
    caption,
    body,
    cta,
    media_asset_id,
    storage_ref,
    kind,
    mime_type,
    alt_text,
    checksum,
    provider_summary,
    disclosure_ref,
    now,
):
    version_id = f"version_{platform}_v1"
    conn.execute(
        "insert into platform_drafts values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (draft_id, DEMO_CAMPAIGN_ID, DEMO_MERCHANT_ID, channel_id, platform, "needs_review", version_id, now, now),
    )
    conn.execute(
        """
        insert into draft_versions (
          id, draft_id, version_number, platform, status, caption, body, cta,
          provider_payload_summary, disclosure_settings_ref, created_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            version_id,
            draft_id,
            1,
            platform,
            "needs_review",
            caption,
            body,
            cta,
            json_dumps(provider_summary),
            json_dumps(disclosure_ref),
            now,
        ),
    )
    conn.execute(
        "insert into media_assets values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            media_asset_id,
            DEMO_MERCHANT_ID,
            version_id,
            "server_media_ref",
            storage_ref,
            kind,
            mime_type,
            alt_text,
            checksum,
            now,
        ),
    )


def ensure_database(db_path):
    conn = connect(db_path)
    try:
        initialize_database(conn)
        seed_demo_data(conn)
    finally:
        conn.close()


def get_workflow(conn):
    merchants = [dict(row) for row in conn.execute("select * from merchants order by id")]
    users = [dict(row) for row in conn.execute("select * from users order by id")]
    profiles = [dict(row) for row in conn.execute("select * from business_profiles order by id")]
    campaigns = [dict(row) for row in conn.execute("select * from campaigns order by created_at")]

    connected_channels = []
    for row in conn.execute("select * from connected_channels order by provider"):
        boundary = conn.execute(
            "select * from provider_token_boundaries where id = ?",
            (row["token_boundary_id"],),
        ).fetchone()
        connected_channels.append(serialize_connected_channel(row, row_to_boundary(boundary)))

    platform_drafts = []
    for draft in conn.execute("select * from platform_drafts order by platform"):
        versions = []
        for version in conn.execute(
            "select * from draft_versions where draft_id = ? order by version_number",
            (draft["id"],),
        ):
            media_assets = get_media_assets_for_version(conn, version["id"])
            versions.append(serialize_draft_version(version, media_assets))
        current_version = next(
            (version for version in versions if version["id"] == draft["current_version_id"]),
            versions[-1] if versions else None,
        )
        platform_drafts.append(
            {
                "id": draft["id"],
                "campaignId": draft["campaign_id"],
                "merchantId": draft["merchant_id"],
                "connectedChannelId": draft["connected_channel_id"],
                "platform": draft["platform"],
                "status": draft["status"],
                "currentVersion": current_version,
                "versions": versions,
                "createdAt": draft["created_at"],
                "updatedAt": draft["updated_at"],
            }
        )

    approvals = []
    for approval in conn.execute("select * from approvals order by created_at"):
        approvals.append(
            {
                "id": approval["id"],
                "draftId": approval["draft_id"],
                "draftVersionId": approval["draft_version_id"],
                "connectedChannelId": approval["connected_channel_id"],
                "status": approval["status"],
                "snapshot": json_loads(approval["snapshot_json"], {}),
                "idempotencyKey": approval["idempotency_key"],
                "createdAt": approval["created_at"],
            }
        )

    return {
        "status": "ok",
        "merchants": merchants,
        "users": users,
        "businessProfiles": profiles,
        "connectedChannels": connected_channels,
        "campaigns": campaigns,
        "platformDrafts": platform_drafts,
        "approvals": approvals,
    }


def get_media_assets_for_version(conn, version_id):
    return list(
        conn.execute(
            "select * from media_assets where draft_version_id = ? order by id",
            (version_id,),
        )
    )


def create_campaign(conn, payload):
    now = utc_now()
    campaign_id = new_id("campaign")
    conn.execute(
        "insert into campaigns values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            campaign_id,
            DEMO_MERCHANT_ID,
            DEMO_USER_ID,
            payload.get("title") or payload.get("offer") or "Untitled campaign",
            payload.get("offer") or "Local offer",
            payload.get("goal") or "drive local action",
            payload.get("audience") or "local customers",
            "active",
            now,
            now,
        ),
    )
    conn.commit()
    return dict(conn.execute("select * from campaigns where id = ?", (campaign_id,)).fetchone())


def update_draft(conn, draft_id, payload):
    draft = get_draft(conn, draft_id)
    current = get_version(conn, draft["current_version_id"])
    latest_number = conn.execute(
        "select max(version_number) from draft_versions where draft_id = ?",
        (draft_id,),
    ).fetchone()[0]
    version_id = new_id("version")
    now = utc_now()
    conn.execute(
        """
        insert into draft_versions (
          id, draft_id, version_number, platform, status, caption, body, cta,
          provider_payload_summary, disclosure_settings_ref, created_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            version_id,
            draft_id,
            latest_number + 1,
            draft["platform"],
            "needs_review",
            payload.get("caption") or current["caption"],
            payload.get("body") or current["body"],
            payload.get("cta") or current["cta"],
            current["provider_payload_summary"],
            current["disclosure_settings_ref"],
            now,
        ),
    )
    for media in get_media_assets_for_version(conn, current["id"]):
        conn.execute(
            "insert into media_assets values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_id("media"),
                media["merchant_id"],
                version_id,
                media["storage_mode"],
                media["storage_ref"],
                media["kind"],
                media["mime_type"],
                media["alt_text"],
                media["checksum"],
                now,
            ),
        )
    conn.execute(
        "update platform_drafts set current_version_id = ?, status = ?, updated_at = ? where id = ?",
        (version_id, "needs_review", now, draft_id),
    )
    conn.commit()
    return get_serialized_draft(conn, draft_id)


def approve_draft(conn, draft_id, payload):
    if payload.get("confirmation") != "APPROVE_EXACT_VERSION":
        raise StoreError(400, "Approval requires explicit exact-version confirmation.")
    approver = payload.get("approver") or {}
    if not approver.get("name") or not approver.get("email"):
        raise StoreError(400, "Approval requires approver name and email.")
    if not payload.get("draftVersionId"):
        raise StoreError(400, "Approval requires a draftVersionId.")

    draft = get_draft(conn, draft_id)
    if payload["draftVersionId"] != draft["current_version_id"]:
        raise StoreError(409, "Approval must target the current exact draft version.")
    version = get_version(conn, payload["draftVersionId"])
    media_assets = get_media_assets_for_version(conn, version["id"])
    if not media_assets:
        raise StoreError(400, "Approval requires at least one server-owned media asset.")

    requested_media = payload.get("mediaRefs")
    if requested_media is not None:
        existing_ids = {media["id"] for media in media_assets}
        if set(requested_media) != existing_ids:
            raise StoreError(400, "Approval mediaRefs must match seeded server media assets.")

    channel = conn.execute(
        "select * from connected_channels where id = ?",
        (draft["connected_channel_id"],),
    ).fetchone()
    if channel is None:
        raise StoreError(400, "Draft has no connected channel.")
    boundary_row = conn.execute(
        "select * from provider_token_boundaries where id = ?",
        (channel["token_boundary_id"],),
    ).fetchone()
    if boundary_row is None:
        raise StoreError(400, "Connected channel has no token boundary.")

    approved_at = utc_now()
    snapshot = build_approval_snapshot(
        draft,
        version,
        media_assets,
        channel,
        row_to_boundary(boundary_row),
        {"name": approver["name"], "email": approver["email"]},
        approved_at=approved_at,
    )
    approval_id = new_id("approval")
    try:
        conn.execute(
            "insert into approvals values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                approval_id,
                draft_id,
                version["id"],
                channel["id"],
                approver["name"],
                approver["email"],
                json_dumps(snapshot),
                snapshot["idempotencyKey"],
                "approved",
                approved_at,
            ),
        )
        conn.execute(
            "insert into idempotency_keys values (?, ?, ?)",
            (snapshot["idempotencyKey"], approval_id, approved_at),
        )
        conn.execute(
            "update platform_drafts set status = ?, updated_at = ? where id = ?",
            ("approved", approved_at, draft_id),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise StoreError(409, "This exact draft version is already approved.") from exc

    return {
        "approval": {
            "id": approval_id,
            "draftId": draft_id,
            "draftVersionId": version["id"],
            "connectedChannelId": channel["id"],
            "status": "approved",
            "snapshot": snapshot,
            "idempotencyKey": snapshot["idempotencyKey"],
            "createdAt": approved_at,
        }
    }


def get_approval(conn, approval_id):
    approval = conn.execute("select * from approvals where id = ?", (approval_id,)).fetchone()
    if approval is None:
        raise StoreError(400, "Approval not found.")
    if approval["status"] != "approved":
        raise StoreError(409, "Approval is not ready to publish.")
    return approval


def get_existing_publish_job_for_approval(conn, approval_id):
    return conn.execute(
        "select * from publish_jobs where approval_id = ? order by created_at desc limit 1",
        (approval_id,),
    ).fetchone()


def create_publish_job(conn, approval):
    existing = get_existing_publish_job_for_approval(conn, approval["id"])
    if existing is not None:
        return existing

    snapshot = json_loads(approval["snapshot_json"], {})
    now = utc_now()
    job_id = new_id("publish_job")
    conn.execute(
        "insert into publish_jobs (id, approval_id, platform, status, created_at, updated_at) values (?, ?, ?, ?, ?, ?)",
        (job_id, approval["id"], snapshot.get("platform"), "queued", now, now),
    )
    return conn.execute("select * from publish_jobs where id = ?", (job_id,)).fetchone()


def update_publish_job_status(conn, job_id, status):
    now = utc_now()
    conn.execute(
        "update publish_jobs set status = ?, updated_at = ? where id = ?",
        (status, now, job_id),
    )


def append_publish_event(conn, job_id, status, summary, source_actor, attempt_number):
    now = utc_now()
    safe_summary = safe_diagnostics({"summary": summary}).get("summary") or "Publish event recorded."
    conn.execute(
        """
        insert into publish_events (
          id, publish_job_id, event_type, status, summary, actor,
          source_actor, attempt_number, created_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("publish_event"),
            job_id,
            status,
            status,
            safe_summary,
            source_actor,
            source_actor,
            attempt_number,
            now,
        ),
    )


def create_publish_attempt(conn, job_id, snapshot, outcome):
    now = utc_now()
    attempt_number = next_attempt_number(conn, job_id)
    attempt_id = new_id("publish_attempt")
    diagnostics = safe_diagnostics(outcome.get("diagnostics", {}))
    conn.execute(
        """
        insert into publish_attempts (
          id, publish_job_id, attempt_number, status, trace_id, request_digest,
          diagnostics_json, retry_classification, started_at, finished_at, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            attempt_id,
            job_id,
            attempt_number,
            outcome["attemptStatus"],
            trace_id(),
            request_digest(snapshot),
            json_dumps(diagnostics),
            outcome["retryClassification"],
            now,
            now,
            now,
            now,
        ),
    )
    return conn.execute("select * from publish_attempts where id = ?", (attempt_id,)).fetchone()


def record_publish_outcome(conn, job_id, attempt_id, snapshot):
    idempotency = snapshot.get("idempotencyKey")
    connected_channel = snapshot.get("connectedChannelRef") or {}
    connected_channel_id = connected_channel.get("id")
    draft_version_id = snapshot.get("draftVersionId")
    platform = snapshot.get("platform")
    if not idempotency or not connected_channel_id or not draft_version_id or not platform:
        raise StoreError(409, "Approved snapshot is missing idempotency fields.")

    existing = conn.execute(
        """
        select * from publish_outcomes
        where idempotency_key = ? and connected_channel_id = ?
        """,
        (idempotency, connected_channel_id),
    ).fetchone()
    if existing is not None:
        if existing["publish_job_id"] == job_id and existing["attempt_id"] == attempt_id:
            return existing
        raise StoreError(409, "A published outcome already exists for this approved draft version and channel.")

    job = get_publish_job(conn, job_id)
    now = utc_now()
    attempt = conn.execute("select * from publish_attempts where id = ?", (attempt_id,)).fetchone()
    if attempt is None:
        raise StoreError(409, "Published outcome has no attempt record.")
    provider_result_ref = f"fake:{platform}:{idempotency[-8:]}"
    conn.execute(
        """
        insert into publish_outcomes (
          id, publish_job_id, approval_id, attempt_id, attempt_number, idempotency_key,
          connected_channel_id, draft_version_id, platform, provider,
          provider_result_ref, created_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("publish_outcome"),
            job_id,
            job["approval_id"],
            attempt_id,
            attempt["attempt_number"],
            idempotency,
            connected_channel_id,
            draft_version_id,
            platform,
            "fake",
            provider_result_ref,
            now,
        ),
    )
    return conn.execute(
        "select * from publish_outcomes where idempotency_key = ? and connected_channel_id = ?",
        (idempotency, connected_channel_id),
    ).fetchone()


def next_attempt_number(conn, job_id):
    current = conn.execute(
        "select max(attempt_number) from publish_attempts where publish_job_id = ?",
        (job_id,),
    ).fetchone()[0]
    return (current or 0) + 1


def get_publish_job(conn, job_id):
    job = conn.execute("select * from publish_jobs where id = ?", (job_id,)).fetchone()
    if job is None:
        raise StoreError(404, "Publish job not found.")
    return job


def serialize_publish_event(row):
    return {
        "id": row["id"],
        "timestamp": row["created_at"],
        "sourceActor": row["source_actor"] or row["actor"],
        "attemptNumber": row["attempt_number"] or 1,
        "status": row["status"] or row["event_type"],
        "summary": row["summary"],
    }


def serialize_publish_attempt(row):
    return {
        "id": row["id"],
        "attemptNumber": row["attempt_number"],
        "status": row["status"],
        "traceId": row["trace_id"],
        "requestDigest": row["request_digest"],
        "diagnostics": safe_diagnostics(json_loads(row["diagnostics_json"], {})),
        "retryClassification": row["retry_classification"] or "none",
        "startedAt": row["started_at"] or row["created_at"],
        "finishedAt": row["finished_at"] or row["updated_at"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_publish_job(conn, job):
    approval = conn.execute("select * from approvals where id = ?", (job["approval_id"],)).fetchone()
    if approval is None:
        raise StoreError(400, "Publish job has no approval snapshot.")
    snapshot = json_loads(approval["snapshot_json"], {})
    events = [
        serialize_publish_event(row)
        for row in conn.execute(
            "select * from publish_events where publish_job_id = ? order by created_at, rowid",
            (job["id"],),
        )
    ]
    attempts = [
        serialize_publish_attempt(row)
        for row in conn.execute(
            "select * from publish_attempts where publish_job_id = ? order by attempt_number",
            (job["id"],),
        )
    ]
    return safe_diagnostics(
        {
            "id": job["id"],
            "approvalId": job["approval_id"],
            "draftVersionId": approval["draft_version_id"],
            "connectedChannelId": approval["connected_channel_id"],
            "platform": job["platform"] or snapshot.get("platform"),
            "status": job["status"],
            "approvalSnapshot": snapshot,
            "attempts": attempts,
            "events": events,
            "createdAt": job["created_at"],
            "updatedAt": job["updated_at"],
        }
    )


def get_serialized_publish_job(conn, job_id):
    return serialize_publish_job(conn, get_publish_job(conn, job_id))


def debug_next_action(diagnostics):
    return diagnostics.get("nextRecommendedAction") or diagnostics.get("nextAction") or "none"


def debug_error_class(diagnostics):
    return diagnostics.get("errorClass") or "none"


def serialize_debug_publish_job(conn, job):
    approval = conn.execute("select * from approvals where id = ?", (job["approval_id"],)).fetchone()
    if approval is None:
        raise StoreError(400, "Publish job has no approval snapshot.")
    draft = conn.execute("select * from platform_drafts where id = ?", (approval["draft_id"],)).fetchone()
    if draft is None:
        raise StoreError(400, "Publish job has no draft.")
    merchant = conn.execute("select * from merchants where id = ?", (draft["merchant_id"],)).fetchone()
    if merchant is None:
        raise StoreError(400, "Publish job has no merchant.")

    snapshot = json_loads(approval["snapshot_json"], {})
    attempts = [
        serialize_publish_attempt(row)
        for row in conn.execute(
            "select * from publish_attempts where publish_job_id = ? order by attempt_number",
            (job["id"],),
        )
    ]
    events = [
        serialize_publish_event(row)
        for row in conn.execute(
            "select * from publish_events where publish_job_id = ? order by created_at, rowid",
            (job["id"],),
        )
    ]
    latest_attempt = attempts[-1] if attempts else {}
    diagnostics = safe_diagnostics(latest_attempt.get("diagnostics") or {})
    return safe_diagnostics(
        {
            "id": job["id"],
            "approvalId": job["approval_id"],
            "merchant": {
                "id": merchant["id"],
                "name": merchant["name"],
            },
            "platform": job["platform"] or snapshot.get("platform"),
            "jobStatus": job["status"],
            "attemptCount": len(attempts),
            "latestTraceId": latest_attempt.get("traceId"),
            "errorClass": debug_error_class(diagnostics),
            "updatedAt": job["updated_at"],
            "nextAction": debug_next_action(diagnostics),
            "approver": {
                "name": approval["approver_name"],
                "email": approval["approver_email"],
            },
            "draftVersion": {
                "id": approval["draft_version_id"],
                "versionNumber": snapshot.get("versionNumber"),
            },
            "mediaRefs": snapshot.get("mediaRefs") or [],
            "tokenBoundaryRef": redacted_token_boundary_ref(snapshot),
            "approvalSnapshotSummary": summarize_approval_snapshot(snapshot),
            "attempts": attempts,
            "events": events,
            "redactedDiagnostics": diagnostics,
            "createdAt": job["created_at"],
        }
    )


def list_debug_publish_jobs(conn):
    return [
        serialize_debug_publish_job(conn, row)
        for row in conn.execute("select * from publish_jobs order by updated_at desc, created_at desc, id")
    ]


def get_serialized_draft(conn, draft_id):
    draft = get_draft(conn, draft_id)
    versions = []
    for version in conn.execute(
        "select * from draft_versions where draft_id = ? order by version_number",
        (draft_id,),
    ):
        versions.append(serialize_draft_version(version, get_media_assets_for_version(conn, version["id"])))
    current_version = next(version for version in versions if version["id"] == draft["current_version_id"])
    return {
        "draft": {
            "id": draft["id"],
            "campaignId": draft["campaign_id"],
            "merchantId": draft["merchant_id"],
            "connectedChannelId": draft["connected_channel_id"],
            "platform": draft["platform"],
            "status": draft["status"],
            "currentVersion": current_version,
            "versions": versions,
            "createdAt": draft["created_at"],
            "updatedAt": draft["updated_at"],
        }
    }


def get_draft(conn, draft_id):
    draft = conn.execute("select * from platform_drafts where id = ?", (draft_id,)).fetchone()
    if draft is None:
        raise StoreError(404, "Draft not found.")
    return draft


def get_version(conn, version_id):
    version = conn.execute("select * from draft_versions where id = ?", (version_id,)).fetchone()
    if version is None:
        raise StoreError(404, "Draft version not found.")
    return version


class StoreError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message
