import html
import logging
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlparse

from backend.app import sessions
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


logger = logging.getLogger(__name__)


DEMO_MERCHANT_ID = "merchant_northstar"
DEMO_USER_ID = "user_karen"
DEMO_CAMPAIGN_ID = "campaign_lunch_special"
FACEBOOK_DRAFT_ID = "draft_facebook_lunch"
TIKTOK_DRAFT_ID = "draft_tiktok_lunch"
FACEBOOK_CHANNEL_ID = "channel-facebook-page"
TIKTOK_CHANNEL_ID = "channel-tiktok-business"
INSTAGRAM_CHANNEL_ID = "channel-instagram-assist"
GOOGLE_BUSINESS_CHANNEL_ID = "channel-google-business-assist"
DEMO_SESSION_ID = "session_demo_karen"
OPENAI_IMAGE_MODEL_ID = "genmodel_openai_image_primary"
OPENAI_VIDEO_MODEL_ID = "genmodel_openai_video_primary"
CCDANCE_AVATAR_MODEL_ID = "genmodel_ccdance_avatar_preview"
MINIMAX_IMAGE_MODEL_ID = "genmodel_minimax_carousel_primary"
CAROUSEL_WORKFLOW_TYPE = "carousel"
CAROUSEL_PRESET_ID = "carousel_canonical_v1"
CAROUSEL_ASPECT_RATIO = "3:4"
CAROUSEL_SLIDE_ROLES = ("cover", "problem", "proof", "offer", "cta")
CAROUSEL_EDITOR_MODE = "carousel_slide_edit"
CAROUSEL_LOGO_PLACEMENT = "fixed_top_left"
VIDEO_CAPABILITIES = frozenset({"video", "avatar_video"})

CHANNEL_HEALTH_STATES = (
    "connected",
    "missing_permission",
    "expired_token",
    "review_blocked",
    "reconnect_required",
    "disconnected",
)

_CHANNEL_HEALTH_ALIASES = {
    "active": "connected",
    "ok": "connected",
    "healthy": "connected",
    "enabled": "connected",
    "inactive": "disconnected",
    "disabled": "disconnected",
    "revoked": "reconnect_required",
    "needs_reconnect": "reconnect_required",
    "reconnect": "reconnect_required",
    "expired": "expired_token",
    "token_expired": "expired_token",
    "permission_denied": "missing_permission",
    "missing_scope": "missing_permission",
    "in_review": "review_blocked",
    "pending_review": "review_blocked",
    "app_review": "review_blocked",
}

MANUAL_FALLBACK_RETRYABLE_CLASSES = {"rate_limit", "platform_transient"}


def review_url_for_token(token):
    return f"/review/{quote(token)}"


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

        create table if not exists sessions (
          id text primary key,
          user_id text not null references users(id),
          merchant_id text not null references merchants(id),
          status text not null,
          created_at text not null,
          last_seen_at text not null,
          expires_at text not null,
          user_agent text,
          ip_hash text
        );

        create table if not exists generation_model_catalog (
          id text primary key,
          provider_key text not null,
          model_key text not null,
          capability text not null,
          display_name text not null,
          credit_cost integer not null,
          readiness_status text not null,
          settings_schema_json text not null,
          limits_json text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists generation_jobs (
          id text primary key,
          merchant_id text not null references merchants(id),
          model_catalog_id text not null references generation_model_catalog(id),
          provider_key text not null,
          model_key text not null,
          capability text not null,
          prompt text not null,
          request_json text not null,
          settings_json text not null,
          status text not null,
          reserved_credits integer not null default 0,
          failure_reason text,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists generation_attempts (
          id text primary key,
          generation_job_id text not null references generation_jobs(id),
          attempt_number integer not null,
          status text not null,
          diagnostics_json text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists generation_outputs (
          id text primary key,
          generation_job_id text not null references generation_jobs(id),
          output_kind text not null,
          storage_ref text not null,
          preview_ref text not null,
          metadata_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists credit_accounts (
          id text primary key,
          merchant_id text not null unique references merchants(id),
          plan_name text not null,
          monthly_credits integer not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists credit_ledger (
          id text primary key,
          merchant_id text not null references merchants(id),
          generation_job_id text references generation_jobs(id),
          entry_type text not null,
          amount_delta integer not null,
          balance_after integer not null,
          metadata_json text not null,
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

        create table if not exists merchant_profiles (
          id text primary key,
          merchant_id text not null references merchants(id),
          status text not null default 'draft',
          crawl_url text,
          name text not null default '',
          description text not null default '',
          industry text not null default '',
          logo_url text not null default '',
          primary_color text not null default '',
          secondary_color text not null default '',
          accent_color text not null default '',
          font_family text not null default '',
          language text not null default '',
          timezone text not null default '',
          tonality text not null default '',
          voiceover text not null default '',
          avatar text not null default '',
          target_audience text not null default '',
          raw_extraction_json text not null default '{}',
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

        create table if not exists channel_registry (
          id text primary key,
          display_name text not null,
          status text not null,
          max_caption_length integer,
          supported_media_json text not null,
          required_scopes_json text not null,
          platform_config_json text not null,
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

        create table if not exists brand_kits (
          id text primary key,
          merchant_id text not null references merchants(id),
          logo_ref text,
          website text not null,
          social_handle text not null,
          colors_json text not null,
          voice_json text not null,
          hashtags_json text not null,
          typography_json text not null,
          logos_json text not null,
          integrations_json text not null,
          approved_terms_json text not null,
          avoid_terms_json text not null,
          examples_json text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists content_batches (
          id text primary key,
          merchant_id text not null references merchants(id),
          campaign_id text references campaigns(id),
          source_prompt text not null,
          objective text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists content_sources (
          id text primary key,
          merchant_id text not null references merchants(id),
          source_type text not null,
          label text not null,
          url text not null,
          status text not null,
          extracted_json text not null,
          brief_json text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists ai_assistant_replies (
          id text primary key,
          merchant_id text not null references merchants(id),
          prompt text not null,
          reply_text text not null,
          outline_json text not null,
          source_prompt text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists generated_creatives (
          id text primary key,
          batch_id text not null references content_batches(id),
          merchant_id text not null references merchants(id),
          platform text not null,
          format text not null,
          title text not null,
          caption text not null,
          hashtags_json text not null,
          cta text not null,
          proof_hook text not null,
          schedule_slot text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists creative_idea_variants (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          variant_label text not null,
          hook text not null,
          caption text not null,
          cta text not null,
          score integer not null,
          score_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists creative_language_variants (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          language_code text not null,
          language_label text not null,
          localized_title text not null,
          localized_caption text not null,
          localized_cta text not null,
          localized_hashtags_json text not null,
          localization_notes text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists creative_bulk_variants (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          variant_label text not null,
          hook text not null,
          caption text not null,
          visual_direction text not null,
          format text not null,
          score integer not null,
          metadata_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists creative_ugc_packages (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          package_label text not null,
          avatar_json text not null,
          voiceover_json text not null,
          script_json text not null,
          scenes_json text not null,
          export_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists creator_style_workflows (
          id text primary key,
          merchant_id text not null references merchants(id),
          creative_id text references generated_creatives(id),
          prompt text not null,
          goal text not null,
          ideas_json text not null,
          selected_idea_id text not null,
          style_id text not null,
          actor_json text not null,
          template_json text not null,
          script_json text not null,
          publish_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists creative_media_assets (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          asset_type text not null,
          format text not null,
          aspect_ratio text not null,
          storage_ref text not null,
          prompt text not null,
          status text not null,
          provider text not null,
          metadata_json text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists rendered_media_outputs (
          id text primary key,
          media_asset_id text not null references creative_media_assets(id),
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          output_kind text not null,
          format text not null,
          mime_type text not null,
          storage_ref text not null,
          preview_data_url text not null,
          status text not null,
          metadata_json text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists creative_templates (
          id text primary key,
          merchant_id text not null references merchants(id),
          source_provider text not null,
          title text not null,
          format text not null,
          aspect_ratio text not null,
          category text not null,
          preview_ref text not null,
          layer_schema_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists asset_library_items (
          id text primary key,
          merchant_id text not null references merchants(id),
          kind text not null,
          title text not null,
          provider text not null,
          license text not null,
          tags_json text not null,
          storage_ref text not null,
          fit_notes text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists imported_templates (
          id text primary key,
          template_id text not null references creative_templates(id),
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          source_provider text not null,
          import_ref text not null,
          status text not null,
          metadata_json text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists approval_review_links (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          review_token text not null unique,
          review_url text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists approval_feedback (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          review_link_id text references approval_review_links(id),
          author_name text not null,
          author_role text not null,
          feedback_type text not null,
          body text not null,
          status text not null,
          created_at text not null
        );

        create table if not exists review_notifications (
          id text primary key,
          review_link_id text not null references approval_review_links(id),
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          recipient_name text not null,
          recipient_contact text not null,
          channel text not null,
          subject text not null,
          body text not null,
          status text not null,
          provider_ref text not null,
          sent_at text,
          created_at text not null
        );

        create table if not exists calendar_slots (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          platform text not null,
          slot_label text not null,
          scheduled_for text,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists scheduled_posts (
          id text primary key,
          merchant_id text not null references merchants(id),
          connected_channel_id text not null references connected_channels(id),
          channel text not null references channel_registry(id),
          creative_id text references generated_creatives(id),
          campaign_id text references campaigns(id),
          caption text not null,
          body text not null,
          cta text not null,
          hashtags_json text not null,
          media_refs_json text not null,
          channel_config_json text not null,
          scheduled_for text,
          timezone text not null default 'UTC',
          slot_label text not null,
          status text not null,
          approval_id text references approvals(id),
          publish_job_id text references publish_jobs(id),
          approved_at text,
          published_at text,
          failed_reason text,
          retry_count integer not null default 0,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists publish_dispatch_queue (
          id text primary key,
          scheduled_post_id text not null references scheduled_posts(id),
          dispatch_at text not null,
          status text not null,
          attempt_count integer not null default 0,
          last_attempt_at text,
          error_json text,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists proof_links (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          kind text not null,
          code text not null,
          target_url text not null,
          short_url text not null,
          qr_ref text not null,
          coupon_code text,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists proof_events (
          id text primary key,
          proof_link_id text references proof_links(id),
          creative_id text references generated_creatives(id),
          merchant_id text not null references merchants(id),
          event_type text not null,
          label text not null,
          value integer not null,
          source text not null,
          created_at text not null
        );

        create table if not exists performance_snapshots (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          platform text not null,
          impressions integer not null,
          reach integer not null,
          engagements integer not null,
          clicks integer not null,
          leads integer not null,
          spend_cents integer not null,
          lower_bound_value_cents integer not null,
          confidence text not null,
          metrics_json text not null,
          captured_at text not null,
          created_at text not null
        );

        create table if not exists analytics_insights (
          id text primary key,
          merchant_id text not null references merchants(id),
          title text not null,
          insight text not null,
          recommendation text not null,
          confidence text not null,
          related_creative_id text references generated_creatives(id),
          created_at text not null
        );

        create table if not exists competitor_sources (
          id text primary key,
          merchant_id text not null references merchants(id),
          label text not null,
          url text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        );

        create table if not exists competitor_ideas (
          id text primary key,
          source_id text not null references competitor_sources(id),
          merchant_id text not null references merchants(id),
          theme text not null,
          hook text not null,
          timing text not null,
          hashtags_json text not null,
          confidence text not null,
          created_at text not null
        );

        create table if not exists facebook_page_tokens (
          id text primary key,
          merchant_id text not null references merchants(id),
          connected_channel_id text not null,
          page_id text not null,
          ciphertext blob not null,
          credential_fingerprint text not null,
          token_expires_at text,
          issued_at text,
          status text not null default 'active',
          is_active integer not null default 0,
          created_at text not null,
          updated_at text not null
        );

        create unique index if not exists idx_fb_page_tokens_unique
          on facebook_page_tokens(merchant_id, connected_channel_id, page_id);

        create table if not exists oauth_sessions (
          id text primary key,
          provider text not null,
          session_type text not null,
          payload_json text not null,
          created_at text not null,
          expires_at text not null
        );

        create index if not exists idx_oauth_sessions_lookup
          on oauth_sessions(provider, session_type, id);
        """
    )
    migrate_database(conn)
    conn.commit()


def column_names(conn, table_name):
    return {row["name"] for row in conn.execute(f"pragma table_info({table_name})")}


def migrate_database(conn):
    conn.executescript(
        """
        create table if not exists oauth_sessions (
          id text primary key,
          provider text not null,
          session_type text not null,
          payload_json text not null,
          created_at text not null,
          expires_at text not null
        );

        create index if not exists idx_oauth_sessions_lookup
          on oauth_sessions(provider, session_type, id);
        """
    )

    connected_channel_columns = column_names(conn, "connected_channels")
    if "channel_registry_id" not in connected_channel_columns:
        conn.execute("alter table connected_channels add column channel_registry_id text references channel_registry(id)")
    if "connected_by_user_id" not in connected_channel_columns:
        conn.execute("alter table connected_channels add column connected_by_user_id text references users(id)")
    if "capabilities_json" not in connected_channel_columns:
        conn.execute("alter table connected_channels add column capabilities_json text not null default '{}'")
    if "creator_info_json" not in connected_channel_columns:
        conn.execute("alter table connected_channels add column creator_info_json text")

    brand_columns = column_names(conn, "brand_kits")
    if "website" not in brand_columns:
        conn.execute("alter table brand_kits add column website text not null default ''")
    if "social_handle" not in brand_columns:
        conn.execute("alter table brand_kits add column social_handle text not null default ''")
    if "hashtags_json" not in brand_columns:
        conn.execute("alter table brand_kits add column hashtags_json text not null default '[]'")
    if "typography_json" not in brand_columns:
        conn.execute("alter table brand_kits add column typography_json text not null default '{}'")
    if "logos_json" not in brand_columns:
        conn.execute("alter table brand_kits add column logos_json text not null default '{}'")
    if "integrations_json" not in brand_columns:
        conn.execute("alter table brand_kits add column integrations_json text not null default '[]'")

    merchant_profile_columns = column_names(conn, "merchant_profiles")
    if "voiceover" not in merchant_profile_columns:
        conn.execute("alter table merchant_profiles add column voiceover text not null default ''")
    if "avatar" not in merchant_profile_columns:
        conn.execute("alter table merchant_profiles add column avatar text not null default ''")

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
    conn.execute(
        """
        create table if not exists rendered_media_outputs (
          id text primary key,
          media_asset_id text not null references creative_media_assets(id),
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          output_kind text not null,
          format text not null,
          mime_type text not null,
          storage_ref text not null,
          preview_data_url text not null,
          status text not null,
          metadata_json text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists creative_idea_variants (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          variant_label text not null,
          hook text not null,
          caption text not null,
          cta text not null,
          score integer not null,
          score_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists creative_language_variants (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          language_code text not null,
          language_label text not null,
          localized_title text not null,
          localized_caption text not null,
          localized_cta text not null,
          localized_hashtags_json text not null,
          localization_notes text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists creative_bulk_variants (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          variant_label text not null,
          hook text not null,
          caption text not null,
          visual_direction text not null,
          format text not null,
          score integer not null,
          metadata_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists creative_ugc_packages (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          package_label text not null,
          avatar_json text not null,
          voiceover_json text not null,
          script_json text not null,
          scenes_json text not null,
          export_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists creator_style_workflows (
          id text primary key,
          merchant_id text not null references merchants(id),
          creative_id text references generated_creatives(id),
          prompt text not null,
          goal text not null,
          ideas_json text not null,
          selected_idea_id text not null,
          style_id text not null,
          actor_json text not null,
          template_json text not null,
          script_json text not null,
          publish_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists content_sources (
          id text primary key,
          merchant_id text not null references merchants(id),
          source_type text not null,
          label text not null,
          url text not null,
          status text not null,
          extracted_json text not null,
          brief_json text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists ai_assistant_replies (
          id text primary key,
          merchant_id text not null references merchants(id),
          prompt text not null,
          reply_text text not null,
          outline_json text not null,
          source_prompt text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists creative_templates (
          id text primary key,
          merchant_id text not null references merchants(id),
          source_provider text not null,
          title text not null,
          format text not null,
          aspect_ratio text not null,
          category text not null,
          preview_ref text not null,
          layer_schema_json text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists asset_library_items (
          id text primary key,
          merchant_id text not null references merchants(id),
          kind text not null,
          title text not null,
          provider text not null,
          license text not null,
          tags_json text not null,
          storage_ref text not null,
          fit_notes text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists imported_templates (
          id text primary key,
          template_id text not null references creative_templates(id),
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          source_provider text not null,
          import_ref text not null,
          status text not null,
          metadata_json text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists approval_review_links (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          review_token text not null unique,
          review_url text not null,
          status text not null,
          created_at text not null,
          updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists approval_feedback (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          review_link_id text references approval_review_links(id),
          author_name text not null,
          author_role text not null,
          feedback_type text not null,
          body text not null,
          status text not null,
          created_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists review_notifications (
          id text primary key,
          review_link_id text not null references approval_review_links(id),
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          recipient_name text not null,
          recipient_contact text not null,
          channel text not null,
          subject text not null,
          body text not null,
          status text not null,
          provider_ref text not null,
          sent_at text,
          created_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists performance_snapshots (
          id text primary key,
          creative_id text not null references generated_creatives(id),
          merchant_id text not null references merchants(id),
          platform text not null,
          impressions integer not null,
          reach integer not null,
          engagements integer not null,
          clicks integer not null,
          leads integer not null,
          spend_cents integer not null,
          lower_bound_value_cents integer not null,
          confidence text not null,
          metrics_json text not null,
          captured_at text not null,
          created_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists analytics_insights (
          id text primary key,
          merchant_id text not null references merchants(id),
          title text not null,
          insight text not null,
          recommendation text not null,
          confidence text not null,
          related_creative_id text references generated_creatives(id),
          created_at text not null
        )
        """
    )
    user_columns = column_names(conn, "users")
    if "google_sub" not in user_columns:
        conn.execute("alter table users add column google_sub text")
    if "email_verified" not in user_columns:
        conn.execute("alter table users add column email_verified integer")
    conn.execute(
        "create unique index if not exists idx_users_google_sub on users(google_sub) where google_sub is not null"
    )

    seed_channel_registry(conn)
    migrate_demo_seed_to_aurora(conn)


def get_user_by_google_sub(conn, sub):
    return conn.execute("select * from users where google_sub = ?", (sub,)).fetchone()


def get_user_by_email(conn, email):
    return conn.execute("select * from users where email = ?", (email,)).fetchone()


def create_merchant_and_user(conn, *, name, email, google_sub, email_verified):
    now = utc_now()
    merchant_id = new_id("merchant")
    user_id = new_id("user")
    conn.execute(
        "insert into merchants values (?, ?, ?)",
        (merchant_id, name or email, now),
    )
    conn.execute(
        "insert into users (id, merchant_id, name, email, role, created_at, google_sub, email_verified) values (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, merchant_id, name or email, email, "owner", now, google_sub, 1 if email_verified else 0),
    )
    conn.commit()
    return conn.execute("select * from users where id = ?", (user_id,)).fetchone()


def seed_channel_registry(conn):
    now = utc_now()
    rows = [
        (
            "facebook",
            "Facebook",
            "enabled",
            63206,
            ["image", "video", "link", "carousel"],
            [],
            {"defaultPublishRoute": "page_feed"},
        ),
        (
            "tiktok",
            "TikTok",
            "enabled",
            2200,
            ["video"],
            [],
            {"defaultPublishRoute": "upload_to_inbox"},
        ),
        (
            "xiaohongshu",
            "Xiaohongshu",
            "coming_soon",
            None,
            ["image", "video"],
            [],
            {"defaultPublishRoute": "manual_fallback"},
        ),
        (
            "instagram",
            "Instagram",
            "coming_soon",
            2200,
            ["image", "video", "carousel"],
            [],
            {"defaultPublishRoute": "manual_fallback"},
        ),
        (
            "google_business",
            "Google Business Profile",
            "coming_soon",
            1500,
            ["image", "text"],
            [],
            {"defaultPublishRoute": "manual_fallback"},
        ),
    ]
    for row in rows:
        conn.execute(
            """
            insert or ignore into channel_registry (
              id, display_name, status, max_caption_length, supported_media_json,
              required_scopes_json, platform_config_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row[0],
                row[1],
                row[2],
                row[3],
                json_dumps(row[4]),
                json_dumps(row[5]),
                json_dumps(row[6]),
                now,
                now,
            ),
        )


def seed_generation_model_catalog(conn):
    now = utc_now()
    rows = [
        (
            OPENAI_IMAGE_MODEL_ID,
            "openai",
            "gpt-image-2",
            "image",
            "GPT Image 2",
            40,
            "ready",
            {
                "fields": [
                    "prompt",
                    "brandContext",
                    "aspectRatio",
                    "styleHint",
                ]
            },
            {
                "maxPromptLength": 4000,
                "aspectRatios": ["1:1", "4:5", "16:9"],
            },
        ),
        (
            MINIMAX_IMAGE_MODEL_ID,
            "minimax",
            "image-01",
            "image",
            "MiniMax Carousel Image",
            200,
            "ready",
            {
                "fields": [
                    "prompt",
                    "sourceKind",
                    "sourceText",
                    "sourceUrl",
                    "workflowType",
                    "carouselPresetId",
                    "slideRoles",
                    "aspectRatio",
                ]
            },
            {
                "maxPromptLength": 4000,
                "supportsCarousel": True,
                "aspectRatios": ["3:4"],
                "slideCount": 5,
            },
        ),
        (
            OPENAI_VIDEO_MODEL_ID,
            "openai",
            "sora-2",
            "video",
            "Sora 2",
            180,
            "ready",
            {
                "fields": [
                    "prompt",
                    "brandContext",
                    "aspectRatio",
                    "durationSeconds",
                ]
            },
            {
                "maxPromptLength": 4000,
                "durations": [5, 10, 15],
                "aspectRatios": ["9:16", "16:9"],
            },
        ),
        (
            CCDANCE_AVATAR_MODEL_ID,
            "heygen",
            "heygen-avatar",
            "avatar_video",
            "HeyGen UGC Avatar",
            220,
            "ready",
            {
                "fields": [
                    "prompt",
                    "avatar",
                    "voiceover",
                    "script",
                    "durationSeconds",
                ]
            },
            {
                "maxPromptLength": 4000,
                "durations": [10, 15, 20],
                "avatars": ["female_host", "male_owner", "creator_style"],
            },
        ),
    ]
    for row in rows:
        conn.execute(
            """
            insert or ignore into generation_model_catalog (
              id, provider_key, model_key, capability, display_name, credit_cost,
              readiness_status, settings_schema_json, limits_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                json_dumps(row[7]),
                json_dumps(row[8]),
                now,
                now,
            ),
        )
        conn.execute(
            """
            update generation_model_catalog
            set provider_key = ?, model_key = ?, capability = ?, display_name = ?,
                credit_cost = ?, readiness_status = ?, settings_schema_json = ?,
                limits_json = ?, updated_at = ?
            where id = ?
            """,
            (
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                json_dumps(row[7]),
                json_dumps(row[8]),
                now,
                row[0],
            ),
        )


def ensure_generation_credit_account(conn, merchant_id, plan_name="Growth Demo", monthly_credits=3200):
    now = utc_now()
    conn.execute(
        """
        insert or ignore into credit_accounts (
          id, merchant_id, plan_name, monthly_credits, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("credit_account"),
            merchant_id,
            plan_name,
            monthly_credits,
            now,
            now,
        ),
    )


def ensure_phase13_generation_seed(conn):
    seed_generation_model_catalog(conn)
    ensure_generation_credit_account(conn, DEMO_MERCHANT_ID)


def ensure_phase5_foundation_seed(conn):
    seed_channel_registry(conn)
    conn.execute(
        """
        update connected_channels
        set channel_registry_id = platform
        where channel_registry_id is null
          and exists (select 1 from channel_registry where channel_registry.id = connected_channels.platform)
        """
    )
    conn.execute(
        """
        update connected_channels
        set connected_by_user_id = ?
        where merchant_id = ? and connected_by_user_id is null
        """,
        (DEMO_USER_ID, DEMO_MERCHANT_ID),
    )
    conn.execute(
        """
        update connected_channels
        set capabilities_json = '{}'
        where capabilities_json is null or trim(capabilities_json) = ''
        """
    )
    ensure_demo_session(conn)
    ensure_tiktok_creator_info_seed(conn)
    migrate_calendar_slots_to_scheduled_posts(conn)


def ensure_tiktok_creator_info_seed(conn):
    rows = conn.execute(
        "select id from connected_channels where platform = 'tiktok' and (creator_info_json is null or trim(creator_info_json) = '')"
    ).fetchall()
    for row in rows:
        conn.execute(
            "update connected_channels set creator_info_json = ?, updated_at = ? where id = ?",
            (json_dumps(default_tiktok_creator_info(version=1)), utc_now(), row["id"]),
        )


def ensure_demo_session(conn):
    row = conn.execute("select id from sessions where id = ?", (DEMO_SESSION_ID,)).fetchone()
    if row is not None:
        return
    now = utc_now()
    conn.execute(
        """
        insert into sessions (
          id, user_id, merchant_id, status, created_at, last_seen_at, expires_at, user_agent, ip_hash
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            DEMO_SESSION_ID,
            DEMO_USER_ID,
            DEMO_MERCHANT_ID,
            "authenticated",
            now,
            now,
            "2099-01-01T00:00:00Z",
            "LocalPilot demo seed",
            "sha256:demo-session",
        ),
    )


def scheduled_post_id_for_slot(slot_id):
    return f"scheduled_post_{slot_id}"


def resolve_connected_channel_id_for_slot(conn, merchant_id, platform):
    matches = conn.execute(
        """
        select id from connected_channels
        where merchant_id = ? and platform = ?
        order by created_at, id
        """,
        (merchant_id, platform),
    ).fetchall()
    if matches:
        return matches[0]["id"]
    platform_matches = conn.execute(
        "select id from connected_channels where platform = ? order by created_at, id",
        (platform,),
    ).fetchall()
    if len(platform_matches) == 1:
        return platform_matches[0]["id"]
    return None


def campaign_id_for_creative(conn, creative_id):
    row = conn.execute(
        """
        select content_batches.campaign_id
        from generated_creatives
        join content_batches on content_batches.id = generated_creatives.batch_id
        where generated_creatives.id = ?
        """,
        (creative_id,),
    ).fetchone()
    if row is None:
        return None
    return row["campaign_id"]


def migrate_calendar_slots_to_scheduled_posts(conn):
    for row in conn.execute("select * from calendar_slots order by created_at, id").fetchall():
        scheduled_post_id = scheduled_post_id_for_slot(row["id"])
        existing = conn.execute("select id from scheduled_posts where id = ?", (scheduled_post_id,)).fetchone()
        if existing is not None:
            continue
        connected_channel_id = resolve_connected_channel_id_for_slot(conn, row["merchant_id"], row["platform"])
        if connected_channel_id is None:
            continue
        creative = conn.execute("select * from generated_creatives where id = ?", (row["creative_id"],)).fetchone()
        mapped_status = {
            "scheduled": "queued",
            "in_review": "draft",
            "assisted": "draft",
        }.get(row["status"], "draft")
        conn.execute(
            """
            insert into scheduled_posts (
              id, merchant_id, connected_channel_id, channel, creative_id, campaign_id,
              caption, body, cta, hashtags_json, media_refs_json, channel_config_json,
              scheduled_for, timezone, slot_label, status, approval_id, publish_job_id,
              approved_at, published_at, failed_reason, retry_count, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scheduled_post_id,
                row["merchant_id"],
                connected_channel_id,
                row["platform"],
                row["creative_id"],
                campaign_id_for_creative(conn, row["creative_id"]),
                creative["caption"] if creative is not None else "",
                creative["title"] if creative is not None else "",
                creative["cta"] if creative is not None else "",
                creative["hashtags_json"] if creative is not None else "[]",
                "[]",
                "{}",
                row["scheduled_for"],
                "UTC",
                row["slot_label"],
                mapped_status,
                None,
                None,
                None,
                None,
                None,
                0,
                row["created_at"],
                row["updated_at"],
            ),
        )


def serialize_scheduled_post(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "connectedChannelId": row["connected_channel_id"],
        "channel": row["channel"],
        "creativeId": row["creative_id"],
        "campaignId": row["campaign_id"],
        "caption": row["caption"],
        "body": row["body"],
        "cta": row["cta"],
        "hashtags": json_loads(row["hashtags_json"], []),
        "mediaRefs": json_loads(row["media_refs_json"], []),
        "channelConfig": json_loads(row["channel_config_json"], {}),
        "scheduledFor": row["scheduled_for"],
        "timezone": row["timezone"],
        "slotLabel": row["slot_label"],
        "status": row["status"],
        "approvalId": row["approval_id"],
        "publishJobId": row["publish_job_id"],
        "approvedAt": row["approved_at"],
        "publishedAt": row["published_at"],
        "failedReason": row["failed_reason"],
        "retryCount": row["retry_count"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def advance_scheduled_post_status(conn, scheduled_post_id, next_status):
    row = conn.execute("select * from scheduled_posts where id = ?", (scheduled_post_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Scheduled post not found.")
    if next_status in {"queued", "publishing"}:
        channel = conn.execute("select * from connected_channels where id = ?", (row["connected_channel_id"],)).fetchone()
        if channel is None:
            raise StoreError(400, "Scheduled post has no connected channel.")
        if channel["status"] != "connected":
            raise StoreError(409, "Channel must be connected before the scheduled post can advance.")

    now = utc_now()
    approved_at = row["approved_at"]
    published_at = row["published_at"]
    if next_status == "approved" and not approved_at:
        approved_at = now
    if next_status == "published" and not published_at:
        published_at = now
    conn.execute(
        """
        update scheduled_posts
        set status = ?, approved_at = ?, published_at = ?, updated_at = ?
        where id = ?
        """,
        (next_status, approved_at, published_at, now, scheduled_post_id),
    )
    conn.commit()
    return serialize_scheduled_post(
        conn.execute("select * from scheduled_posts where id = ?", (scheduled_post_id,)).fetchone()
    )


def normalize_channel_health(value):
    normalized = str(value or "").strip().lower()
    if normalized in CHANNEL_HEALTH_STATES:
        return normalized
    return _CHANNEL_HEALTH_ALIASES.get(normalized, "disconnected")


def _registry_status_for_channel(conn, channel_row):
    registry_id = channel_row["channel_registry_id"] or channel_row["platform"]
    registry = conn.execute(
        "select status from channel_registry where id = ?", (registry_id,)
    ).fetchone()
    return registry["status"] if registry else "disabled"


def _refine_facebook_health(conn, channel_row, health):
    if channel_row["platform"] != "facebook" or health != "connected":
        return health
    try:
        from backend.app import facebook_oauth

        page_health = facebook_oauth.active_page_health(conn=conn, merchant_id=channel_row["merchant_id"])
    except Exception:
        return health
    refined = normalize_channel_health(page_health.get("health"))
    if refined != "connected" and not page_health.get("canPublish", False):
        return refined
    return health


def serialize_channel_health(conn, channel_row):
    health = normalize_channel_health(channel_row["status"])
    health = _refine_facebook_health(conn, channel_row, health)
    registry_status = _registry_status_for_channel(conn, channel_row)
    can_publish = health == "connected" and registry_status == "enabled"
    return safe_diagnostics(
        {
            "connectedChannelId": channel_row["id"],
            "platform": channel_row["platform"],
            "provider": channel_row["provider"],
            "displayName": channel_row["display_name"],
            "providerChannelId": channel_row["provider_channel_id"],
            "registryStatus": registry_status,
            "health": health,
            "canPublish": can_publish,
            "contentCreationAvailable": True,
            "updatedAt": channel_row["updated_at"],
        }
    )


def get_channel_health(conn, merchant_id, platform=None):
    params = [merchant_id]
    sql = "select * from connected_channels where merchant_id = ?"
    if platform:
        sql += " and platform = ?"
        params.append(platform)
    sql += " order by created_at, id"
    rows = conn.execute(sql, tuple(params)).fetchall()
    return {
        "status": "ok",
        "channels": [serialize_channel_health(conn, row) for row in rows],
    }


def get_connected_channel_for_merchant(conn, merchant_id, channel_id):
    row = conn.execute(
        "select * from connected_channels where id = ? and merchant_id = ?",
        (channel_id, merchant_id),
    ).fetchone()
    if row is None:
        raise StoreError(404, "Connected channel not found for this merchant.")
    return row


def set_channel_health(conn, merchant_id, channel_id, health):
    normalized = normalize_channel_health(health)
    channel = get_connected_channel_for_merchant(conn, merchant_id, channel_id)
    conn.execute(
        "update connected_channels set status = ?, updated_at = ? where id = ?",
        (normalized, utc_now(), channel["id"]),
    )
    conn.commit()
    return serialize_channel_health(
        conn, conn.execute("select * from connected_channels where id = ?", (channel["id"],)).fetchone()
    )


def disconnect_channel(conn, merchant_id, channel_id):
    # Preserve historical drafts, approvals, and publish jobs; only flip the live
    # connection status so new schedule/publish progression is blocked immediately.
    return set_channel_health(conn, merchant_id, channel_id, "disconnected")


def assert_channel_publishable(conn, connected_channel_id):
    channel = conn.execute(
        "select * from connected_channels where id = ?", (connected_channel_id,)
    ).fetchone()
    if channel is None:
        raise StoreError(404, "Connected channel not found.")
    # Gate on the stored connection status only. Provider-specific health (e.g.
    # Facebook Page capability when publishing with a fresh user token) is enforced
    # by each publisher; this gate is the disconnect / reconnect-required backstop.
    health = normalize_channel_health(channel["status"])
    if health != "connected":
        raise StoreError(
            409,
            "This channel can't publish yet \u2014 reconnect or fix its connection health first.",
        )
    return channel


TIKTOK_PRIVACY_LEVELS = (
    "PUBLIC_TO_EVERYONE",
    "MUTUAL_FOLLOW_FRIENDS",
    "FOLLOWER_OF_CREATOR",
    "SELF_ONLY",
)


def default_tiktok_creator_info(version=1):
    return {
        "version": version,
        "fetchedAt": utc_now(),
        "creatorNickname": "Aurora Heating & Cooling",
        "privacyLevelOptions": [
            "PUBLIC_TO_EVERYONE",
            "MUTUAL_FOLLOW_FRIENDS",
            "SELF_ONLY",
        ],
        "commentDisabled": False,
        "duetDisabled": False,
        "stitchDisabled": False,
        "maxVideoPostDurationSec": 600,
        "disclosureRequiredForCommercial": True,
    }


def get_tiktok_creator_info(conn, connected_channel_id, *, ensure=True):
    channel = conn.execute(
        "select * from connected_channels where id = ?", (connected_channel_id,)
    ).fetchone()
    if channel is None:
        raise StoreError(404, "Connected channel not found.")
    if channel["platform"] != "tiktok":
        raise StoreError(409, "Creator info is only available for TikTok channels.")
    stored = json_loads(channel["creator_info_json"], None)
    if stored is None and ensure:
        stored = default_tiktok_creator_info(version=1)
        conn.execute(
            "update connected_channels set creator_info_json = ?, updated_at = ? where id = ?",
            (json_dumps(stored), utc_now(), connected_channel_id),
        )
        conn.commit()
    return stored


def refresh_tiktok_creator_info(conn, connected_channel_id):
    current = get_tiktok_creator_info(conn, connected_channel_id, ensure=True) or {}
    next_version = int(current.get("version") or 0) + 1
    refreshed = default_tiktok_creator_info(version=next_version)
    conn.execute(
        "update connected_channels set creator_info_json = ?, updated_at = ? where id = ?",
        (json_dumps(refreshed), utc_now(), connected_channel_id),
    )
    conn.commit()
    return refreshed


def validate_tiktok_confirmations(creator_info, confirmations):
    creator_info = creator_info or {}
    if not isinstance(confirmations, dict) or not confirmations:
        raise StoreError(400, "TikTok approval requires disclosure, privacy, and interaction confirmations.")

    if confirmations.get("creatorInfoVersion") != creator_info.get("version"):
        raise StoreError(409, "TikTok creator settings changed \u2014 refresh creator info and re-confirm before approving.")

    privacy_level = confirmations.get("privacyLevel")
    if privacy_level not in (creator_info.get("privacyLevelOptions") or []):
        raise StoreError(400, "TikTok approval requires a privacyLevel allowed by the creator's settings.")

    if not confirmations.get("disclosureReviewed"):
        raise StoreError(400, "TikTok approval requires explicit disclosure confirmation.")
    if not confirmations.get("interactionReviewed"):
        raise StoreError(400, "TikTok approval requires interaction-settings confirmation.")

    if creator_info.get("commentDisabled") and confirmations.get("allowComment"):
        raise StoreError(400, "Comments are disabled for this TikTok creator; they cannot be enabled.")
    if creator_info.get("duetDisabled") and confirmations.get("allowDuet"):
        raise StoreError(400, "Duets are disabled for this TikTok creator; they cannot be enabled.")
    if creator_info.get("stitchDisabled") and confirmations.get("allowStitch"):
        raise StoreError(400, "Stitches are disabled for this TikTok creator; they cannot be enabled.")

    if confirmations.get("commercialContent") and creator_info.get("disclosureRequiredForCommercial"):
        if not (confirmations.get("yourBrand") or confirmations.get("brandedContent")):
            raise StoreError(400, "Commercial TikTok content requires a disclosure (your brand or branded content).")

    return {
        "creatorInfoVersion": creator_info.get("version"),
        "privacyLevel": privacy_level,
        "disclosureReviewed": True,
        "interactionReviewed": True,
        "allowComment": bool(confirmations.get("allowComment")),
        "allowDuet": bool(confirmations.get("allowDuet")),
        "allowStitch": bool(confirmations.get("allowStitch")),
        "commercialContent": bool(confirmations.get("commercialContent")),
        "yourBrand": bool(confirmations.get("yourBrand")),
        "brandedContent": bool(confirmations.get("brandedContent")),
        "confirmedAt": utc_now(),
    }


def strictest_channel_media_policy(conn, platforms=None):
    """Media generation policy that targets the strictest relevant channel first.

    Default to a single asset that satisfies the strictest enabled-channel
    constraints; extra variants are opt-in, not a default fallback (D-13).
    """
    rows = conn.execute(
        "select id, status, max_caption_length, supported_media_json from channel_registry"
    ).fetchall()
    enabled = [row for row in rows if row["status"] == "enabled"]
    if platforms:
        wanted = set(platforms)
        enabled = [row for row in enabled if row["id"] in wanted]

    caption_limits = [
        (row["id"], row["max_caption_length"])
        for row in enabled
        if row["max_caption_length"] is not None
    ]
    strictest_caption = min((limit for _, limit in caption_limits), default=None)
    strictest_channel = min(caption_limits, key=lambda item: item[1])[0] if caption_limits else None

    media_sets = [set(json_loads(row["supported_media_json"], [])) for row in enabled]
    supported_media = sorted(set.intersection(*media_sets)) if media_sets else []

    return {
        "strictestChannel": strictest_channel,
        "maxCaptionLength": strictest_caption,
        "supportedMedia": supported_media,
        "generateVariants": False,
        "variantPolicy": "strictest_relevant_channel_first",
        "rationale": (
            "Generate one asset that satisfies the strictest relevant channel constraints first; "
            "only create extra variants when a concrete compliance or performance reason requires it."
        ),
    }


def migrate_demo_seed_to_aurora(conn):
    now = utc_now()
    conn.execute(
        "update merchants set name = ? where id = ?",
        ("Aurora Heating & Cooling", DEMO_MERCHANT_ID),
    )
    conn.execute(
        """
        update business_profiles
        set business_name = ?, business_type = ?, location = ?, audience = ?, tone = ?, updated_at = ?
        where merchant_id = ?
        """,
        (
            "Aurora Heating & Cooling",
            "home_services",
            "Washtenaw County, MI",
            "homeowners and property managers who need HVAC service",
            "trusted, prompt, local",
            now,
            DEMO_MERCHANT_ID,
        ),
    )
    conn.execute(
        """
        update connected_channels
        set display_name = ?, provider_channel_id = ?, updated_at = ?
        where id = ?
        """,
        ("Aurora Heating & Cooling Facebook Page", "1243605852158721", now, FACEBOOK_CHANNEL_ID),
    )
    conn.execute(
        """
        update connected_channels
        set display_name = ?, provider_channel_id = ?, updated_at = ?
        where id = ?
        """,
        ("Aurora Heating & Cooling TikTok", "tt-business-aurora-hvac", now, TIKTOK_CHANNEL_ID),
    )
    conn.execute(
        """
        update campaigns
        set title = ?, offer = ?, goal = ?, audience = ?, updated_at = ?
        where id = ?
        """,
        (
            "Spring AC tune-up openings",
            "Same-week AC tune-up appointments are available for Washtenaw County homeowners",
            "drive calls and appointment bookings",
            "local homeowners preparing for warm weather",
            now,
            DEMO_CAMPAIGN_ID,
        ),
    )
    conn.execute(
        """
        update draft_versions
        set caption = ?, body = ?, cta = ?
        where draft_id = ? and version_number = 1
        """,
        (
            "Aurora Heating & Cooling has same-week AC tune-up openings.",
            "Washtenaw County homeowners can book a seasonal AC check before the next hot stretch. Our local team handles tune-ups, emergency service, and honest repair recommendations.",
            "Call Aurora to schedule service",
            FACEBOOK_DRAFT_ID,
        ),
    )
    conn.execute(
        """
        update draft_versions
        set caption = ?, body = ?, cta = ?
        where draft_id = ? and version_number = 1
        """,
        (
            "POV: your AC gets checked before the heat wave.",
            "Aurora Heating & Cooling is booking same-week tune-ups for local homeowners. Save this before the next hot stretch.",
            "Call to schedule",
            TIKTOK_DRAFT_ID,
        ),
    )
    conn.execute(
        """
        update media_assets
        set storage_ref = ?, alt_text = ?, checksum = ?
        where id = ?
        """,
        (
            "localpilot-media/demo/aurora/facebook-ac-tune-up.jpg",
            "HVAC technician checking an outdoor AC unit",
            "sha256:facebookauroraac",
            "media_facebook_lunch_bowl",
        ),
    )
    conn.execute(
        """
        update media_assets
        set storage_ref = ?, alt_text = ?, checksum = ?
        where id = ?
        """,
        (
            "localpilot-media/demo/aurora/tiktok-ac-tune-up.mp4",
            "Short vertical video of HVAC tune-up work",
            "sha256:tiktokauroraac",
            "media_tiktok_lunch_video",
        ),
    )


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
        ensure_phase8_onboarding_seed(conn)
        ensure_phase5_foundation_seed(conn)
        ensure_phase13_generation_seed(conn)
        conn.commit()
        return

    now = utc_now()
    conn.execute("insert into merchants values (?, ?, ?)", (DEMO_MERCHANT_ID, "Aurora Heating & Cooling", now))
    conn.execute(
        "insert into users (id, merchant_id, name, email, role, created_at) values (?, ?, ?, ?, ?, ?)",
        (DEMO_USER_ID, DEMO_MERCHANT_ID, "Karen Li", "karen@example.com", "owner", now),
    )
    conn.execute(
        "insert into business_profiles values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "profile_cafe",
            DEMO_MERCHANT_ID,
            "Aurora Heating & Cooling",
            "home_services",
            "Washtenaw County, MI",
            "homeowners and property managers who need HVAC service",
            "trusted, prompt, local",
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
    instagram_boundary = create_token_boundary(
        "instagram",
        INSTAGRAM_CHANNEL_ID,
        "localpilot/provider/instagram/channel-instagram-assist",
    )
    google_business_boundary = create_token_boundary(
        "google_business",
        GOOGLE_BUSINESS_CHANNEL_ID,
        "localpilot/provider/google_business/channel-google-business-assist",
    )
    insert_boundary(conn, instagram_boundary)
    insert_boundary(conn, google_business_boundary)

    conn.execute(
        """
        insert into connected_channels (
          id, merchant_id, provider, platform, display_name, provider_channel_id,
          status, token_boundary_id, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            FACEBOOK_CHANNEL_ID,
            DEMO_MERCHANT_ID,
            "facebook",
            "facebook",
            "Aurora Heating & Cooling Facebook Page",
            "1243605852158721",
            "connected",
            facebook_boundary["id"],
            now,
            now,
        ),
    )
    conn.execute(
        """
        insert into connected_channels (
          id, merchant_id, provider, platform, display_name, provider_channel_id,
          status, token_boundary_id, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            INSTAGRAM_CHANNEL_ID,
            DEMO_MERCHANT_ID,
            "instagram",
            "instagram",
            "Aurora Heating & Cooling Instagram",
            "ig-aurora-assist",
            "disconnected",
            instagram_boundary["id"],
            now,
            now,
        ),
    )
    conn.execute(
        """
        insert into connected_channels (
          id, merchant_id, provider, platform, display_name, provider_channel_id,
          status, token_boundary_id, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            GOOGLE_BUSINESS_CHANNEL_ID,
            DEMO_MERCHANT_ID,
            "google_business",
            "google_business",
            "Aurora Heating & Cooling Google Business Profile",
            "gbp-aurora-assist",
            "disconnected",
            google_business_boundary["id"],
            now,
            now,
        ),
    )
    conn.execute(
        """
        insert into connected_channels (
          id, merchant_id, provider, platform, display_name, provider_channel_id,
          status, token_boundary_id, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            TIKTOK_CHANNEL_ID,
            DEMO_MERCHANT_ID,
            "tiktok",
            "tiktok",
            "Aurora Heating & Cooling TikTok",
            "tt-business-aurora-hvac",
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
            "Spring AC tune-up openings",
            "Same-week AC tune-up appointments are available for Washtenaw County homeowners",
            "drive calls and appointment bookings",
            "local homeowners preparing for warm weather",
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
        caption="Aurora Heating & Cooling has same-week AC tune-up openings.",
        body="Washtenaw County homeowners can book a seasonal AC check before the next hot stretch. Our local team handles tune-ups, emergency service, and honest repair recommendations.",
        cta="Call Aurora to schedule service",
        media_asset_id="media_facebook_lunch_bowl",
        storage_ref="localpilot-media/demo/aurora/facebook-ac-tune-up.jpg",
        kind="image",
        mime_type="image/jpeg",
        alt_text="HVAC technician checking an outdoor AC unit",
        checksum="sha256:facebookauroraac",
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
        caption="POV: your AC gets checked before the heat wave.",
        body="Aurora Heating & Cooling is booking same-week tune-ups for local homeowners. Save this before the next hot stretch.",
        cta="Call to schedule",
        media_asset_id="media_tiktok_lunch_video",
        storage_ref="localpilot-media/demo/aurora/tiktok-ac-tune-up.mp4",
        kind="video",
        mime_type="video/mp4",
        alt_text="Short vertical video of HVAC tune-up work",
        checksum="sha256:tiktokauroraac",
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
    ensure_phase8_onboarding_seed(conn)
    ensure_phase5_foundation_seed(conn)
    ensure_phase13_generation_seed(conn)
    conn.commit()


def seed_phase3_data(conn):
    existing = conn.execute("select count(*) from brand_kits where merchant_id = ?", (DEMO_MERCHANT_ID,)).fetchone()[0]
    if existing:
        ensure_phase3_media_assets(conn)
        seed_phase3_template_library(conn)
        seed_phase3_analytics(conn)
        seed_phase3_approval_feedback(conn)
        seed_phase3_review_notifications(conn)
        seed_phase3_content_sources(conn)
        seed_phase3_creator_workflows(conn)
        ensure_phase5_foundation_seed(conn)
        conn.commit()
        return

    now = utc_now()
    brand_id = "brandkit_aurora"
    conn.execute(
        """
        insert into brand_kits (
          id, merchant_id, logo_ref, website, social_handle, colors_json, voice_json,
          hashtags_json, typography_json, logos_json, integrations_json, approved_terms_json,
          avoid_terms_json, examples_json, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            brand_id,
            DEMO_MERCHANT_ID,
            "localpilot-brand/aurora/logo.svg",
            "https://auroraheatcool.example",
            "@auroraheatcool",
            json_dumps(["#172033", "#2563eb", "#f4a62a", "#fff7e8"]),
            json_dumps(
                {
                    "tone": "trusted, prompt, local",
                    "audience": "Washtenaw County homeowners and property managers",
                    "language": "clear English with helpful service guidance",
                    "promise": "local team, honest recommendations, fast scheduling",
                }
            ),
            json_dumps(["#AnnArbor", "#HVAC", "#LocalService"]),
            json_dumps(
                {
                    "title": "Fraunces-style bold service headline",
                    "subtitle": "Readable sans caption for local offers",
                    "body": "Plain-English service guidance",
                }
            ),
            json_dumps(
                {
                    "light": "localpilot-brand/aurora/logo.svg",
                    "dark": "localpilot-brand/aurora/logo-dark.svg",
                }
            ),
            json_dumps(
                [
                    {"name": "Website URL", "status": "available_demo"},
                    {"name": "CSV upload", "status": "available_demo"},
                    {"name": "Odoo", "status": "planned_localpilot_priority"},
                ]
            ),
            json_dumps(["same-week", "local team", "honest recommendations", "seasonal tune-up"]),
            json_dumps(["guaranteed savings", "miracle fix", "scare tactics", "unverified energy claims"]),
            json_dumps(
                [
                    "Same-week AC tune-up openings before the next warm stretch.",
                    "Our local team explains repairs clearly before work starts.",
                    "Call Aurora to schedule service in Washtenaw County.",
                ]
            ),
            now,
            now,
        ),
    )
    batch_result = create_content_batch(
        conn,
        {
            "sourcePrompt": "Same-week AC tune-up appointments before the next hot stretch",
            "objective": "book calls and service appointments",
        },
        commit=False,
    )

    source_id = "competitor_source_hvac_local"
    conn.execute(
        "insert into competitor_sources values (?, ?, ?, ?, ?, ?, ?)",
        (
            source_id,
            DEMO_MERCHANT_ID,
            "Nearby HVAC Facebook Pages",
            "https://facebook.com/search/pages?q=ann%20arbor%20hvac",
            "demo",
            now,
            now,
        ),
    )
    for theme, hook, timing, hashtags in [
        (
            "Heat-wave readiness",
            "Before the first 85 degree day, check this one thing.",
            "Monday 7:30 AM",
            ["#annarborhomes", "#hvactips", "#michiganweather"],
        ),
        (
            "Service trust",
            "What an honest AC tune-up should include.",
            "Wednesday 6:00 PM",
            ["#localservice", "#homeownerhelp", "#aurorahvac"],
        ),
        (
            "Emergency prevention",
            "The small filter mistake that creates big summer calls.",
            "Friday 10:00 AM",
            ["#actuneup", "#homecare", "#washtenawcounty"],
        ),
    ]:
        conn.execute(
            "insert into competitor_ideas values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_id("idea"),
                source_id,
                DEMO_MERCHANT_ID,
                theme,
                hook,
                timing,
                json_dumps(hashtags),
                "demo_pattern",
                now,
            ),
        )

    record_proof_event(
        conn,
        {
            "eventType": "call_tap",
            "label": "Seeded call taps",
            "value": 12,
            "source": "seed_demo",
            "creativeId": batch_result["creatives"][0]["id"] if batch_result["creatives"] else None,
        },
        commit=False,
    )
    seed_phase3_template_library(conn, commit=False)
    seed_phase3_analytics(conn, commit=False)
    seed_phase3_approval_feedback(conn, commit=False)
    seed_phase3_review_notifications(conn, commit=False)
    seed_phase3_content_sources(conn, commit=False)
    seed_phase3_creator_workflows(conn, commit=False)
    ensure_phase5_foundation_seed(conn)
    conn.commit()


def seed_phase3_approval_feedback(conn, commit=True):
    existing = conn.execute(
        "select count(*) from approval_review_links where merchant_id = ?",
        (DEMO_MERCHANT_ID,),
    ).fetchone()[0]
    if existing:
        for row in conn.execute("select id, review_token from approval_review_links where merchant_id = ?", (DEMO_MERCHANT_ID,)):
            conn.execute(
                "update approval_review_links set review_url = ?, updated_at = ? where id = ?",
                (review_url_for_token(row["review_token"]), utc_now(), row["id"]),
            )
        if commit:
            conn.commit()
        return
    rows = conn.execute(
        "select * from generated_creatives where merchant_id = ? order by platform",
        (DEMO_MERCHANT_ID,),
    ).fetchall()
    if not rows:
        return
    now = utc_now()
    first_link_id = None
    for row in rows:
        token = f"aurora-{row['platform'].replace('_', '-')}-{row['id'][-6:]}"
        link_id = new_id("approval_link")
        if first_link_id is None:
            first_link_id = link_id
        conn.execute(
            "insert into approval_review_links values (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                link_id,
                row["id"],
                DEMO_MERCHANT_ID,
                token,
                review_url_for_token(token),
                "active",
                now,
                now,
            ),
        )
    first_creative = rows[0]
    for author_name, author_role, feedback_type, body, status in [
        (
            "Karen Li",
            "owner",
            "approval_note",
            "The offer is accurate. Please keep the same-week language and make the phone CTA prominent.",
            "noted",
        ),
        (
            "LocalPilot reviewer",
            "internal",
            "change_request",
            "Before publishing, avoid guaranteed savings language and keep the copy focused on tune-up availability.",
            "open",
        ),
    ]:
        conn.execute(
            "insert into approval_feedback values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_id("approval_feedback"),
                first_creative["id"],
                DEMO_MERCHANT_ID,
                first_link_id,
                author_name,
                author_role,
                feedback_type,
                body,
                status,
                now,
            ),
        )
    if commit:
        conn.commit()


def seed_phase3_review_notifications(conn, commit=True):
    existing = conn.execute(
        "select count(*) from review_notifications where merchant_id = ?",
        (DEMO_MERCHANT_ID,),
    ).fetchone()[0]
    if existing:
        return
    link = conn.execute(
        """
        select approval_review_links.*, generated_creatives.title
        from approval_review_links
        join generated_creatives on generated_creatives.id = approval_review_links.creative_id
        where approval_review_links.merchant_id = ?
        order by approval_review_links.created_at, approval_review_links.id
        limit 1
        """,
        (DEMO_MERCHANT_ID,),
    ).fetchone()
    if link is None:
        return
    now = utc_now()
    conn.execute(
        "insert into review_notifications values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            new_id("review_notification"),
            link["id"],
            link["creative_id"],
            DEMO_MERCHANT_ID,
            "Karen Li",
            "karen@example.com",
            "email",
            f"Review requested: {link['title']}",
            f"Please review this LocalPilot post: {link['review_url']}",
            "sent_demo",
            "localpilot-outbox/demo-seed",
            now,
            now,
        ),
    )
    if commit:
        conn.commit()


def content_source_brief(label, url, source_type="url"):
    normalized_label = label or "Local business source"
    if source_type == "image":
        return {
            "summary": f"{normalized_label} gives LocalPilot a product/service image to turn into local social posts.",
            "offer": "same-week AC tune-up appointments",
            "audience": "Washtenaw County homeowners preparing for warm weather",
            "proofPoint": "real service photo, local team context, and call-to-book CTA",
            "angles": [
                "turn the image into a before-the-heat-wave reminder",
                "make a technician/owner explainer from the visual",
                "create a Facebook Page post that feels organic and local",
            ],
            "sourceUrl": url,
            "inputType": "image",
        }
    return {
        "summary": f"{normalized_label} gives LocalPilot an offer/source page to turn into local social posts.",
        "offer": "same-week AC tune-up appointments",
        "audience": "Washtenaw County homeowners preparing for warm weather",
        "proofPoint": "local team, seasonal checklist, and call-to-book CTA",
        "angles": [
            "turn the source page into a homeowner checklist",
            "extract an owner-explainer video hook",
            "make a Google Business update focused on calls and directions",
        ],
        "sourceUrl": url,
    }


def seed_phase3_content_sources(conn, commit=True):
    existing = conn.execute(
        "select count(*) from content_sources where merchant_id = ?",
        (DEMO_MERCHANT_ID,),
    ).fetchone()[0]
    if existing:
        return
    now = utc_now()
    label = "Aurora AC tune-up offer page"
    url = "https://auroraheatcool.example/ac-tune-up"
    extracted = {
        "title": label,
        "detectedBusiness": "Aurora Heating & Cooling",
        "detectedOffer": "same-week AC tune-up appointments",
        "sourceKind": "local_service_page",
    }
    conn.execute(
        "insert into content_sources values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "content_source_aurora_ac_offer",
            DEMO_MERCHANT_ID,
            "url",
            label,
            url,
            "analyzed_demo",
            json_dumps(extracted),
            json_dumps(content_source_brief(label, url)),
            now,
            now,
        ),
    )
    if commit:
        conn.commit()


def creator_style_options():
    return {
        "styles": [
            {
                "id": "storytelling",
                "label": "Storytelling",
                "summary": "Problem, local context, simple fix, proof point, and a direct CTA.",
                "scriptTone": "narrative local expert with a practical setup and payoff",
            },
            {
                "id": "promotional",
                "label": "Promotional",
                "summary": "Offer-first delivery with deadline, CTA, and proof-safe language.",
                "scriptTone": "clear sales CTA with grounded local proof",
            },
            {
                "id": "motivational",
                "label": "Motivational",
                "summary": "Direct-to-camera encouragement with a clear reason to act now.",
                "scriptTone": "warm local expert, energetic but not exaggerated",
            },
            {
                "id": "exploratory",
                "label": "Exploratory",
                "summary": "Educational comparison that explains options without hard claims.",
                "scriptTone": "curious guide, calm explanation, practical recommendation",
            },
        ],
        "actors": [
            {
                "id": "local-owner",
                "name": "Local owner",
                "type": "ai_actor",
                "persona": "approachable small-business owner",
                "look": "branded polo, direct-to-camera, friendly service desk setting",
                "badge": "Owner voice",
            },
            {
                "id": "field-expert",
                "name": "Field expert",
                "type": "ai_actor",
                "persona": "hands-on technician or service specialist",
                "look": "work shirt, job-site background, confident explainer posture",
                "badge": "Expert",
            },
            {
                "id": "community-guide",
                "name": "Community guide",
                "type": "ai_actor",
                "persona": "local neighbor recommending a practical next step",
                "look": "casual local setting, softer delivery, trust-first expression",
                "badge": "Community",
            },
            {
                "id": "studio-host",
                "name": "Studio host",
                "type": "ai_actor",
                "persona": "polished host for premium product/service offers",
                "look": "clean studio lighting, neutral jacket, confident camera framing",
                "badge": "Studio",
            },
            {
                "id": "service-coach",
                "name": "Service coach",
                "type": "ai_actor",
                "persona": "calm explainer who helps customers choose the next step",
                "look": "desk or showroom background, approachable coaching posture",
                "badge": "Coach",
            },
            {
                "id": "neighborhood-pro",
                "name": "Neighborhood pro",
                "type": "ai_actor",
                "persona": "local professional with neighborly credibility",
                "look": "casual service setting, warm smile, local business context",
                "badge": "Local pro",
            },
            {
                "id": "front-desk-guide",
                "name": "Front desk guide",
                "type": "ai_actor",
                "persona": "helpful scheduler who makes booking feel easy",
                "look": "front desk background, clear CTA posture, friendly expression",
                "badge": "Scheduler",
            },
            {
                "id": "premium-advisor",
                "name": "Premium advisor",
                "type": "ai_actor",
                "persona": "trust-first advisor for higher-value purchases",
                "look": "premium showroom or consultation setting, measured delivery",
                "badge": "Advisor",
            },
            {
                "id": "modern-founder",
                "name": "Modern founder",
                "type": "ai_actor",
                "persona": "design-aware founder explaining premium product decisions",
                "look": "bright studio or showroom, premium-casual wardrobe, calm delivery",
                "badge": "Founder",
            },
            {
                "id": "wellness-host",
                "name": "Wellness host",
                "type": "ai_actor",
                "persona": "friendly expert for beauty, wellness, and lifestyle offers",
                "look": "clean wellness interior, polished camera framing, warm expression",
                "badge": "Host",
            },
            {
                "id": "retail-specialist",
                "name": "Retail specialist",
                "type": "ai_actor",
                "persona": "in-store product explainer with confident but approachable tone",
                "look": "boutique or retail floor, product-in-hand posture, clear CTA energy",
                "badge": "Retail",
            },
            {
                "id": "service-mentor",
                "name": "Service mentor",
                "type": "ai_actor",
                "persona": "seasoned operator who explains what premium service really means",
                "look": "professional interior, trust-first posture, direct-to-camera framing",
                "badge": "Mentor",
            },
        ],
        "templates": [
            {
                "id": "hook-proof-cta",
                "title": "Hook / proof / CTA",
                "format": "9:16 creator video",
                "durationSeconds": 24,
                "summary": "Hook in 3 seconds, one proof moment, one direct CTA.",
                "sceneStyle": "actor + service b-roll + branded end card",
            },
            {
                "id": "problem-solution",
                "title": "Problem / solution",
                "format": "9:16 explainer",
                "durationSeconds": 28,
                "summary": "Show the pain, explain the fix, then invite a call or booking.",
                "sceneStyle": "problem caption + actor explainer + checklist overlay",
            },
            {
                "id": "offer-walkthrough",
                "title": "Offer walkthrough",
                "format": "9:16 short ad",
                "durationSeconds": 20,
                "summary": "A compact promo format for fancy product or premium service offers.",
                "sceneStyle": "product/service beauty shot + actor narration + CTA card",
            },
            {
                "id": "subtitle-punch",
                "title": "Subtitle punch",
                "format": "9:16 caption-led video",
                "durationSeconds": 22,
                "summary": "Large kinetic subtitles, short beats, and a bold closing CTA.",
                "sceneStyle": "actor hook + animated captions + product/service insert",
            },
            {
                "id": "premium-comparison",
                "title": "Premium comparison",
                "format": "9:16 comparison explainer",
                "durationSeconds": 26,
                "summary": "Compare cheap vs premium choices without making unsupported claims.",
                "sceneStyle": "split proof frame + actor explanation + CTA lower-third",
            },
            {
                "id": "owner-note",
                "title": "Owner note",
                "format": "9:16 founder-style clip",
                "durationSeconds": 24,
                "summary": "A founder-style recommendation that feels personal and approval-ready.",
                "sceneStyle": "direct-to-camera note + local proof overlay + schedule card",
            },
            {
                "id": "caption-flash",
                "title": "Caption flash",
                "format": "9:16 fast-caption reel",
                "durationSeconds": 18,
                "summary": "Rapid subtitle beats with a quick product or service payoff.",
                "sceneStyle": "large kinetic captions + short proof flashes + CTA button card",
            },
            {
                "id": "center-punch",
                "title": "Center punch",
                "format": "9:16 centered subtitle layout",
                "durationSeconds": 21,
                "summary": "Bold centered subtitles with a clean mid-frame actor layout.",
                "sceneStyle": "centered caption rhythm + actor close-up + branded lower-third",
            },
            {
                "id": "bottom-caption",
                "title": "Bottom caption",
                "format": "9:16 creator explainer",
                "durationSeconds": 23,
                "summary": "Traditional lower subtitle track with clean readability for spoken copy.",
                "sceneStyle": "actor explainer + bottom subtitles + proof insert + CTA card",
            },
            {
                "id": "quote-overlay",
                "title": "Quote overlay",
                "format": "9:16 testimonial style",
                "durationSeconds": 20,
                "summary": "Use quote-style subtitles to turn a recommendation into social proof.",
                "sceneStyle": "quote captions + actor recommendation + offer highlight",
            },
            {
                "id": "staggered-words",
                "title": "Staggered words",
                "format": "9:16 motion subtitle layout",
                "durationSeconds": 22,
                "summary": "Stagger words across multiple rows for a more animated subtitle feel.",
                "sceneStyle": "staggered kinetic subtitles + actor hook + CTA end card",
            },
        ],
    }


def option_by_id(options, option_id):
    return next((item for item in options if item["id"] == option_id), options[0] if options else {})


def creator_style_idea_options(prompt, goal):
    normalized_prompt = prompt or "promote products that look premium"
    normalized_goal = goal or "lead more sales"
    return [
        {
            "id": "premium-problem",
            "label": "Premium problem opener",
            "hook": f"Most people wait too long before they act on {normalized_prompt}.",
            "angle": "Start with the hesitation, then make the next step feel simple and local.",
            "goalFit": normalized_goal,
            "confidence": "high",
        },
        {
            "id": "fancy-before-after",
            "label": "Fancy before/after moment",
            "hook": f"Here is the simple upgrade that makes {normalized_prompt} feel more premium.",
            "angle": "Show the transformation, explain the value, then ask for the sale or booking.",
            "goalFit": normalized_goal,
            "confidence": "medium",
        },
        {
            "id": "owner-recommendation",
            "label": "Owner recommendation",
            "hook": f"If your goal is to {normalized_goal}, this is the version I would recommend first.",
            "angle": "Use a direct owner-style recommendation with transparent constraints.",
            "goalFit": normalized_goal,
            "confidence": "high",
        },
    ]


def creator_script_from_selection(prompt, goal, idea, style, actor, template):
    topic = prompt or "promote products that look premium"
    target = goal or "lead more sales"
    hook = idea.get("hook") or f"Here is a better way to {topic}."
    return {
        "lines": [
            f"Hook: {hook}",
            f"Context: The viewer wants something that feels premium, but still needs a clear reason to act.",
            f"Value: {style.get('scriptTone', 'clear local guidance')}.",
            f"CTA: If you want to {target}, start with this offer and book the next step today.",
        ],
        "caption": f"{topic}. {target}. Demo-safe creator-style video storyboard with owner approval before publishing.",
        "disclosure": "AI actor storyboard generated for review; production publishing requires account connection and disclosure checks.",
        "actorDirection": actor.get("look", "direct-to-camera local expert"),
        "templateDirection": template.get("sceneStyle", "actor + b-roll + CTA card"),
    }


def creator_scenes_from_selection(script, actor, template):
    return [
        {
            "secondRange": "0-3",
            "shot": f"{actor.get('name', 'AI actor')} opens direct-to-camera with a fast hook.",
            "caption": script["lines"][0].replace("Hook: ", ""),
        },
        {
            "secondRange": "4-10",
            "shot": "Premium product/service visual with one concise benefit overlay.",
            "caption": "Make the value obvious before the viewer scrolls.",
        },
        {
            "secondRange": "11-18",
            "shot": f"{actor.get('persona', 'Local expert')} explains the offer in plain language.",
            "caption": script["lines"][2].replace("Value: ", ""),
        },
        {
            "secondRange": "19-24",
            "shot": f"{template.get('title', 'CTA card')} with brand color, phone/action CTA, and proof-safe note.",
            "caption": "Book the next step after owner approval.",
        },
    ]


def seed_phase3_creator_workflows(conn, commit=True):
    existing = conn.execute(
        "select count(*) from creator_style_workflows where merchant_id = ?",
        (DEMO_MERCHANT_ID,),
    ).fetchone()[0]
    if existing:
        return
    now = utc_now()
    options = creator_style_options()
    prompt = "promote products that looks fancy"
    goal = "lead more sales"
    ideas = creator_style_idea_options(prompt, goal)
    style = option_by_id(options["styles"], "motivational")
    actor = option_by_id(options["actors"], "local-owner")
    template = option_by_id(options["templates"], "hook-proof-cta")
    script = creator_script_from_selection(prompt, goal, ideas[0], style, actor, template)
    conn.execute(
        """
        insert into creator_style_workflows (
          id, merchant_id, creative_id, prompt, goal, ideas_json, selected_idea_id,
          style_id, actor_json, template_json, script_json, publish_json, status,
          created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "creator_workflow_scribe_seed",
            DEMO_MERCHANT_ID,
            None,
            prompt,
            goal,
            json_dumps(ideas),
            ideas[0]["id"],
            style["id"],
            json_dumps(actor),
            json_dumps(template),
            json_dumps(script),
            json_dumps(
                {
                    "destination": "assisted_tiktok_or_facebook_reel",
                    "scheduleStep": "Schedule Post after owner approval",
                    "ownerApprovalRequired": True,
                }
            ),
            "ideas_ready",
            now,
            now,
        ),
    )
    if commit:
        conn.commit()


def seed_phase3_analytics(conn, commit=True):
    existing = conn.execute(
        "select count(*) from performance_snapshots where merchant_id = ?",
        (DEMO_MERCHANT_ID,),
    ).fetchone()[0]
    if existing:
        return
    rows = conn.execute(
        "select * from generated_creatives where merchant_id = ? order by platform",
        (DEMO_MERCHANT_ID,),
    ).fetchall()
    if not rows:
        return
    now = utc_now()
    metrics_by_platform = {
        "facebook": (1840, 1390, 146, 58, 17, 0, 51000, "medium", {"comments": 12, "shares": 9, "callTaps": 17}),
        "instagram": (2260, 1710, 232, 71, 21, 0, 63000, "medium", {"saves": 48, "dmKeywords": 21, "carouselCompletes": 82}),
        "tiktok": (3180, 2550, 291, 44, 11, 0, 33000, "low", {"watchThroughRate": "31%", "profileVisits": 27, "shares": 14}),
        "google_business": (920, 740, 88, 39, 18, 0, 54000, "medium", {"directionTaps": 18, "callTaps": 12, "websiteClicks": 9}),
    }
    for row in rows:
        metrics = metrics_by_platform.get(row["platform"]) or (800, 640, 55, 19, 6, 0, 18000, "low", {})
        conn.execute(
            "insert into performance_snapshots values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_id("performance"),
                row["id"],
                DEMO_MERCHANT_ID,
                row["platform"],
                metrics[0],
                metrics[1],
                metrics[2],
                metrics[3],
                metrics[4],
                metrics[5],
                metrics[6],
                metrics[7],
                json_dumps(metrics[8]),
                now,
                now,
            ),
        )
    top_creative = rows[0]
    for title, insight, recommendation, confidence, related_id in [
        (
            "Top local response channel",
            "Google Business and Facebook are producing the clearest call and direction intent.",
            "Keep appointment CTAs on Facebook/Google and use TikTok/Instagram for awareness and DM capture.",
            "medium",
            top_creative["id"],
        ),
        (
            "Creative angle to repeat",
            "Checklist and owner-explainer formats are driving stronger saves, comments, and call taps than generic offer copy.",
            "Generate the next batch around a homeowner checklist plus a short owner answer video.",
            "medium",
            rows[min(1, len(rows) - 1)]["id"],
        ),
        (
            "Lower-bound value guardrail",
            "Reported value only counts observable calls, DMs, map actions, and owner-confirmed mentions; it does not claim exact offline revenue.",
            "Use the proof loop as sales evidence, then connect phone/booking systems before claiming stronger attribution.",
            "high",
            top_creative["id"],
        ),
    ]:
        conn.execute(
            "insert into analytics_insights values (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_id("analytics_insight"),
                DEMO_MERCHANT_ID,
                title,
                insight,
                recommendation,
                confidence,
                related_id,
                now,
            ),
        )
    if commit:
        conn.commit()


def seed_phase3_template_library(conn, commit=True):
    existing = conn.execute(
        "select count(*) from creative_templates where merchant_id = ?",
        (DEMO_MERCHANT_ID,),
    ).fetchone()[0]
    if existing:
        return
    now = utc_now()
    templates = [
        (
            "template_canva_heatwave_checklist",
            "Canva",
            "Heat-wave checklist carousel",
            "3-slide carousel",
            "4:5",
            "local service carousel",
            "localpilot-template/canva/heatwave-checklist.webp",
            {
                "layers": [
                    {"id": "headline", "label": "Headline", "placement": "cover top", "style": "bold_hook"},
                    {"id": "checklist", "label": "Checklist", "placement": "slide body", "style": "icon_rows"},
                    {"id": "cta", "label": "CTA", "placement": "footer", "style": "button"},
                    {"id": "brand_color", "label": "Brand color", "placement": "theme", "style": "palette"},
                ],
                "sourceUrl": "https://canva.com/demo/localpilot-heatwave-checklist",
            },
        ),
        (
            "template_figma_service_story",
            "Figma",
            "Technician service story reel",
            "20-second vertical reel",
            "9:16",
            "short video storyboard",
            "localpilot-template/figma/service-story-reel.webp",
            {
                "layers": [
                    {"id": "hook_text", "label": "Hook text", "placement": "0-3s", "style": "caption_overlay"},
                    {"id": "scene_order", "label": "Scene order", "placement": "timeline", "style": "storyboard"},
                    {"id": "captions", "label": "Captions", "placement": "lower third", "style": "subtitles"},
                    {"id": "cta", "label": "CTA", "placement": "end card", "style": "phone_link"},
                ],
                "sourceUrl": "https://figma.com/file/localpilot-service-story-reel",
            },
        ),
        (
            "template_adobe_offer_card",
            "Adobe Express",
            "Same-week offer card",
            "1:1 feed image",
            "1:1",
            "offer announcement",
            "localpilot-template/adobe/same-week-offer-card.webp",
            {
                "layers": [
                    {"id": "headline", "label": "Headline", "placement": "top safe zone", "style": "large_type"},
                    {"id": "body_copy", "label": "Body copy", "placement": "center", "style": "short_paragraph"},
                    {"id": "phone_cta", "label": "Phone CTA", "placement": "bottom", "style": "contact_badge"},
                    {"id": "service_area", "label": "Service area", "placement": "footer", "style": "local_badge"},
                ],
                "sourceUrl": "https://express.adobe.com/demo/localpilot-same-week-offer",
            },
        ),
    ]
    for template in templates:
        conn.execute(
            "insert into creative_templates values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                template[0],
                DEMO_MERCHANT_ID,
                template[1],
                template[2],
                template[3],
                template[4],
                template[5],
                template[6],
                json_dumps(template[7]),
                "ready",
                now,
                now,
            ),
        )
    for item in [
        (
            "asset_hvac_technician_rooftop",
            "photo",
            "HVAC technician roof unit",
            "LocalPilot premium library",
            "demo_premium_safe",
            ["technician", "hvac", "service", "local"],
            "localpilot-assets/premium/hvac-technician-rooftop.webp",
            "Best for trust-builder posts and service story reels.",
        ),
        (
            "asset_homeowner_thermostat",
            "photo",
            "Homeowner checking thermostat",
            "LocalPilot premium library",
            "demo_premium_safe",
            ["homeowner", "thermostat", "comfort", "summer"],
            "localpilot-assets/premium/homeowner-thermostat.webp",
            "Best for heat-wave readiness hooks.",
        ),
        (
            "asset_ac_checklist_icons",
            "icon_set",
            "AC tune-up checklist icons",
            "LocalPilot generated asset library",
            "demo_generated_safe",
            ["checklist", "icons", "maintenance", "carousel"],
            "localpilot-assets/generated/ac-checklist-icons.svg",
            "Best for carousel checklist slides and Google Business updates.",
        ),
    ]:
        conn.execute(
            "insert into asset_library_items values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item[0],
                DEMO_MERCHANT_ID,
                item[1],
                item[2],
                item[3],
                item[4],
                json_dumps(item[5]),
                item[6],
                item[7],
                "ready",
                now,
                now,
            ),
        )
    if commit:
        conn.commit()


def generated_creative_templates(prompt, objective):
    return [
        {
            "platform": "facebook",
            "format": "community post",
            "title": "Neighborhood AC tune-up reminder",
            "caption": f"Aurora Heating & Cooling is booking {prompt}. Local homeowners can call ahead and get on the schedule before the next warm stretch.",
            "hashtags": ["#AnnArbor", "#HVAC", "#LocalService"],
            "cta": "Call Aurora to schedule",
            "proofHook": "call tap + owner-confirmed mention",
            "scheduleSlot": "Wednesday 6:00 PM",
            "status": "needs_review",
        },
        {
            "platform": "instagram",
            "format": "carousel",
            "title": "AC tune-up checklist carousel",
            "caption": f"Save this before the heat hits: 5 signs your AC needs a tune-up. DM COOL for openings. Goal: {objective}.",
            "hashtags": ["#HomeTips", "#AnnArborHomes", "#HVACService"],
            "cta": "DM COOL",
            "proofHook": "DM keyword + booking click",
            "scheduleSlot": "Tuesday 12:30 PM",
            "status": "assisted_package",
        },
        {
            "platform": "tiktok",
            "format": "reel script",
            "title": "POV: AC checked before the heat wave",
            "caption": f"POV: you booked {prompt} before everyone else called during the heat wave.",
            "hashtags": ["#HVACTips", "#HomeownerTok", "#MichiganWeather"],
            "cta": "Call to schedule",
            "proofHook": "short link + call tap",
            "scheduleSlot": "Monday 9:00 AM",
            "status": "assisted_package",
        },
        {
            "platform": "google_business",
            "format": "business profile update",
            "title": "Same-week AC service near you",
            "caption": f"{prompt}. Tap for directions or call Aurora Heating & Cooling for local service.",
            "hashtags": ["#LocalHVAC"],
            "cta": "Get directions",
            "proofHook": "direction tap + call tap",
            "scheduleSlot": "Friday 10:00 AM",
            "status": "assisted_package",
        },
    ]


def media_asset_templates_for_creative(template):
    platform = template["platform"]
    title = template["title"]
    caption = template["caption"]
    if platform == "instagram":
        return [
            {
                "assetType": "carousel_storyboard",
                "format": "3-slide carousel",
                "aspectRatio": "4:5",
                "prompt": f"Create a branded three-slide HVAC carousel for: {title}",
                "metadata": {
                    "slides": [
                        "Cover: heat-wave readiness hook with Aurora brand colors",
                        "Slide 2: quick homeowner checklist with simple icons",
                        "Slide 3: DM COOL CTA plus proof-link/coupon footer",
                    ],
                    "editableLayers": ["headline", "checklist", "cta", "brand_color"],
                    "safeZones": ["feed crop", "reel remix", "story frame"],
                },
            }
        ]
    if platform == "tiktok":
        return [
            {
                "assetType": "video_storyboard",
                "format": "20-second vertical reel",
                "aspectRatio": "9:16",
                "prompt": f"Create a vertical short-video storyboard for: {caption}",
                "metadata": {
                    "durationSeconds": 20,
                    "scenes": [
                        "0-3s: technician opens AC panel with text hook",
                        "4-9s: close-up filter/checklist moment",
                        "10-15s: owner explains why early tune-ups prevent urgent calls",
                        "16-20s: call-to-schedule CTA and tracked short link",
                    ],
                    "editableLayers": ["hook_text", "scene_order", "cta", "captions"],
                    "audioDirection": "clean local expert voiceover, no exaggerated claims",
                },
            }
        ]
    if platform == "google_business":
        return [
            {
                "assetType": "business_profile_image",
                "format": "Google Business update image",
                "aspectRatio": "16:9",
                "prompt": f"Create a local service update image for: {title}",
                "metadata": {
                    "placements": ["business profile update", "map result preview"],
                    "editableLayers": ["headline", "service_area", "phone_cta"],
                    "safeZones": ["mobile business profile crop"],
                },
            }
        ]
    return [
        {
            "assetType": "static_social_post",
            "format": "1:1 feed image",
            "aspectRatio": "1:1",
            "prompt": f"Create a branded local-service feed post for: {title}",
            "metadata": {
                "placements": ["Facebook Page feed", "Instagram square fallback"],
                "editableLayers": ["headline", "body_copy", "cta", "brand_color"],
                "safeZones": ["feed crop", "mobile preview"],
            },
        }
    ]


def insert_media_assets_for_creative(conn, creative_id, template, now):
    assets = []
    for asset in media_asset_templates_for_creative(template):
        asset_id = new_id("creative_asset")
        storage_ref = f"localpilot-generated/phase3/{creative_id}/{asset['assetType']}.json"
        conn.execute(
            """
            insert into creative_media_assets (
              id, creative_id, merchant_id, asset_type, format, aspect_ratio, storage_ref,
              prompt, status, provider, metadata_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                creative_id,
                DEMO_MERCHANT_ID,
                asset["assetType"],
                asset["format"],
                asset["aspectRatio"],
                storage_ref,
                asset["prompt"],
                "ready_preview",
                "localpilot_deterministic_media_planner",
                json_dumps(asset["metadata"]),
                now,
                now,
            ),
        )
        assets.append(asset_id)
    return assets


def ensure_phase3_media_assets(conn):
    now = utc_now()
    rows = conn.execute("select * from generated_creatives where merchant_id = ?", (DEMO_MERCHANT_ID,)).fetchall()
    for row in rows:
        existing = conn.execute(
            "select count(*) from creative_media_assets where creative_id = ?",
            (row["id"],),
        ).fetchone()[0]
        if existing:
            continue
        template = {
            "platform": row["platform"],
            "format": row["format"],
            "title": row["title"],
            "caption": row["caption"],
        }
        insert_media_assets_for_creative(conn, row["id"], template, now)
    conn.commit()


def create_content_batch(conn, payload, commit=True):
    now = utc_now()
    merchant_id = payload.get("merchantId") or DEMO_MERCHANT_ID
    prompt = (payload.get("sourcePrompt") or payload.get("prompt") or "").strip()
    if not prompt:
        prompt = "Same-week AC tune-up appointments before the next hot stretch"
    objective = (payload.get("objective") or "book local calls and appointments").strip()
    campaign = conn.execute(
        "select * from campaigns where merchant_id = ? order by created_at desc limit 1",
        (merchant_id,),
    ).fetchone()
    batch_id = new_id("batch")
    conn.execute(
        "insert into content_batches values (?, ?, ?, ?, ?, ?, ?, ?)",
        (batch_id, merchant_id, campaign["id"] if campaign else None, prompt, objective, "generated", now, now),
    )
    creatives = []
    for template in generated_creative_templates(prompt, objective):
        creative_id = new_id("creative")
        conn.execute(
            """
            insert into generated_creatives (
              id, batch_id, merchant_id, platform, format, title, caption, hashtags_json,
              cta, proof_hook, schedule_slot, status, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                creative_id,
                batch_id,
                merchant_id,
                template["platform"],
                template["format"],
                template["title"],
                template["caption"],
                json_dumps(template["hashtags"]),
                template["cta"],
                template["proofHook"],
                template["scheduleSlot"],
                template["status"],
                now,
                now,
            ),
        )
        conn.execute(
            "insert into calendar_slots values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_id("slot"),
                creative_id,
                merchant_id,
                template["platform"],
                template["scheduleSlot"],
                "",
                "scheduled" if template["platform"] == "facebook" else "assisted",
                now,
                now,
            ),
        )
        proof_id = new_id("proof")
        code = f"AURORA-{template['platform'].replace('_', '').upper()}"
        conn.execute(
            "insert into proof_links values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                proof_id,
                creative_id,
                merchant_id,
                "short_link",
                code,
                f"https://auroraheatcool.example/offers/{code.lower()}",
                f"https://lp.local/{code.lower()}",
                f"localpilot-proof/qr/{code}.svg",
                code if template["platform"] in {"instagram", "tiktok"} else None,
                now,
                now,
            ),
        )
        insert_media_assets_for_creative(conn, creative_id, template, now)
        creatives.append(serialize_generated_creative(conn, creative_id))
    if commit:
        conn.commit()
    return {"batch": serialize_content_batch(conn, batch_id), "creatives": creatives}


def create_content_source_import(conn, payload):
    now = utc_now()
    merchant_id = payload.get("merchantId") or DEMO_MERCHANT_ID
    requested_type = (payload.get("sourceType") or "").strip().lower()
    image_data_url = (payload.get("imageDataUrl") or payload.get("previewDataUrl") or "").strip()
    source_type = "image" if requested_type == "image" or image_data_url else "url"
    source_id = new_id("content_source")
    label = (payload.get("label") or payload.get("title") or ("Uploaded source image" if source_type == "image" else "Imported source page")).strip()
    if source_type == "image":
        if not image_data_url.startswith("data:image/"):
            raise StoreError(400, "Source image must be provided as a data:image/* preview.")
        if len(image_data_url) > 1_200_000:
            raise StoreError(400, "Source image preview is too large for the local demo import.")
        mime_type = image_data_url[5 : image_data_url.find(";")] if ";" in image_data_url else "image/*"
        file_name = (payload.get("fileName") or payload.get("imageName") or "uploaded-source-image").strip()
        url = f"localpilot-source-images/{source_id}"
        extracted = {
            "title": label,
            "detectedBusiness": "Aurora Heating & Cooling",
            "detectedOffer": "same-week AC tune-up appointments",
            "sourceKind": "uploaded_image",
            "fileName": file_name,
            "mimeType": mime_type,
            "previewDataUrl": image_data_url,
            "byteEstimate": len(image_data_url),
        }
    else:
        url = (payload.get("url") or payload.get("sourceUrl") or "").strip()
        if not url:
            raise StoreError(400, "Source URL is required.")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise StoreError(400, "Source URL must start with http:// or https://.")

        parsed_url = urlparse(url)
        extracted = {
            "title": label,
            "detectedBusiness": "Aurora Heating & Cooling",
            "detectedOffer": "same-week AC tune-up appointments",
            "sourceKind": "local_service_page",
            "urlHost": parsed_url.netloc,
        }
    conn.execute(
        "insert into content_sources values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            source_id,
            merchant_id,
            source_type,
            label,
            url,
            "analyzed_demo",
            json_dumps(extracted),
            json_dumps(content_source_brief(label, url, source_type)),
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute("select * from content_sources where id = ?", (source_id,)).fetchone()
    return {"source": serialize_content_source(row), "workspace": get_phase3_workspace(conn)}


def assistant_outline(prompt):
    topic = prompt or "same-week AC tune-up appointments"
    return [
        {
            "day": "Monday",
            "postIdea": "Owner tip that explains why early tune-ups prevent emergency calls.",
            "format": "Facebook Page post",
        },
        {
            "day": "Wednesday",
            "postIdea": "Short video script showing the top three checks before a heat wave.",
            "format": "TikTok/Reel assisted package",
        },
        {
            "day": "Friday",
            "postIdea": "Local proof post with call taps, map directions, and a booking CTA.",
            "format": "Google/Facebook local update",
        },
    ], f"{topic} -> 3-post local content calendar with owner trust, service proof, and call-to-book CTA"


def create_ai_assistant_reply(conn, payload):
    now = utc_now()
    prompt = (payload.get("prompt") or payload.get("message") or "").strip()
    if not prompt:
        raise StoreError(400, "AI Assistant prompt is required.")
    outline, source_prompt = assistant_outline(prompt)
    reply_text = (
        f"Here is a LocalPilot calendar outline for {prompt}: lead with one owner tip, "
        "follow with one short-form explainer, and close the week with a proof-backed booking CTA."
    )
    reply_id = new_id("assistant_reply")
    conn.execute(
        "insert into ai_assistant_replies values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            reply_id,
            DEMO_MERCHANT_ID,
            prompt,
            reply_text,
            json_dumps(outline),
            source_prompt,
            "ready",
            now,
            now,
        ),
    )
    conn.commit()
    reply = serialize_ai_assistant_reply(
        conn.execute("select * from ai_assistant_replies where id = ?", (reply_id,)).fetchone()
    )
    return {"reply": reply, "workspace": get_phase3_workspace(conn)}


def create_content_batch_from_ai_reply(conn, reply_id):
    row = conn.execute(
        "select * from ai_assistant_replies where id = ? and merchant_id = ?",
        (reply_id, DEMO_MERCHANT_ID),
    ).fetchone()
    if row is None:
        raise StoreError(404, "AI Assistant reply not found.")
    result = create_content_batch(
        conn,
        {
            "sourcePrompt": row["source_prompt"],
            "objective": "turn AI assistant reply into approved local social posts",
        },
        commit=False,
    )
    now = utc_now()
    conn.execute(
        "update ai_assistant_replies set status = ?, updated_at = ? where id = ?",
        ("converted_to_posts", now, reply_id),
    )
    conn.commit()
    reply = serialize_ai_assistant_reply(
        conn.execute("select * from ai_assistant_replies where id = ?", (reply_id,)).fetchone()
    )
    return {**result, "reply": reply, "workspace": get_phase3_workspace(conn)}


def create_creator_style_video_workflow(conn, payload):
    now = utc_now()
    prompt = str(payload.get("prompt") or payload.get("sourcePrompt") or "").strip()
    if not prompt:
        prompt = "promote products that look premium"
    goal = str(payload.get("goal") or payload.get("objective") or "").strip()
    if not goal:
        goal = "lead more sales"
    options = creator_style_options()
    ideas = creator_style_idea_options(prompt, goal)
    selected_idea_id = str(payload.get("selectedIdeaId") or ideas[0]["id"]).strip()
    if selected_idea_id not in {idea["id"] for idea in ideas}:
        selected_idea_id = ideas[0]["id"]
    style = option_by_id(options["styles"], str(payload.get("styleId") or "motivational").strip())
    actor = option_by_id(options["actors"], str(payload.get("actorId") or "local-owner").strip())
    template = option_by_id(options["templates"], str(payload.get("templateId") or "hook-proof-cta").strip())
    idea = option_by_id(ideas, selected_idea_id)
    script = creator_script_from_selection(prompt, goal, idea, style, actor, template)
    workflow_id = new_id("creator_workflow")
    conn.execute(
        """
        insert into creator_style_workflows (
          id, merchant_id, creative_id, prompt, goal, ideas_json, selected_idea_id,
          style_id, actor_json, template_json, script_json, publish_json, status,
          created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            workflow_id,
            DEMO_MERCHANT_ID,
            None,
            prompt[:500],
            goal[:240],
            json_dumps(ideas),
            selected_idea_id,
            style["id"],
            json_dumps(actor),
            json_dumps(template),
            json_dumps(script),
            json_dumps(
                {
                    "destination": "assisted_tiktok_or_facebook_reel",
                    "scheduleStep": "Schedule Post after owner approval",
                    "ownerApprovalRequired": True,
                }
            ),
            "ideas_ready",
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute("select * from creator_style_workflows where id = ?", (workflow_id,)).fetchone()
    return {"workflow": serialize_creator_style_workflow(row), "workspace": get_phase3_workspace(conn)}


def create_creator_style_video(conn, workflow_id, payload):
    workflow = conn.execute(
        "select * from creator_style_workflows where id = ? and merchant_id = ?",
        (workflow_id, DEMO_MERCHANT_ID),
    ).fetchone()
    if workflow is None:
        raise StoreError(404, "Creator-style video workflow not found.")
    now = utc_now()
    options = creator_style_options()
    prompt = str(payload.get("prompt") or workflow["prompt"] or "").strip()[:500]
    goal = str(payload.get("goal") or workflow["goal"] or "").strip()[:240]
    ideas = json_loads(workflow["ideas_json"], []) or creator_style_idea_options(prompt, goal)
    selected_idea_id = str(payload.get("selectedIdeaId") or workflow["selected_idea_id"] or ideas[0]["id"]).strip()
    if selected_idea_id not in {idea["id"] for idea in ideas}:
        selected_idea_id = ideas[0]["id"]
    style = option_by_id(options["styles"], str(payload.get("styleId") or workflow["style_id"] or "motivational").strip())
    actor = option_by_id(options["actors"], str(payload.get("actorId") or json_loads(workflow["actor_json"], {}).get("id") or "local-owner").strip())
    template = option_by_id(options["templates"], str(payload.get("templateId") or json_loads(workflow["template_json"], {}).get("id") or "hook-proof-cta").strip())
    aspect_ratio = str(payload.get("aspectRatio") or "9:16").strip() or "9:16"
    idea = option_by_id(ideas, selected_idea_id)
    script = creator_script_from_selection(prompt, goal, idea, style, actor, template)
    scenes = creator_scenes_from_selection(script, actor, template)
    campaign = conn.execute("select * from campaigns order by created_at desc limit 1").fetchone()
    batch_id = new_id("batch")
    conn.execute(
        "insert into content_batches values (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            batch_id,
            DEMO_MERCHANT_ID,
            campaign["id"] if campaign else None,
            f"Creator-style video: {prompt}",
            goal,
            "generated",
            now,
            now,
        ),
    )
    creative_id = new_id("creative")
    title = idea.get("label") or "Creator-style video"
    caption = script["caption"]
    cta = "Book the next step"
    conn.execute(
        """
        insert into generated_creatives (
          id, batch_id, merchant_id, platform, format, title, caption, hashtags_json,
          cta, proof_hook, schedule_slot, status, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            creative_id,
            batch_id,
            DEMO_MERCHANT_ID,
            "tiktok",
            "creator-style video",
            title[:180],
            caption[:1200],
            json_dumps(["#LocalBusiness", "#CreatorStyle", "#AIActor", "#OwnerApproved"]),
            cta,
            "owner-approved schedule + tracked assisted handoff",
            "Thursday 10:00 AM",
            "needs_review",
            now,
            now,
        ),
    )
    asset_id = new_id("creative_asset")
    metadata = {
        "workflowId": workflow_id,
        "referenceWorkflow": "Predis-style creator video: idea -> style -> actor -> template -> generate -> publish/schedule",
        "prompt": prompt,
        "goal": goal,
        "idea": idea,
        "style": style,
        "actor": actor,
        "template": template,
        "durationSeconds": template.get("durationSeconds", 24),
        "scenes": scenes,
        "editableLayers": ["hook_text", "actor_direction", "scene_order", "captions", "cta"],
        "safeZones": ["caption safe zone", "CTA lower-third", "AI disclosure area"],
        "publishReadiness": {
            "ownerApprovalRequired": True,
            "officialAccountRequired": True,
            "readyForCalendar": True,
        },
    }
    conn.execute(
        """
        insert into creative_media_assets (
          id, creative_id, merchant_id, asset_type, format, aspect_ratio, storage_ref,
          prompt, status, provider, metadata_json, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset_id,
            creative_id,
            DEMO_MERCHANT_ID,
            "creator_style_video_storyboard",
            template.get("format", "9:16 creator video"),
            aspect_ratio,
            f"localpilot-generated/phase3/{creative_id}/creator-style-video.json",
            f"{prompt} | {goal} | {style.get('label')} | {actor.get('name')}",
            "storyboard_ready",
            "localpilot_creator_style_demo_backend",
            json_dumps(metadata),
            now,
            now,
        ),
    )
    package_id = new_id("ugc_package")
    voiceover = {
        "tone": style.get("scriptTone", "clear local expert"),
        "pace": "fast hook, calm explanation, direct CTA",
        "language": payload.get("language") or "English",
        "durationSeconds": template.get("durationSeconds", 24),
        "direction": "creator-style AI actor narration; no exaggerated claims",
    }
    export_spec = {
        "format": template.get("format", "9:16 creator video"),
        "resolution": "1080x1920",
        "frameRate": "30fps storyboard target",
        "safeZones": metadata["safeZones"],
        "productionNextStep": "connect a real avatar/video renderer before claiming rendered video output",
    }
    conn.execute(
        """
        insert into creative_ugc_packages (
          id, creative_id, merchant_id, package_label, avatar_json, voiceover_json,
          script_json, scenes_json, export_json, status, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            package_id,
            creative_id,
            DEMO_MERCHANT_ID,
            f"{style.get('label', 'Creator')} {actor.get('name', 'AI actor')} package",
            json_dumps(actor),
            json_dumps(voiceover),
            json_dumps(script),
            json_dumps(scenes),
            json_dumps(export_spec),
            "storyboard_ready",
            now,
            now,
        ),
    )
    slot_id = new_id("slot")
    conn.execute(
        "insert into calendar_slots values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            slot_id,
            creative_id,
            DEMO_MERCHANT_ID,
            "tiktok",
            "Thursday 10:00 AM",
            "",
            "in_review",
            now,
            now,
        ),
    )
    code = f"AURORA-CREATOR-{creative_id[-6:].upper()}"
    conn.execute(
        "insert into proof_links values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            new_id("proof"),
            creative_id,
            DEMO_MERCHANT_ID,
            "short_link",
            code,
            f"https://auroraheatcool.example/offers/{code.lower()}",
            f"https://lp.local/{code.lower()}",
            f"localpilot-proof/qr/{code}.svg",
            "CREATOR",
            now,
            now,
        ),
    )
    creative_row = conn.execute("select * from generated_creatives where id = ?", (creative_id,)).fetchone()
    review_link = ensure_review_link_for_creative(conn, creative_row)
    publish = {
        "destination": "assisted_tiktok_or_facebook_reel",
        "scheduleStep": "Schedule Post",
        "ownerApprovalRequired": True,
        "calendarSlotId": slot_id,
        "reviewLinkId": review_link["id"],
        "status": "ready_for_publish_review",
    }
    conn.execute(
        """
        update creator_style_workflows
        set creative_id = ?, prompt = ?, goal = ?, ideas_json = ?, selected_idea_id = ?,
            style_id = ?, actor_json = ?, template_json = ?, script_json = ?,
            publish_json = ?, status = ?, updated_at = ?
        where id = ?
        """,
        (
            creative_id,
            prompt,
            goal,
            json_dumps(ideas),
            selected_idea_id,
            style["id"],
            json_dumps(actor),
            json_dumps(template),
            json_dumps(script),
            json_dumps(publish),
            "generated_ready",
            now,
            workflow_id,
        ),
    )
    conn.commit()
    updated_workflow = conn.execute("select * from creator_style_workflows where id = ?", (workflow_id,)).fetchone()
    slot = conn.execute("select * from calendar_slots where id = ?", (slot_id,)).fetchone()
    package = conn.execute("select * from creative_ugc_packages where id = ?", (package_id,)).fetchone()
    asset = conn.execute("select * from creative_media_assets where id = ?", (asset_id,)).fetchone()
    return {
        "workflow": serialize_creator_style_workflow(updated_workflow),
        "creative": serialize_generated_creative(conn, creative_id),
        "mediaAsset": serialize_creative_media_asset(conn, asset),
        "package": serialize_creative_ugc_package(package),
        "calendarSlot": serialize_calendar_slot(slot),
        "workspace": get_phase3_workspace(conn),
    }


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
        seed_phase3_data(conn)
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


def serialize_brand_kit(row):
    if row is None:
        return {}
    voice = json_loads(row["voice_json"], {})
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "logoRef": row["logo_ref"],
        "website": row["website"],
        "socialHandle": row["social_handle"],
        "colors": json_loads(row["colors_json"], []),
        "voice": voice,
        "voiceover": voice.get("voiceover") or "",
        "avatar": voice.get("avatar") or "",
        "hashtags": json_loads(row["hashtags_json"], []),
        "typography": json_loads(row["typography_json"], {}),
        "logos": json_loads(row["logos_json"], {}),
        "integrations": json_loads(row["integrations_json"], []),
        "approvedTerms": json_loads(row["approved_terms_json"], []),
        "avoidTerms": json_loads(row["avoid_terms_json"], []),
        "examples": json_loads(row["examples_json"], []),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


MERCHANT_PROFILE_FIELDS = (
    "name",
    "description",
    "industry",
    "logo_url",
    "primary_color",
    "secondary_color",
    "accent_color",
    "font_family",
    "language",
    "timezone",
    "tonality",
    "voiceover",
    "avatar",
    "target_audience",
)

_MERCHANT_PROFILE_COLOR_FIELDS = {"primary_color", "secondary_color", "accent_color"}
_MERCHANT_PROFILE_URL_FIELDS = {"crawl_url", "logo_url"}
_MERCHANT_PROFILE_DEFAULTS = {
    "voiceover": "Warm owner voice",
    "avatar": "Owner-style avatar",
}
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _sanitize_profile_text(value):
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return html.escape(" ".join(text.split()), quote=False)


def _sanitize_profile_url(value):
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
        return ""
    return text


def _sanitize_profile_color(value):
    text = str(value or "").strip()
    if not text or not _HEX_COLOR_RE.match(text):
        return ""
    return text.lower()


def _sanitize_profile_value(field, value):
    if field in _MERCHANT_PROFILE_COLOR_FIELDS:
        return _sanitize_profile_color(value)
    if field in _MERCHANT_PROFILE_URL_FIELDS:
        return _sanitize_profile_url(value)
    return _sanitize_profile_text(value)


def serialize_merchant_profile(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "status": row["status"],
        "crawlUrl": row["crawl_url"] or "",
        "name": row["name"],
        "description": row["description"],
        "industry": row["industry"],
        "logoUrl": row["logo_url"],
        "primaryColor": row["primary_color"],
        "secondaryColor": row["secondary_color"],
        "accentColor": row["accent_color"],
        "fontFamily": row["font_family"],
        "language": row["language"],
        "timezone": row["timezone"],
        "tonality": row["tonality"],
        "voiceover": row["voiceover"],
        "avatar": row["avatar"],
        "targetAudience": row["target_audience"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def get_merchant_profile(conn, merchant_id):
    return conn.execute(
        "select * from merchant_profiles where merchant_id = ? order by updated_at desc limit 1",
        (merchant_id,),
    ).fetchone()


def upsert_merchant_profile(conn, merchant_id, profile_data):
    existing = get_merchant_profile(conn, merchant_id)
    now = utc_now()
    payload = {}
    for field in MERCHANT_PROFILE_FIELDS:
        value = _sanitize_profile_value(field, profile_data.get(field))
        payload[field] = value or _MERCHANT_PROFILE_DEFAULTS.get(field, "")
    crawl_url = _sanitize_profile_value("crawl_url", profile_data.get("crawl_url") or profile_data.get("crawlUrl"))
    raw_extraction = profile_data.get("raw_extraction_json")
    if not isinstance(raw_extraction, (dict, list)):
        raw_extraction = {}
    if existing is None:
        conn.execute(
            """
            insert into merchant_profiles (
              id, merchant_id, status, crawl_url, name, description, industry, logo_url,
              primary_color, secondary_color, accent_color, font_family, language, timezone,
              tonality, voiceover, avatar, target_audience, raw_extraction_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("mprofile"),
                merchant_id,
                "draft",
                crawl_url,
                payload["name"],
                payload["description"],
                payload["industry"],
                payload["logo_url"],
                payload["primary_color"],
                payload["secondary_color"],
                payload["accent_color"],
                payload["font_family"],
                payload["language"],
                payload["timezone"],
                payload["tonality"],
                payload["voiceover"],
                payload["avatar"],
                payload["target_audience"],
                json_dumps(raw_extraction),
                now,
                now,
            ),
        )
    else:
        conn.execute(
            """
            update merchant_profiles
            set status = ?, crawl_url = ?, name = ?, description = ?, industry = ?, logo_url = ?,
                primary_color = ?, secondary_color = ?, accent_color = ?, font_family = ?,
                language = ?, timezone = ?, tonality = ?, voiceover = ?, avatar = ?, target_audience = ?,
                raw_extraction_json = ?, updated_at = ?
            where id = ?
            """,
            (
                "draft",
                crawl_url,
                payload["name"],
                payload["description"],
                payload["industry"],
                payload["logo_url"],
                payload["primary_color"],
                payload["secondary_color"],
                payload["accent_color"],
                payload["font_family"],
                payload["language"],
                payload["timezone"],
                payload["tonality"],
                payload["voiceover"],
                payload["avatar"],
                payload["target_audience"],
                json_dumps(raw_extraction),
                now,
                existing["id"],
            ),
        )
    conn.commit()
    return get_merchant_profile(conn, merchant_id)


def update_merchant_profile(conn, merchant_id, updates):
    current = get_merchant_profile(conn, merchant_id)
    if current is None:
        raise StoreError(404, "Merchant profile not found.")
    if current["status"] != "draft":
        raise StoreError(409, "Confirmed profiles cannot be edited.")
    fields = []
    values = []
    for field in ("crawl_url", *MERCHANT_PROFILE_FIELDS):
        if field in updates:
            fields.append(f"{field} = ?")
            values.append(_sanitize_profile_value(field, updates.get(field)))
            continue
        camel_case = "".join(part.title() if idx else part for idx, part in enumerate(field.split("_")))
        if camel_case in updates:
            fields.append(f"{field} = ?")
            values.append(_sanitize_profile_value(field, updates.get(camel_case)))
    if not fields:
        return current
    values.extend((utc_now(), current["id"]))
    conn.execute(
        f"update merchant_profiles set {', '.join(fields)}, updated_at = ? where id = ?",
        tuple(values),
    )
    conn.commit()
    return get_merchant_profile(conn, merchant_id)


def confirm_merchant_profile(conn, merchant_id):
    profile = get_merchant_profile(conn, merchant_id)
    if profile is None:
        raise StoreError(404, "Merchant profile not found.")
    now = utc_now()
    conn.execute(
        "update merchant_profiles set status = ?, updated_at = ? where id = ?",
        ("confirmed", now, profile["id"]),
    )
    refreshed = get_merchant_profile(conn, merchant_id)
    colors = [value for value in (refreshed["primary_color"], refreshed["secondary_color"], refreshed["accent_color"]) if value]
    brand = conn.execute(
        "select * from brand_kits where merchant_id = ? order by updated_at desc limit 1",
        (merchant_id,),
    ).fetchone()
    voice = json_loads(brand["voice_json"], {}) if brand else {}
    voice.update(
        {
            "tone": refreshed["tonality"],
            "audience": refreshed["target_audience"],
            "language": refreshed["language"],
            "description": refreshed["description"],
            "voiceover": refreshed["voiceover"],
            "avatar": refreshed["avatar"],
        }
    )
    typography = json_loads(brand["typography_json"], {}) if brand else {}
    if refreshed["font_family"]:
        typography.update(
            {
                "title": refreshed["font_family"],
                "body": refreshed["font_family"],
                "fontFamily": refreshed["font_family"],
            }
        )
    logos = json_loads(brand["logos_json"], {}) if brand else {}
    if refreshed["logo_url"]:
        logos.update(
            {
                "light": refreshed["logo_url"],
                "dark": refreshed["logo_url"],
                "sourceUrl": refreshed["logo_url"],
            }
        )
    if brand is None:
        conn.execute(
            """
            insert into brand_kits (
              id, merchant_id, logo_ref, website, social_handle, colors_json, voice_json,
              hashtags_json, typography_json, logos_json, integrations_json, approved_terms_json,
              avoid_terms_json, examples_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("brandkit"),
                merchant_id,
                refreshed["logo_url"],
                refreshed["crawl_url"] or "",
                "",
                json_dumps(colors),
                json_dumps(voice),
                json_dumps([]),
                json_dumps(typography),
                json_dumps(logos),
                json_dumps([]),
                json_dumps([]),
                json_dumps([]),
                json_dumps([]),
                now,
                now,
            ),
        )
    else:
        conn.execute(
            """
            update brand_kits
            set logo_ref = ?, website = ?, colors_json = ?, voice_json = ?, typography_json = ?,
                logos_json = ?, updated_at = ?
            where id = ?
            """,
            (
                refreshed["logo_url"] or brand["logo_ref"],
                refreshed["crawl_url"] or brand["website"],
                json_dumps(colors or json_loads(brand["colors_json"], [])),
                json_dumps(voice),
                json_dumps(typography),
                json_dumps(logos),
                now,
                brand["id"],
            ),
        )
    conn.commit()
    return get_merchant_profile(conn, merchant_id)


def ensure_phase8_onboarding_seed(conn):
    if get_merchant_profile(conn, DEMO_MERCHANT_ID) is not None:
        return
    now = utc_now()
    conn.execute(
        """
        insert into merchant_profiles (
          id, merchant_id, status, crawl_url, name, description, industry, logo_url,
          primary_color, secondary_color, accent_color, font_family, language, timezone,
          tonality, voiceover, avatar, target_audience, raw_extraction_json, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "mprofile_demo_aurora",
            DEMO_MERCHANT_ID,
            "confirmed",
            "https://auroraheatcool.example",
            "Aurora Heating & Cooling",
            "Local HVAC service for homeowners and property managers who need tune-ups, repairs, and fast scheduling.",
            "home_services",
            "https://auroraheatcool.example/logo.svg",
            "#172033",
            "#2563eb",
            "#f4a62a",
            "Sora",
            "en",
            "America/Detroit",
            "professional",
            "Warm owner voice",
            "Owner-style avatar",
            "Washtenaw County homeowners and property managers",
            json_dumps(
                {
                    "name": "Aurora Heating & Cooling",
                    "description": "Local HVAC service for homeowners and property managers who need tune-ups, repairs, and fast scheduling.",
                    "voiceover": "Warm owner voice",
                    "avatar": "Owner-style avatar",
                }
            ),
            now,
            now,
        ),
    )


def serialize_content_batch(conn, batch_id):
    row = conn.execute("select * from content_batches where id = ?", (batch_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Content batch not found.")
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "campaignId": row["campaign_id"],
        "sourcePrompt": row["source_prompt"],
        "objective": row["objective"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_content_source(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "sourceType": row["source_type"],
        "label": row["label"],
        "url": row["url"],
        "status": row["status"],
        "extracted": json_loads(row["extracted_json"], {}),
        "brief": json_loads(row["brief_json"], {}),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_ai_assistant_reply(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "prompt": row["prompt"],
        "replyText": row["reply_text"],
        "outline": json_loads(row["outline_json"], []),
        "sourcePrompt": row["source_prompt"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def proof_link_for_creative(conn, creative_id):
    row = conn.execute("select * from proof_links where creative_id = ? order by created_at desc limit 1", (creative_id,)).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "kind": row["kind"],
        "code": row["code"],
        "targetUrl": row["target_url"],
        "shortUrl": row["short_url"],
        "qrRef": row["qr_ref"],
        "couponCode": row["coupon_code"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_rendered_media_output(row):
    return {
        "id": row["id"],
        "mediaAssetId": row["media_asset_id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "outputKind": row["output_kind"],
        "format": row["format"],
        "mimeType": row["mime_type"],
        "storageRef": row["storage_ref"],
        "previewDataUrl": row["preview_data_url"],
        "status": row["status"],
        "metadata": json_loads(row["metadata_json"], {}),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def rendered_outputs_for_asset(conn, media_asset_id):
    return [
        serialize_rendered_media_output(row)
        for row in conn.execute(
            "select * from rendered_media_outputs where media_asset_id = ? order by created_at desc, id desc",
            (media_asset_id,),
        )
    ]


def serialize_creative_idea_variant(row):
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "variantLabel": row["variant_label"],
        "hook": row["hook"],
        "caption": row["caption"],
        "cta": row["cta"],
        "score": row["score"],
        "scoreBreakdown": json_loads(row["score_json"], {}),
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_creative_language_variant(row):
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "languageCode": row["language_code"],
        "languageLabel": row["language_label"],
        "localizedTitle": row["localized_title"],
        "localizedCaption": row["localized_caption"],
        "localizedCta": row["localized_cta"],
        "localizedHashtags": json_loads(row["localized_hashtags_json"], []),
        "localizationNotes": row["localization_notes"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_creative_bulk_variant(row):
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "variantLabel": row["variant_label"],
        "hook": row["hook"],
        "caption": row["caption"],
        "visualDirection": row["visual_direction"],
        "format": row["format"],
        "score": row["score"],
        "metadata": json_loads(row["metadata_json"], {}),
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_creative_ugc_package(row):
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "packageLabel": row["package_label"],
        "avatar": json_loads(row["avatar_json"], {}),
        "voiceover": json_loads(row["voiceover_json"], {}),
        "script": json_loads(row["script_json"], {}),
        "scenes": json_loads(row["scenes_json"], []),
        "exportSpec": json_loads(row["export_json"], {}),
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_creator_style_workflow(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "creativeId": row["creative_id"],
        "prompt": row["prompt"],
        "goal": row["goal"],
        "ideas": json_loads(row["ideas_json"], []),
        "selectedIdeaId": row["selected_idea_id"],
        "styleId": row["style_id"],
        "actor": json_loads(row["actor_json"], {}),
        "template": json_loads(row["template_json"], {}),
        "script": json_loads(row["script_json"], {}),
        "publish": json_loads(row["publish_json"], {}),
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def creator_style_workflows_for_workspace(conn, merchant_id=DEMO_MERCHANT_ID):
    return [
        serialize_creator_style_workflow(row)
        for row in conn.execute(
            "select * from creator_style_workflows where merchant_id = ? order by created_at desc, id desc",
            (merchant_id,),
        )
    ]


def idea_variants_for_creative(conn, creative_id):
    return [
        serialize_creative_idea_variant(row)
        for row in conn.execute(
            "select * from creative_idea_variants where creative_id = ? order by score desc, created_at desc, id",
            (creative_id,),
        )
    ]


def bulk_variants_for_creative(conn, creative_id):
    return [
        serialize_creative_bulk_variant(row)
        for row in conn.execute(
            "select * from creative_bulk_variants where creative_id = ? order by score desc, created_at desc, id",
            (creative_id,),
        )
    ]


def ugc_packages_for_creative(conn, creative_id):
    return [
        serialize_creative_ugc_package(row)
        for row in conn.execute(
            "select * from creative_ugc_packages where creative_id = ? order by created_at desc, id desc",
            (creative_id,),
        )
    ]


def language_variants_for_creative(conn, creative_id):
    return [
        serialize_creative_language_variant(row)
        for row in conn.execute(
            "select * from creative_language_variants where creative_id = ? order by created_at desc, language_label",
            (creative_id,),
        )
    ]


def normalize_layer_id(value):
    normalized = "".join(ch if ch.isalnum() else "_" for ch in str(value or "").lower()).strip("_")
    return normalized or "layer"


def layer_label(layer_id):
    return str(layer_id or "layer").replace("_", " ").title()


def default_layer_layout(index):
    return {
        "x": 8,
        "y": 10 + index * 16,
        "width": 84,
        "height": 12,
        "rotation": 0,
        "order": index + 1,
    }


def normalized_layer_controls(metadata):
    existing_controls = metadata.get("layerControls") if isinstance(metadata.get("layerControls"), list) else []
    existing_by_id = {
        normalize_layer_id(control.get("id") or control.get("layerId") or control.get("label")): control
        for control in existing_controls
        if isinstance(control, dict)
    }
    editable_layers = metadata.get("editableLayers") if isinstance(metadata.get("editableLayers"), list) else []
    ordered_ids = [normalize_layer_id(layer) for layer in editable_layers]
    ordered_ids.extend(layer_id for layer_id in existing_by_id if layer_id not in ordered_ids)
    controls = []
    for index, layer_id in enumerate(ordered_ids):
        current = existing_by_id.get(layer_id, {})
        layout = current.get("layout") if isinstance(current.get("layout"), dict) else default_layer_layout(index)
        controls.append(
            {
                "id": layer_id,
                "label": current.get("label") or layer_label(layer_id),
                "value": current.get("value") or "Ready for owner edit",
                "placement": current.get("placement") or "canvas",
                "style": current.get("style") or "brand_safe",
                "status": current.get("status") or "ready",
                "layout": {
                    "x": layout.get("x", 8),
                    "y": layout.get("y", 10 + index * 16),
                    "width": layout.get("width", 84),
                    "height": layout.get("height", 12),
                    "rotation": layout.get("rotation", 0),
                    "order": layout.get("order", index + 1),
                },
                "updatedAt": current.get("updatedAt"),
            }
        )
    return sorted(controls, key=lambda control: (control["layout"]["order"], control["id"]))


def upsert_layer_control(metadata, layer_control, now):
    controls = normalized_layer_controls(metadata)
    layer_id = normalize_layer_id(layer_control.get("id") or layer_control.get("layerId") or layer_control.get("label"))
    label = (layer_control.get("label") or layer_label(layer_id)).strip()
    value = str(layer_control.get("value") or "").strip()[:180] or "Owner-approved layer update"
    updated_control = {
        "id": layer_id,
        "label": label,
        "value": value,
        "placement": str(layer_control.get("placement") or "canvas").strip()[:80],
        "style": str(layer_control.get("style") or "brand_safe").strip()[:80],
        "status": str(layer_control.get("status") or "edited").strip()[:40],
        "updatedAt": now,
    }
    replaced = False
    next_controls = []
    for control in controls:
        if control["id"] == layer_id:
            next_controls.append({**control, **updated_control})
            replaced = True
        else:
            next_controls.append(control)
    if not replaced:
        next_controls.append(updated_control)
    metadata["layerControls"] = next_controls
    metadata["lastLayerEdit"] = f"{label}: {value}"
    edits = metadata.get("structuredLayerEdits") if isinstance(metadata.get("structuredLayerEdits"), list) else []
    edits.append({"layerId": layer_id, "label": label, "value": value, "createdAt": now})
    metadata["structuredLayerEdits"] = edits[-8:]


def placement_layout(placement, current_layout, order):
    layout = dict(current_layout or {})
    placement_key = str(placement or "").strip().lower().replace("_", "-")
    presets = {
        "top-left": {"x": 8, "y": 8, "width": 62, "height": 12},
        "top-center": {"x": 18, "y": 8, "width": 64, "height": 12},
        "center": {"x": 18, "y": 42, "width": 64, "height": 14},
        "bottom-center": {"x": 18, "y": 78, "width": 64, "height": 12},
        "bottom-right": {"x": 34, "y": 78, "width": 58, "height": 12},
    }
    layout.update(presets.get(placement_key, presets["center"]))
    layout["rotation"] = layout.get("rotation", 0)
    layout["order"] = order
    return layout


def apply_layer_layout(metadata, payload, now):
    controls = normalized_layer_controls(metadata)
    layer_id = normalize_layer_id(payload.get("layerId") or payload.get("id") or payload.get("label"))
    if not layer_id:
        raise StoreError(400, "layerId is required.")
    target_index = next((index for index, control in enumerate(controls) if control["id"] == layer_id), -1)
    if target_index < 0:
        raise StoreError(404, "Layer control not found.")
    action = str(payload.get("action") or "move-down").strip().lower()
    if action in {"move-up", "bring-forward"} and target_index > 0:
        controls[target_index - 1], controls[target_index] = controls[target_index], controls[target_index - 1]
        target_index -= 1
    elif action in {"move-down", "send-backward"} and target_index < len(controls) - 1:
        controls[target_index + 1], controls[target_index] = controls[target_index], controls[target_index + 1]
        target_index += 1
    target = controls[target_index]
    placement = str(payload.get("placement") or target.get("placement") or "center").strip()[:80]
    target["placement"] = placement
    target["status"] = "layout_adjusted"
    target["updatedAt"] = now
    for index, control in enumerate(controls):
        order = index + 1
        control["layout"] = placement_layout(
            placement if control["id"] == layer_id else control.get("placement"),
            control.get("layout"),
            order,
        )
    metadata["layerControls"] = controls
    metadata["lastLayerEdit"] = f"{target['label']} layout moved to {placement}"
    edits = metadata.get("layerLayoutEdits") if isinstance(metadata.get("layerLayoutEdits"), list) else []
    edits.append(
        {
            "layerId": layer_id,
            "label": target["label"],
            "action": action,
            "placement": placement,
            "order": target["layout"]["order"],
            "createdAt": now,
        }
    )
    metadata["layerLayoutEdits"] = edits[-8:]
    return target


def layer_control_value(metadata, layer_ids, fallback):
    controls = normalized_layer_controls(metadata)
    wanted = {normalize_layer_id(layer_id) for layer_id in layer_ids}
    for control in controls:
        if control["id"] in wanted and control.get("value") and control["value"] != "Ready for owner edit":
            return str(control["value"])
    return fallback


def safe_hex_color(value, fallback="#2563eb"):
    text = str(value or "").strip()
    if len(text) == 7 and text.startswith("#") and all(ch in "0123456789abcdefABCDEF" for ch in text[1:]):
        return text
    return fallback


def render_preview_svg(asset, creative, metadata):
    ratio = asset["aspect_ratio"]
    width, height = (1080, 1080)
    if ratio == "9:16":
        width, height = (1080, 1920)
    elif ratio == "4:5":
        width, height = (1080, 1350)
    elif ratio == "16:9":
        width, height = (1600, 900)

    title_text = layer_control_value(metadata, ["headline", "hook_text", "title"], creative["title"])
    caption_text = layer_control_value(metadata, ["body_copy", "captions", "checklist"], creative["caption"])
    cta_text = layer_control_value(metadata, ["cta", "phone_cta"], creative["cta"])
    brand_color = safe_hex_color(layer_control_value(metadata, ["brand_color"], "#2563eb"))

    title = html.escape(title_text[:72])
    caption = html.escape(caption_text[:120])
    platform = html.escape(creative["platform"].replace("_", " ").title())
    cta = html.escape(cta_text[:40])
    asset_label = html.escape(asset["format"][:64])
    highlights = []
    for key in ("slides", "scenes", "placements"):
        value = metadata.get(key)
        if isinstance(value, list):
            highlights.extend(str(item) for item in value[:3])
    if not highlights:
        highlights = [asset["prompt"][:90]]
    highlight_svg = "\n".join(
        f'<text x="92" y="{520 + index * 58}" class="body">- {html.escape(item[:88])}</text>'
        for index, item in enumerate(highlights[:3])
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#0f3b57"/>
      <stop offset="54%" stop-color="{brand_color}"/>
      <stop offset="100%" stop-color="#f97316"/>
    </linearGradient>
    <style>
      .eyebrow {{ font: 700 30px sans-serif; letter-spacing: 5px; fill: #dbeafe; text-transform: uppercase; }}
      .title {{ font: 800 62px sans-serif; fill: #ffffff; }}
      .body {{ font: 500 34px sans-serif; fill: #f8fafc; }}
      .cta {{ font: 800 38px sans-serif; fill: #0f172a; }}
      .small {{ font: 600 26px sans-serif; fill: #bfdbfe; }}
    </style>
  </defs>
  <rect width="100%" height="100%" rx="0" fill="url(#bg)"/>
  <rect x="52" y="52" width="{width - 104}" height="{height - 104}" rx="42" fill="rgba(15,23,42,0.30)" stroke="#dbeafe" stroke-width="3"/>
  <text x="92" y="132" class="eyebrow">LocalPilot Render Preview</text>
  <text x="92" y="232" class="title">{title}</text>
  <text x="92" y="312" class="body">{caption}</text>
  <text x="92" y="410" class="small">{platform} · {asset_label} · {ratio}</text>
  {highlight_svg}
  <rect x="92" y="{height - 190}" width="{min(width - 184, 700)}" height="86" rx="43" fill="#f8fafc"/>
  <text x="132" y="{height - 134}" class="cta">{cta}</text>
  <text x="92" y="{height - 64}" class="small">Deterministic demo artifact · replace with renderer/provider in production</text>
</svg>"""


def serialize_creative_media_asset(conn, row):
    metadata = json_loads(row["metadata_json"], {})
    metadata["layerControls"] = normalized_layer_controls(metadata)
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "assetType": row["asset_type"],
        "format": row["format"],
        "aspectRatio": row["aspect_ratio"],
        "storageRef": row["storage_ref"],
        "prompt": row["prompt"],
        "status": row["status"],
        "provider": row["provider"],
        "metadata": metadata,
        "renderedOutputs": rendered_outputs_for_asset(conn, row["id"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def media_assets_for_creative(conn, creative_id):
    assets = [
        serialize_creative_media_asset(conn, row)
        for row in conn.execute(
            "select * from creative_media_assets where creative_id = ? order by created_at, id",
            (creative_id,),
        )
    ]
    if any(isinstance(asset.get("metadata"), dict) and asset["metadata"].get("carouselSlide") for asset in assets):
        assets.sort(
            key=lambda asset: (
                (asset.get("metadata") or {}).get("carouselSlide", {}).get("index", 999),
                asset.get("createdAt") or "",
                asset.get("id") or "",
            )
        )
    return assets


def compose_carousel_slide_payload(brand_row, slide_plan_item, output_row):
    colors = json_loads(brand_row["colors_json"], []) if brand_row else []
    typography = json_loads(brand_row["typography_json"], {}) if brand_row else {}
    preview_ref = output_row["preview_ref"] if output_row is not None else ""
    accent_color = slide_plan_item.get("accentColor") or (colors[1] if len(colors) > 1 else colors[0] if colors else "#172033")
    typography_token = slide_plan_item.get("typographyToken") or typography.get("title") or typography.get("fontFamily") or "brand-title"
    return {
        "headline": slide_plan_item.get("headline") or "",
        "body": slide_plan_item.get("body") or "",
        "ctaLabel": slide_plan_item.get("ctaLabel") or "",
        "imageUrl": preview_ref,
        "logoSlot": CAROUSEL_LOGO_PLACEMENT,
        "thumbnailRender": preview_ref,
        "editorPreview": preview_ref,
        "layout": {
            "presetId": CAROUSEL_PRESET_ID,
            "aspectRatio": CAROUSEL_ASPECT_RATIO,
            "role": slide_plan_item.get("role") or "",
            "accentColor": accent_color,
            "typographyToken": typography_token,
            "copyAlign": slide_plan_item.get("copyAlign") or "left",
            "brandLock": True,
        },
    }


def materialize_carousel_package(conn, merchant_id, job_row, brand_row, slide_plan, output_rows):
    now = utc_now()
    campaign = conn.execute(
        "select * from campaigns where merchant_id = ? order by created_at desc limit 1",
        (merchant_id,),
    ).fetchone()
    source_prompt = ""
    request_payload = json_loads(job_row["request_json"], {})
    if request_payload.get("sourceKind") == "url":
        source_prompt = request_payload.get("sourceUrl") or job_row["prompt"]
    else:
        source_prompt = request_payload.get("sourceText") or job_row["prompt"]

    batch_id = new_id("batch")
    conn.execute(
        "insert into content_batches values (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            batch_id,
            merchant_id,
            campaign["id"] if campaign else None,
            source_prompt[:500],
            "carousel package generation",
            "generated",
            now,
            now,
        ),
    )

    title = slide_plan[0]["headline"] if slide_plan else "Generated carousel"
    caption = " ".join(item.get("body") or item.get("headline") or "" for item in slide_plan)[:1200]
    cta = slide_plan[-1].get("ctaLabel") or "Review and publish"
    proof_hook = slide_plan[2].get("headline") if len(slide_plan) > 2 else title
    creative_id = new_id("creative")
    conn.execute(
        """
        insert into generated_creatives (
          id, batch_id, merchant_id, platform, format, title, caption, hashtags_json,
          cta, proof_hook, schedule_slot, status, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            creative_id,
            batch_id,
            merchant_id,
            "facebook",
            "carousel",
            title[:180],
            caption,
            brand_row["hashtags_json"] if brand_row is not None else json_dumps(["#LocalPilot"]),
            cta[:180],
            proof_hook[:240],
            "Needs scheduling",
            "needs_review",
            now,
            now,
        ),
    )

    slot_id = new_id("slot")
    conn.execute(
        "insert into calendar_slots values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            slot_id,
            creative_id,
            merchant_id,
            "facebook",
            "Needs scheduling",
            "",
            "in_review",
            now,
            now,
        ),
    )
    proof_code = f"CAROUSEL-{creative_id[-6:].upper()}"
    conn.execute(
        "insert into proof_links values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            new_id("proof"),
            creative_id,
            merchant_id,
            "short_link",
            proof_code,
            f"https://localpilot.ai/carousel/{creative_id}",
            f"https://lp.local/carousel/{creative_id}",
            f"localpilot-proof/carousel/{creative_id}.svg",
            None,
            now,
            now,
        ),
    )

    locked_layout = build_carousel_locked_layout(brand_row)
    media_asset_ids = []
    for index, (slide_plan_item, output_row) in enumerate(zip(slide_plan, output_rows), start=1):
        composed_payload = compose_carousel_slide_payload(brand_row, slide_plan_item, output_row)
        asset_id = new_id("creative_asset")
        metadata = {
            "editorMode": CAROUSEL_EDITOR_MODE,
            "lockedLayout": locked_layout,
            "editableLayers": ["headline", "body", "cta", "image"],
            "carouselSlide": {
                "index": index,
                "role": slide_plan_item.get("role") or "",
                "presetId": CAROUSEL_PRESET_ID,
                "brandLock": True,
                "logoPlacement": CAROUSEL_LOGO_PLACEMENT,
                "creativeId": creative_id,
                "mediaAssetId": asset_id,
                "composedPayload": composed_payload,
            },
            "composedPayload": composed_payload,
        }
        conn.execute(
            """
            insert into creative_media_assets (
              id, creative_id, merchant_id, asset_type, format, aspect_ratio, storage_ref,
              prompt, status, provider, metadata_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                creative_id,
                merchant_id,
                "carousel_slide",
                f"Carousel slide {index}",
                CAROUSEL_ASPECT_RATIO,
                output_row["storage_ref"],
                slide_plan_item.get("imagePrompt") or slide_plan_item.get("headline") or job_row["prompt"],
                "ready_preview",
                job_row["provider_key"],
                json_dumps(metadata),
                now,
                now,
            ),
        )
        output_metadata = json_loads(output_row["metadata_json"], {})
        output_metadata.update(
            {
                "editorMode": CAROUSEL_EDITOR_MODE,
                "lockedLayout": locked_layout,
                "carouselSlide": {
                    **metadata["carouselSlide"],
                    "composedPayload": composed_payload,
                },
                "composedPayload": composed_payload,
            }
        )
        conn.execute(
            "update generation_outputs set metadata_json = ?, updated_at = ? where id = ?",
            (json_dumps(output_metadata), now, output_row["id"]),
        )
        media_asset_ids.append(asset_id)

    creative_row = conn.execute("select * from generated_creatives where id = ?", (creative_id,)).fetchone()
    review_link = ensure_review_link_for_creative(conn, creative_row)
    return {
        "creativeId": creative_id,
        "mediaAssetIds": media_asset_ids,
        "calendarSlotId": slot_id,
        "reviewLinkId": review_link["id"] if review_link else "",
        "lockedLayout": locked_layout,
    }


def materialize_video_package(conn, merchant_id, job_row, output_row):
    now = utc_now()
    capability = job_row["capability"]
    video_format = "ugc_video" if capability == "avatar_video" else "short_video"

    batch_id = new_id("batch")
    conn.execute(
        "insert into content_batches values (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            batch_id,
            merchant_id,
            None,
            job_row["prompt"][:500],
            "video generation",
            "generated",
            now,
            now,
        ),
    )

    creative_id = new_id("creative")
    conn.execute(
        """
        insert into generated_creatives (
          id, batch_id, merchant_id, platform, format, title, caption, hashtags_json,
          cta, proof_hook, schedule_slot, status, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            creative_id,
            batch_id,
            merchant_id,
            "facebook",
            video_format,
            job_row["prompt"][:180],
            "",
            "[]",
            "",
            "",
            "Needs scheduling",
            "needs_review",
            now,
            now,
        ),
    )

    slot_id = new_id("slot")
    conn.execute(
        "insert into calendar_slots values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            slot_id,
            creative_id,
            merchant_id,
            "facebook",
            "Needs scheduling",
            "",
            "in_review",
            now,
            now,
        ),
    )

    proof_code = f"SHORTV-{creative_id[-6:].upper()}"
    conn.execute(
        "insert into proof_links values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            new_id("proof"),
            creative_id,
            merchant_id,
            "short_link",
            proof_code,
            f"https://localpilot.ai/video/{creative_id}",
            f"https://lp.local/video/{creative_id}",
            f"localpilot-proof/video/{creative_id}.svg",
            None,
            now,
            now,
        ),
    )

    asset_id = new_id("creative_asset")
    conn.execute(
        """
        insert into creative_media_assets (
          id, creative_id, merchant_id, asset_type, format, aspect_ratio, storage_ref,
          prompt, status, provider, metadata_json, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset_id,
            creative_id,
            merchant_id,
            "video",
            "9:16 short video",
            "9:16",
            output_row["storage_ref"],
            job_row["prompt"],
            "ready_preview",
            job_row["provider_key"],
            "{}",
            now,
            now,
        ),
    )

    output_metadata = json_loads(output_row["metadata_json"], {})
    output_metadata.update({"creativeId": creative_id, "mediaAssetId": asset_id})
    conn.execute(
        "update generation_outputs set metadata_json = ?, updated_at = ? where id = ?",
        (json_dumps(output_metadata), now, output_row["id"]),
    )

    creative_row = conn.execute("select * from generated_creatives where id = ?", (creative_id,)).fetchone()
    ensure_review_link_for_creative(conn, creative_row)
    return {"creativeId": creative_id, "mediaAssetId": asset_id}


def update_creative_media_asset(conn, asset_id, payload):
    row = conn.execute("select * from creative_media_assets where id = ?", (asset_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Creative media asset not found.")
    now = utc_now()
    metadata = json_loads(row["metadata_json"], {})
    layer_edit = (payload.get("layerEdit") or "").strip()
    if layer_edit:
        metadata["lastLayerEdit"] = layer_edit
        edits = metadata.get("layerEdits") if isinstance(metadata.get("layerEdits"), list) else []
        edits.append({"note": layer_edit, "createdAt": now})
        metadata["layerEdits"] = edits[-5:]
    if isinstance(payload.get("layerControl"), dict):
        upsert_layer_control(metadata, payload["layerControl"], now)
    if isinstance(payload.get("metadata"), dict):
        next_metadata = dict(payload["metadata"])
        if metadata.get("editorMode") == CAROUSEL_EDITOR_MODE:
            next_metadata["editorMode"] = metadata.get("editorMode") or CAROUSEL_EDITOR_MODE
            next_metadata["lockedLayout"] = metadata.get("lockedLayout") or {}
            existing_slide = metadata.get("carouselSlide") if isinstance(metadata.get("carouselSlide"), dict) else {}
            next_slide = next_metadata.get("carouselSlide") if isinstance(next_metadata.get("carouselSlide"), dict) else {}
            locked_slide = dict(existing_slide)
            for key in ("index", "role", "presetId", "brandLock", "logoPlacement", "creativeId", "mediaAssetId"):
                if key in locked_slide:
                    next_slide[key] = locked_slide[key]
            existing_composed_payload = (
                metadata.get("composedPayload") if isinstance(metadata.get("composedPayload"), dict) else {}
            )
            if not existing_composed_payload:
                existing_composed_payload = (
                    existing_slide.get("composedPayload")
                    if isinstance(existing_slide.get("composedPayload"), dict)
                    else {}
                )
            incoming_composed_payload = {}
            if isinstance(next_metadata.get("composedPayload"), dict):
                incoming_composed_payload.update(next_metadata.get("composedPayload") or {})
            if isinstance(next_slide.get("composedPayload"), dict):
                incoming_composed_payload.update(next_slide.get("composedPayload") or {})
            composed_payload = dict(existing_composed_payload)
            for key in ("headline", "body", "ctaLabel"):
                if isinstance(incoming_composed_payload.get(key), str):
                    composed_payload[key] = incoming_composed_payload[key]
            next_metadata["composedPayload"] = composed_payload
            next_slide["composedPayload"] = dict(composed_payload)
            next_metadata["carouselSlide"] = next_slide
        metadata.update(next_metadata)
    metadata["layerControls"] = normalized_layer_controls(metadata)
    conn.execute(
        """
        update creative_media_assets
        set prompt = ?, status = ?, metadata_json = ?, updated_at = ?
        where id = ?
        """,
        (
            payload.get("prompt") or row["prompt"],
            payload.get("status") or "edited_preview",
            json_dumps(metadata),
            now,
            asset_id,
        ),
    )
    conn.commit()
    updated = conn.execute("select * from creative_media_assets where id = ?", (asset_id,)).fetchone()
    return {
        "asset": serialize_creative_media_asset(conn, updated),
        "creative": serialize_generated_creative(conn, row["creative_id"]),
        "workspace": get_phase3_workspace(conn),
    }


def update_creative_media_layer_layout(conn, asset_id, payload):
    row = conn.execute("select * from creative_media_assets where id = ?", (asset_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Creative media asset not found.")
    now = utc_now()
    metadata = json_loads(row["metadata_json"], {})
    layer = apply_layer_layout(metadata, payload, now)
    metadata["layerControls"] = normalized_layer_controls(metadata)
    conn.execute(
        """
        update creative_media_assets
        set status = ?, metadata_json = ?, updated_at = ?
        where id = ?
        """,
        (
            "layout_adjusted",
            json_dumps(metadata),
            now,
            asset_id,
        ),
    )
    conn.commit()
    updated = conn.execute("select * from creative_media_assets where id = ?", (asset_id,)).fetchone()
    return {
        "layer": layer,
        "asset": serialize_creative_media_asset(conn, updated),
        "creative": serialize_generated_creative(conn, row["creative_id"]),
        "workspace": get_phase3_workspace(conn),
    }


def create_creative_media_variant(conn, asset_id, payload):
    row = conn.execute("select * from creative_media_assets where id = ?", (asset_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Creative media asset not found.")
    now = utc_now()
    aspect_ratio = (payload.get("aspectRatio") or "9:16").strip()
    variant_label = (payload.get("label") or f"{aspect_ratio} resize").strip()
    metadata = json_loads(row["metadata_json"], {})
    metadata["sourceAssetId"] = row["id"]
    metadata["resizeVariant"] = True
    metadata["resizeTarget"] = aspect_ratio
    metadata["variantLabel"] = variant_label
    metadata["safeZones"] = payload.get("safeZones") or metadata.get("safeZones") or ["platform-safe crop"]
    storage_suffix = aspect_ratio.replace("/", "x").replace(":", "-").replace(" ", "-")
    asset_id_new = new_id("creative_asset")
    conn.execute(
        """
        insert into creative_media_assets (
          id, creative_id, merchant_id, asset_type, format, aspect_ratio, storage_ref,
          prompt, status, provider, metadata_json, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset_id_new,
            row["creative_id"],
            DEMO_MERCHANT_ID,
            f"{row['asset_type']}_variant",
            variant_label,
            aspect_ratio,
            f"localpilot-generated/phase3/{row['creative_id']}/{row['asset_type']}-{storage_suffix}.json",
            payload.get("prompt") or f"Resize {row['format']} into {aspect_ratio} while preserving brand colors, CTA, and proof hook.",
            "ready_preview",
            "localpilot_deterministic_resizer",
            json_dumps(metadata),
            now,
            now,
        ),
    )
    conn.commit()
    new_row = conn.execute("select * from creative_media_assets where id = ?", (asset_id_new,)).fetchone()
    return {
        "asset": serialize_creative_media_asset(conn, new_row),
        "creative": serialize_generated_creative(conn, row["creative_id"]),
        "workspace": get_phase3_workspace(conn),
    }


def render_creative_media_asset(conn, asset_id, payload):
    row = conn.execute("select * from creative_media_assets where id = ?", (asset_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Creative media asset not found.")
    creative = conn.execute("select * from generated_creatives where id = ?", (row["creative_id"],)).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found.")

    now = utc_now()
    metadata = json_loads(row["metadata_json"], {})
    output_id = new_id("rendered_media")
    output_kind = (payload.get("outputKind") or "preview_svg").strip()
    output_format = (payload.get("format") or f"{row['format']} rendered preview").strip()
    svg = render_preview_svg(row, creative, metadata)
    preview_data_url = f"data:image/svg+xml;charset=utf-8,{quote(svg)}"
    output_metadata = {
        "sourceAssetId": row["id"],
        "sourceAssetType": row["asset_type"],
        "sourceProvider": row["provider"],
        "renderMode": "deterministic_demo_preview",
        "productionNextStep": "connect to selected image/video renderer provider",
        "aspectRatio": row["aspect_ratio"],
        "appliedLayerControls": normalized_layer_controls(metadata),
    }
    conn.execute(
        """
        insert into rendered_media_outputs (
          id, media_asset_id, creative_id, merchant_id, output_kind, format, mime_type,
          storage_ref, preview_data_url, status, metadata_json, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            output_id,
            row["id"],
            row["creative_id"],
            row["merchant_id"],
            output_kind,
            output_format,
            "image/svg+xml",
            f"localpilot-rendered/phase3/{row['creative_id']}/{row['id']}/{output_id}.svg",
            preview_data_url,
            "rendered_preview",
            json_dumps(output_metadata),
            now,
            now,
        ),
    )
    conn.execute(
        """
        update creative_media_assets
        set status = ?, updated_at = ?
        where id = ?
        """,
        ("rendered_preview", now, row["id"]),
    )
    conn.commit()
    updated = conn.execute("select * from creative_media_assets where id = ?", (asset_id,)).fetchone()
    output = conn.execute("select * from rendered_media_outputs where id = ?", (output_id,)).fetchone()
    return {
        "output": serialize_rendered_media_output(output),
        "asset": serialize_creative_media_asset(conn, updated),
        "creative": serialize_generated_creative(conn, row["creative_id"]),
        "workspace": get_phase3_workspace(conn),
    }


def serialize_generated_creative(conn, creative_id):
    row = conn.execute("select * from generated_creatives where id = ?", (creative_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Generated creative not found.")
    media_assets = media_assets_for_creative(conn, row["id"])
    carousel_asset = next((asset for asset in media_assets if isinstance(asset.get("metadata"), dict) and asset["metadata"].get("carouselSlide")), None)
    carousel_metadata = carousel_asset["metadata"] if carousel_asset else {}
    composed_preview = ((carousel_metadata.get("composedPayload") or {}).get("thumbnailRender") if carousel_metadata else "")
    return {
        "id": row["id"],
        "batchId": row["batch_id"],
        "merchantId": row["merchant_id"],
        "platform": row["platform"],
        "format": row["format"],
        "title": row["title"],
        "caption": row["caption"],
        "hashtags": json_loads(row["hashtags_json"], []),
        "cta": row["cta"],
        "proofHook": row["proof_hook"],
        "proofLink": proof_link_for_creative(conn, row["id"]),
        "reviewLink": review_link_for_creative(conn, row["id"]),
        "approvalFeedback": feedback_for_creative(conn, row["id"]),
        "reviewNotifications": notifications_for_creative(conn, row["id"]),
        "mediaAssets": media_assets,
        "ideaVariants": idea_variants_for_creative(conn, row["id"]),
        "bulkVariants": bulk_variants_for_creative(conn, row["id"]),
        "ugcVoiceoverPackages": ugc_packages_for_creative(conn, row["id"]),
        "languageVariants": language_variants_for_creative(conn, row["id"]),
        "editorMode": carousel_metadata.get("editorMode") or "",
        "lockedLayout": carousel_metadata.get("lockedLayout") or {},
        "previewDataUrl": composed_preview or "",
        "scheduleSlot": row["schedule_slot"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_calendar_slot(row):
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "platform": row["platform"],
        "slotLabel": row["slot_label"],
        "scheduledFor": row["scheduled_for"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_competitor_source(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "label": row["label"],
        "url": row["url"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_competitor_idea(row):
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "merchantId": row["merchant_id"],
        "theme": row["theme"],
        "hook": row["hook"],
        "timing": row["timing"],
        "hashtags": json_loads(row["hashtags_json"], []),
        "confidence": row["confidence"],
        "createdAt": row["created_at"],
    }


def serialize_creative_template(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "sourceProvider": row["source_provider"],
        "title": row["title"],
        "format": row["format"],
        "aspectRatio": row["aspect_ratio"],
        "category": row["category"],
        "previewRef": row["preview_ref"],
        "layerSchema": json_loads(row["layer_schema_json"], {}),
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_asset_library_item(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "kind": row["kind"],
        "title": row["title"],
        "provider": row["provider"],
        "license": row["license"],
        "tags": json_loads(row["tags_json"], []),
        "storageRef": row["storage_ref"],
        "fitNotes": row["fit_notes"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_imported_template(row):
    return {
        "id": row["id"],
        "templateId": row["template_id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "sourceProvider": row["source_provider"],
        "importRef": row["import_ref"],
        "status": row["status"],
        "metadata": json_loads(row["metadata_json"], {}),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_approval_review_link(row):
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "reviewToken": row["review_token"],
        "reviewUrl": row["review_url"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_approval_feedback(row):
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "reviewLinkId": row["review_link_id"],
        "authorName": row["author_name"],
        "authorRole": row["author_role"],
        "feedbackType": row["feedback_type"],
        "body": row["body"],
        "status": row["status"],
        "createdAt": row["created_at"],
    }


def serialize_review_notification(row):
    return {
        "id": row["id"],
        "reviewLinkId": row["review_link_id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "recipientName": row["recipient_name"],
        "recipientContact": row["recipient_contact"],
        "channel": row["channel"],
        "subject": row["subject"],
        "body": row["body"],
        "status": row["status"],
        "providerRef": row["provider_ref"],
        "sentAt": row["sent_at"],
        "createdAt": row["created_at"],
    }


def review_link_for_creative(conn, creative_id):
    row = conn.execute(
        "select * from approval_review_links where creative_id = ? order by created_at desc limit 1",
        (creative_id,),
    ).fetchone()
    return serialize_approval_review_link(row) if row else None


def feedback_for_creative(conn, creative_id):
    return [
        serialize_approval_feedback(row)
        for row in conn.execute(
            "select * from approval_feedback where creative_id = ? order by created_at desc, id desc",
            (creative_id,),
        )
    ]


def notifications_for_creative(conn, creative_id):
    return [
        serialize_review_notification(row)
        for row in conn.execute(
            "select * from review_notifications where creative_id = ? order by created_at desc, id desc",
            (creative_id,),
        )
    ]


def ensure_review_link_for_creative(conn, creative):
    row = conn.execute(
        "select * from approval_review_links where creative_id = ? order by created_at desc limit 1",
        (creative["id"],),
    ).fetchone()
    if row:
        return row
    now = utc_now()
    token = f"aurora-{creative['platform'].replace('_', '-')}-{creative['id'][-6:]}"
    link_id = new_id("approval_link")
    conn.execute(
        "insert into approval_review_links values (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            link_id,
            creative["id"],
            creative["merchant_id"],
            token,
            review_url_for_token(token),
            "active",
            now,
            now,
        ),
    )
    return conn.execute("select * from approval_review_links where id = ?", (link_id,)).fetchone()


def create_approval_feedback(conn, payload):
    creative_id = (payload.get("creativeId") or "").strip()
    if not creative_id:
        raise StoreError(400, "creativeId is required.")
    creative = conn.execute(
        "select * from generated_creatives where id = ? and merchant_id = ?",
        (creative_id, DEMO_MERCHANT_ID),
    ).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found for approval feedback.")
    feedback_type = (payload.get("feedbackType") or "approval_note").strip()
    allowed_types = {"approval_note", "change_request", "internal_note"}
    if feedback_type not in allowed_types:
        raise StoreError(400, "Unsupported approval feedback type.")
    body = str(payload.get("body") or "").strip()
    if not body:
        raise StoreError(400, "Feedback body is required.")
    body = body[:500]
    author_name = str(payload.get("authorName") or "Karen Li").strip()[:80] or "Karen Li"
    author_role = str(payload.get("authorRole") or "owner").strip()[:40] or "owner"
    status = "open" if feedback_type == "change_request" else "noted"
    link = ensure_review_link_for_creative(conn, creative)
    now = utc_now()
    feedback_id = new_id("approval_feedback")
    conn.execute(
        "insert into approval_feedback values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            feedback_id,
            creative["id"],
            creative["merchant_id"],
            link["id"],
            author_name,
            author_role,
            feedback_type,
            body,
            status,
            now,
        ),
    )
    conn.commit()
    feedback = conn.execute("select * from approval_feedback where id = ?", (feedback_id,)).fetchone()
    return {
        "feedback": serialize_approval_feedback(feedback),
        "reviewLink": serialize_approval_review_link(link),
        "creative": serialize_generated_creative(conn, creative["id"]),
        "workspace": get_phase3_workspace(conn),
    }


def create_review_notification(conn, payload):
    creative_id = (payload.get("creativeId") or "").strip()
    review_link_id = (payload.get("reviewLinkId") or "").strip()
    if review_link_id:
        link = conn.execute("select * from approval_review_links where id = ?", (review_link_id,)).fetchone()
        if link is None:
            raise StoreError(404, "Review link not found for notification.")
        creative = conn.execute("select * from generated_creatives where id = ?", (link["creative_id"],)).fetchone()
    else:
        if not creative_id:
            raise StoreError(400, "creativeId or reviewLinkId is required.")
        creative = conn.execute(
            "select * from generated_creatives where id = ? and merchant_id = ?",
            (creative_id, DEMO_MERCHANT_ID),
        ).fetchone()
        if creative is None:
            raise StoreError(404, "Generated creative not found for review notification.")
        link = ensure_review_link_for_creative(conn, creative)
    if creative is None:
        raise StoreError(404, "Generated creative not found for review notification.")
    recipient_name = str(payload.get("recipientName") or "Karen Li").strip()[:80] or "Karen Li"
    recipient_contact = str(payload.get("recipientContact") or "karen@example.com").strip()[:120] or "karen@example.com"
    channel = str(payload.get("channel") or "email").strip()[:40] or "email"
    now = utc_now()
    subject = str(payload.get("subject") or f"Review requested: {creative['title']}").strip()[:160]
    body = str(
        payload.get("body")
        or f"Please review this LocalPilot {creative['platform'].replace('_', ' ')} post: {link['review_url']}"
    ).strip()[:800]
    notification_id = new_id("review_notification")
    conn.execute(
        "insert into review_notifications values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            notification_id,
            link["id"],
            creative["id"],
            creative["merchant_id"],
            recipient_name,
            recipient_contact,
            channel,
            subject,
            body,
            "sent_demo",
            f"localpilot-outbox/{notification_id}",
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute("select * from review_notifications where id = ?", (notification_id,)).fetchone()
    return {
        "notification": serialize_review_notification(row),
        "reviewLink": serialize_approval_review_link(link),
        "creative": serialize_generated_creative(conn, creative["id"]),
        "workspace": get_phase3_workspace(conn),
    }


def get_review_package(conn, token):
    token = (token or "").strip()
    if not token:
        raise StoreError(400, "Review token is required.")
    link = conn.execute(
        "select * from approval_review_links where review_token = ? and status = ?",
        (token, "active"),
    ).fetchone()
    if link is None:
        raise StoreError(404, "Review link not found.")
    creative = conn.execute("select * from generated_creatives where id = ?", (link["creative_id"],)).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found for review link.")
    brand = conn.execute(
        "select * from brand_kits where merchant_id = ? order by updated_at desc limit 1",
        (creative["merchant_id"],),
    ).fetchone()
    slot = conn.execute(
        "select * from calendar_slots where creative_id = ? order by updated_at desc limit 1",
        (creative["id"],),
    ).fetchone()
    return {
        "status": "ok",
        "reviewLink": serialize_approval_review_link(link),
        "creative": serialize_generated_creative(conn, creative["id"]),
        "brandKit": serialize_brand_kit(brand),
        "calendarSlot": serialize_calendar_slot(slot) if slot else None,
        "feedback": feedback_for_creative(conn, creative["id"]),
        "mode": "public_review_demo",
    }


def create_review_feedback(conn, token, payload):
    package = get_review_package(conn, token)
    creative = package["creative"]
    next_payload = {
        "creativeId": creative["id"],
        "feedbackType": payload.get("feedbackType") or "approval_note",
        "authorName": payload.get("authorName") or "Client reviewer",
        "authorRole": payload.get("authorRole") or "reviewer",
        "body": payload.get("body"),
    }
    result = create_approval_feedback(conn, next_payload)
    return {
        "status": "ok",
        "feedback": result["feedback"],
        "review": get_review_package(conn, token),
    }


def layer_controls_from_template(template):
    schema = json_loads(template["layer_schema_json"], {})
    layers = schema.get("layers") if isinstance(schema.get("layers"), list) else []
    controls = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = normalize_layer_id(layer.get("id") or layer.get("label"))
        controls.append(
            {
                "id": layer_id,
                "label": layer.get("label") or layer_label(layer_id),
                "value": "Ready for template edit",
                "placement": layer.get("placement") or "canvas",
                "style": layer.get("style") or "template_layer",
                "status": "ready",
                "updatedAt": None,
            }
        )
    return controls


def create_template_import(conn, payload):
    now = utc_now()
    creative_id = (payload.get("creativeId") or "").strip()
    if not creative_id:
        latest = conn.execute(
            "select id from generated_creatives where merchant_id = ? order by created_at desc limit 1",
            (DEMO_MERCHANT_ID,),
        ).fetchone()
        creative_id = latest["id"] if latest else ""
    creative = conn.execute("select * from generated_creatives where id = ?", (creative_id,)).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found for template import.")

    template_id = (payload.get("templateId") or "").strip()
    if not template_id:
        first_template = conn.execute(
            "select id from creative_templates where merchant_id = ? order by created_at, id limit 1",
            (DEMO_MERCHANT_ID,),
        ).fetchone()
        template_id = first_template["id"] if first_template else ""
    template = conn.execute("select * from creative_templates where id = ?", (template_id,)).fetchone()
    if template is None:
        raise StoreError(404, "Creative template not found.")

    asset_id = (payload.get("assetLibraryItemId") or "").strip()
    asset = conn.execute("select * from asset_library_items where id = ?", (asset_id,)).fetchone() if asset_id else None
    media_asset = conn.execute(
        "select * from creative_media_assets where creative_id = ? order by created_at, id limit 1",
        (creative_id,),
    ).fetchone()
    if media_asset is None:
        raise StoreError(404, "Creative media asset not found for template import.")

    import_id = new_id("template_import")
    import_ref = f"localpilot-imports/phase3/{creative_id}/{template['id']}.json"
    import_metadata = {
        "templateTitle": template["title"],
        "templateFormat": template["format"],
        "templateCategory": template["category"],
        "assetLibraryItemId": asset["id"] if asset else None,
        "assetTitle": asset["title"] if asset else None,
        "sourceUrl": json_loads(template["layer_schema_json"], {}).get("sourceUrl"),
    }
    conn.execute(
        "insert into imported_templates values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            import_id,
            template["id"],
            creative_id,
            DEMO_MERCHANT_ID,
            template["source_provider"],
            import_ref,
            "applied_demo",
            json_dumps(import_metadata),
            now,
            now,
        ),
    )

    metadata = json_loads(media_asset["metadata_json"], {})
    metadata["templateImport"] = {
        "id": import_id,
        "templateId": template["id"],
        "templateTitle": template["title"],
        "sourceProvider": template["source_provider"],
        "importRef": import_ref,
        "assetLibraryItemId": asset["id"] if asset else None,
        "assetTitle": asset["title"] if asset else None,
        "appliedAt": now,
    }
    metadata["layerControls"] = layer_controls_from_template(template) or normalized_layer_controls(metadata)
    metadata["lastLayerEdit"] = f"Applied {template['source_provider']} template: {template['title']}"
    if asset:
        metadata["premiumAsset"] = {
            "id": asset["id"],
            "title": asset["title"],
            "provider": asset["provider"],
            "storageRef": asset["storage_ref"],
            "license": asset["license"],
        }
    conn.execute(
        """
        update creative_media_assets
        set format = ?, aspect_ratio = ?, prompt = ?, status = ?, provider = ?, metadata_json = ?, updated_at = ?
        where id = ?
        """,
        (
            template["format"],
            template["aspect_ratio"],
            f"Apply {template['source_provider']} template '{template['title']}' to {creative['title']}.",
            "template_applied",
            "localpilot_template_importer",
            json_dumps(metadata),
            now,
            media_asset["id"],
        ),
    )
    conn.commit()
    imported = conn.execute("select * from imported_templates where id = ?", (import_id,)).fetchone()
    updated_asset = conn.execute("select * from creative_media_assets where id = ?", (media_asset["id"],)).fetchone()
    return {
        "importedTemplate": serialize_imported_template(imported),
        "template": serialize_creative_template(template),
        "assetLibraryItem": serialize_asset_library_item(asset) if asset else None,
        "mediaAsset": serialize_creative_media_asset(conn, updated_asset),
        "creative": serialize_generated_creative(conn, creative_id),
        "workspace": get_phase3_workspace(conn),
    }


def competitor_idea_templates(label, url):
    lowered = f"{label} {url}".lower()
    if "restaurant" in lowered or "cafe" in lowered or "menu" in lowered:
        return [
            (
                "Menu proof",
                "Turn one best-selling item into a behind-the-counter proof post.",
                "Tuesday 11:15 AM",
                ["#localfood", "#annarbor", "#menustory"],
                "derived_demo_analysis",
            ),
            (
                "Owner-led offer",
                "Show the owner explaining why this week's special is worth trying now.",
                "Thursday 5:30 PM",
                ["#smallbusiness", "#dinnerideas", "#localowner"],
                "derived_demo_analysis",
            ),
            (
                "Review remix",
                "Convert one customer quote into a carousel with a clear visit CTA.",
                "Saturday 9:30 AM",
                ["#customerlove", "#weekendplans", "#supportlocal"],
                "derived_demo_analysis",
            ),
        ]
    if "salon" in lowered or "spa" in lowered or "beauty" in lowered:
        return [
            (
                "Before-after trust",
                "Use a simple transformation story with consent-safe wording.",
                "Wednesday 7:00 PM",
                ["#localsalon", "#beforeafter", "#selfcare"],
                "derived_demo_analysis",
            ),
            (
                "Appointment urgency",
                "Frame the last two openings as a helpful reminder, not pressure.",
                "Friday 10:30 AM",
                ["#booknow", "#annarborbeauty", "#localservice"],
                "derived_demo_analysis",
            ),
            (
                "Stylist expertise",
                "Let one team member explain the maintenance mistake they see most.",
                "Monday 12:00 PM",
                ["#stylisttips", "#haircare", "#localexpert"],
                "derived_demo_analysis",
            ),
        ]
    return [
        (
            "Format gap",
            f"{label} is likely winning attention with practical tips; answer with a branded checklist post.",
            "Monday 7:30 AM",
            ["#localbusiness", "#servicearea", "#helpfultips"],
            "derived_demo_analysis",
        ),
        (
            "Trust builder",
            "Make a short owner-led explainer that names the local problem and the honest fix.",
            "Wednesday 6:00 PM",
            ["#localservice", "#ownerled", "#communitytrust"],
            "derived_demo_analysis",
        ),
        (
            "Timing opportunity",
            "Post before the busy decision window with one proof hook and one clear CTA.",
            "Friday 10:00 AM",
            ["#smallbusiness", "#localoffer", "#booklocal"],
            "derived_demo_analysis",
        ),
    ]


def create_competitor_source_analysis(conn, payload):
    now = utc_now()
    url = (payload.get("url") or payload.get("sourceUrl") or "").strip()
    if not url:
        raise StoreError(400, "Competitor source URL is required.")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise StoreError(400, "Competitor source URL must start with http:// or https://.")
    label = (payload.get("label") or payload.get("name") or "Competitor source").strip()
    source_id = new_id("competitor_source")
    conn.execute(
        "insert into competitor_sources values (?, ?, ?, ?, ?, ?, ?)",
        (
            source_id,
            DEMO_MERCHANT_ID,
            label,
            url,
            "analyzed_demo",
            now,
            now,
        ),
    )
    idea_ids = []
    for theme, hook, timing, hashtags, confidence in competitor_idea_templates(label, url):
        idea_id = new_id("idea")
        conn.execute(
            "insert into competitor_ideas values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                idea_id,
                source_id,
                DEMO_MERCHANT_ID,
                theme,
                hook,
                timing,
                json_dumps(hashtags),
                confidence,
                now,
            ),
        )
        idea_ids.append(idea_id)
    conn.commit()
    source = serialize_competitor_source(
        conn.execute("select * from competitor_sources where id = ?", (source_id,)).fetchone()
    )
    ideas = [
        serialize_competitor_idea(row)
        for row in conn.execute(
            "select * from competitor_ideas where source_id = ? order by created_at desc",
            (source_id,),
        )
    ]
    return {"source": source, "ideas": ideas, "workspace": get_phase3_workspace(conn)}


def serialize_proof_event(row):
    return {
        "id": row["id"],
        "proofLinkId": row["proof_link_id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "eventType": row["event_type"],
        "label": row["label"],
        "value": row["value"],
        "source": row["source"],
        "createdAt": row["created_at"],
    }


def serialize_performance_snapshot(row):
    return {
        "id": row["id"],
        "creativeId": row["creative_id"],
        "merchantId": row["merchant_id"],
        "platform": row["platform"],
        "impressions": row["impressions"],
        "reach": row["reach"],
        "engagements": row["engagements"],
        "clicks": row["clicks"],
        "leads": row["leads"],
        "spendCents": row["spend_cents"],
        "lowerBoundValueCents": row["lower_bound_value_cents"],
        "confidence": row["confidence"],
        "metrics": json_loads(row["metrics_json"], {}),
        "capturedAt": row["captured_at"],
        "createdAt": row["created_at"],
    }


def serialize_analytics_insight(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "title": row["title"],
        "insight": row["insight"],
        "recommendation": row["recommendation"],
        "confidence": row["confidence"],
        "relatedCreativeId": row["related_creative_id"],
        "createdAt": row["created_at"],
    }


def get_phase3_analytics_summary(conn, merchant_id=DEMO_MERCHANT_ID):
    rows = conn.execute(
        "select * from performance_snapshots where merchant_id = ? order by platform",
        (merchant_id,),
    ).fetchall()
    totals = {
        "impressions": sum(row["impressions"] for row in rows),
        "reach": sum(row["reach"] for row in rows),
        "engagements": sum(row["engagements"] for row in rows),
        "clicks": sum(row["clicks"] for row in rows),
        "leads": sum(row["leads"] for row in rows),
        "spendCents": sum(row["spend_cents"] for row in rows),
        "lowerBoundValueCents": sum(row["lower_bound_value_cents"] for row in rows),
    }
    engagement_rate = round((totals["engagements"] / totals["impressions"]) * 100, 1) if totals["impressions"] else 0
    click_rate = round((totals["clicks"] / totals["impressions"]) * 100, 1) if totals["impressions"] else 0
    lead_rate = round((totals["leads"] / totals["clicks"]) * 100, 1) if totals["clicks"] else 0
    top = max(rows, key=lambda row: row["lower_bound_value_cents"], default=None)
    return {
        "totals": totals,
        "engagementRate": engagement_rate,
        "clickRate": click_rate,
        "leadRate": lead_rate,
        "topPlatform": top["platform"] if top else "",
        "topCreativeId": top["creative_id"] if top else "",
        "attributionMode": "lower_bound_observable_actions",
        "confidence": "mixed",
    }


def get_phase3_usage_summary(conn, merchant_id=DEMO_MERCHANT_ID):
    generated_count = conn.execute(
        "select count(*) from generated_creatives where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    batch_count = conn.execute(
        "select count(*) from content_batches where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    media_asset_count = conn.execute(
        "select count(*) from creative_media_assets where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    competitor_runs = conn.execute(
        "select count(*) from competitor_ideas where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    template_imports = conn.execute(
        "select count(*) from imported_templates where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    asset_library_count = conn.execute(
        "select count(*) from asset_library_items where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    content_source_count = conn.execute(
        "select count(*) from content_sources where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    social_accounts = conn.execute(
        "select count(*) from connected_channels where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    # Predis publicly meters by credits, brands, channels, and competitor runs.
    # This local demo uses deterministic estimates so usage can be shown without billing.
    credit_usage = generated_count * 15 + media_asset_count * 15 + batch_count * 5 + competitor_runs
    return {
        "planName": "Growth Demo",
        "monthlyCredits": 3200,
        "creditsUsed": credit_usage,
        "creditsRemaining": max(3200 - credit_usage, 0),
        "brandsUsed": 1,
        "brandsLimit": 5,
        "socialAccountsUsed": social_accounts,
        "socialAccountsLimit": 10,
        "competitorRunsUsed": competitor_runs,
        "competitorRunsLimit": 60,
        "generatedCreatives": generated_count,
        "mediaAssets": media_asset_count,
        "contentBatches": batch_count,
        "contentSources": content_source_count,
        "templateImports": template_imports,
        "assetLibraryItems": asset_library_count,
    }


def serialize_generation_model(row):
    return {
        "id": row["id"],
        "providerKey": row["provider_key"],
        "modelKey": row["model_key"],
        "capability": row["capability"],
        "displayName": row["display_name"],
        "creditCost": row["credit_cost"],
        "readinessStatus": row["readiness_status"],
        "settingsSchema": json_loads(row["settings_schema_json"], {}),
        "limits": json_loads(row["limits_json"], {}),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_credit_ledger_entry(row):
    return {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "generationJobId": row["generation_job_id"],
        "entryType": row["entry_type"],
        "amountDelta": row["amount_delta"],
        "balanceAfter": row["balance_after"],
        "metadata": safe_diagnostics(json_loads(row["metadata_json"], {})),
        "createdAt": row["created_at"],
    }


def serialize_generation_attempt(row):
    return {
        "id": row["id"],
        "generationJobId": row["generation_job_id"],
        "attemptNumber": row["attempt_number"],
        "status": row["status"],
        "diagnostics": safe_diagnostics(json_loads(row["diagnostics_json"], {})),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def serialize_generation_output(row):
    return {
        "id": row["id"],
        "generationJobId": row["generation_job_id"],
        "outputKind": row["output_kind"],
        "storageRef": row["storage_ref"],
        "previewRef": row["preview_ref"],
        "metadata": safe_diagnostics(json_loads(row["metadata_json"], {})),
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def get_generation_model_row(conn, model_id):
    row = conn.execute("select * from generation_model_catalog where id = ?", (model_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Generation model not found.")
    return row


def list_generation_models(conn):
    return [
        serialize_generation_model(row)
        for row in conn.execute(
            "select * from generation_model_catalog order by capability, credit_cost, display_name, id"
        ).fetchall()
    ]


def get_credit_account_row(conn, merchant_id):
    row = conn.execute("select * from credit_accounts where merchant_id = ?", (merchant_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Credit account not configured.")
    return row


def current_credit_balance(conn, merchant_id):
    account = get_credit_account_row(conn, merchant_id)
    ledger_delta = conn.execute(
        "select coalesce(sum(amount_delta), 0) from credit_ledger where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    return account["monthly_credits"] + ledger_delta


def current_reserved_credits(conn, merchant_id):
    return conn.execute(
        """
        select coalesce(sum(reserved_credits), 0)
        from generation_jobs
        where merchant_id = ? and status in ('queued', 'running')
        """,
        (merchant_id,),
    ).fetchone()[0]


def get_generation_credit_summary(conn, merchant_id):
    account = get_credit_account_row(conn, merchant_id)
    ledger_entries = conn.execute(
        "select count(*) from credit_ledger where merchant_id = ?",
        (merchant_id,),
    ).fetchone()[0]
    return {
        "merchantId": merchant_id,
        "planName": account["plan_name"],
        "monthlyCredits": account["monthly_credits"],
        "availableCredits": current_credit_balance(conn, merchant_id),
        "reservedCredits": current_reserved_credits(conn, merchant_id),
        "ledgerEntries": ledger_entries,
        "createdAt": account["created_at"],
        "updatedAt": account["updated_at"],
    }


def append_credit_ledger_entry(conn, merchant_id, generation_job_id, entry_type, amount_delta, metadata=None):
    balance_after = current_credit_balance(conn, merchant_id) + amount_delta
    row_id = new_id("credit_entry")
    conn.execute(
        """
        insert into credit_ledger (
          id, merchant_id, generation_job_id, entry_type, amount_delta, balance_after, metadata_json, created_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row_id,
            merchant_id,
            generation_job_id,
            entry_type,
            amount_delta,
            balance_after,
            json_dumps(metadata or {}),
            utc_now(),
        ),
    )
    return conn.execute("select * from credit_ledger where id = ?", (row_id,)).fetchone()


def reserve_generation_credits(conn, merchant_id, generation_job_id, amount):
    return append_credit_ledger_entry(
        conn,
        merchant_id,
        generation_job_id,
        "reserve",
        -abs(amount),
        {"reservedCredits": abs(amount)},
    )


def settle_generation_credits(conn, merchant_id, generation_job_id, amount):
    return append_credit_ledger_entry(
        conn,
        merchant_id,
        generation_job_id,
        "settle",
        0,
        {"finalizedCredits": abs(amount)},
    )


def release_generation_credits(conn, merchant_id, generation_job_id, amount):
    return append_credit_ledger_entry(
        conn,
        merchant_id,
        generation_job_id,
        "release",
        abs(amount),
        {"releasedCredits": abs(amount)},
    )


def get_generation_job(conn, merchant_id, job_id):
    row = conn.execute(
        "select * from generation_jobs where id = ? and merchant_id = ?",
        (job_id, merchant_id),
    ).fetchone()
    if row is None:
        raise StoreError(404, "Generation job not found.")
    return row


def get_latest_brand_kit_row(conn, merchant_id):
    return conn.execute(
        "select * from brand_kits where merchant_id = ? order by updated_at desc limit 1",
        (merchant_id,),
    ).fetchone()


def build_carousel_locked_layout(brand_row):
    colors = json_loads(brand_row["colors_json"], []) if brand_row else []
    typography = json_loads(brand_row["typography_json"], {}) if brand_row else {}
    return {
        "slideCount": len(CAROUSEL_SLIDE_ROLES),
        "slideRoles": list(CAROUSEL_SLIDE_ROLES),
        "aspectRatio": CAROUSEL_ASPECT_RATIO,
        "presetId": CAROUSEL_PRESET_ID,
        "logoPlacement": CAROUSEL_LOGO_PLACEMENT,
        "brandLock": True,
        "accentColor": colors[1] if len(colors) > 1 else colors[0] if colors else "#172033",
        "typographyToken": typography.get("title") or typography.get("fontFamily") or "brand-title",
    }


def normalize_carousel_request(conn, merchant_id, payload, prompt, settings):
    from backend.app import website_crawl

    brand_row = get_latest_brand_kit_row(conn, merchant_id)
    if brand_row is None:
        raise StoreError(409, "Save a brand kit before launching carousel generation.")

    source_kind = str(payload.get("sourceKind") or "idea").strip().lower() or "idea"
    if source_kind not in {"idea", "url"}:
        raise StoreError(400, "Carousel sourceKind must be idea or url.")
    source_text = str(payload.get("sourceText") or (prompt if source_kind == "idea" else "")).strip()
    source_url = str(payload.get("sourceUrl") or "").strip()
    if source_kind == "idea" and not source_text:
        raise StoreError(400, "Carousel idea text is required.")
    if source_kind == "url":
        if not source_url:
            raise StoreError(400, "Carousel sourceUrl is required.")
        try:
            source_url = website_crawl._validate_public_url(source_url)
        except website_crawl.CrawlError as exc:
            raise StoreError(400, exc.message) from exc

    normalized_request = {
        "modelId": payload.get("modelId"),
        "workflowType": CAROUSEL_WORKFLOW_TYPE,
        "carouselPresetId": CAROUSEL_PRESET_ID,
        "slideRoles": list(CAROUSEL_SLIDE_ROLES),
        "sourceKind": source_kind,
        "sourceText": source_text,
        "sourceUrl": source_url,
    }
    normalized_settings = dict(settings or {})
    normalized_settings["aspectRatio"] = CAROUSEL_ASPECT_RATIO
    return brand_row, normalized_request, normalized_settings


def build_carousel_job_handoff(outputs, request_payload):
    if request_payload.get("workflowType") != CAROUSEL_WORKFLOW_TYPE:
        return {}
    slide_outputs = []
    for output in outputs:
        metadata = output.get("metadata") or {}
        slide = metadata.get("carouselSlide")
        composed = metadata.get("composedPayload") or (slide or {}).get("composedPayload")
        if not isinstance(slide, dict) or not isinstance(composed, dict):
            continue
        slide_outputs.append(
            {
                "output": output,
                "slide": slide,
                "composed": composed,
            }
        )
    slide_outputs.sort(key=lambda item: item["slide"].get("index", 0))
    if not slide_outputs:
        return {
            "workflowType": CAROUSEL_WORKFLOW_TYPE,
            "carouselPresetId": request_payload.get("carouselPresetId") or CAROUSEL_PRESET_ID,
            "slideRoles": list(request_payload.get("slideRoles") or CAROUSEL_SLIDE_ROLES),
            "sourceKind": request_payload.get("sourceKind") or "idea",
        }
    first_slide = slide_outputs[0]
    return {
        "workflowType": CAROUSEL_WORKFLOW_TYPE,
        "carouselPresetId": request_payload.get("carouselPresetId") or CAROUSEL_PRESET_ID,
        "slideRoles": list(request_payload.get("slideRoles") or CAROUSEL_SLIDE_ROLES),
        "sourceKind": request_payload.get("sourceKind") or "idea",
        "sourcePreview": request_payload.get("sourcePreview") or {},
        "sourceHealth": request_payload.get("sourceHealth") or "",
        "creativeId": first_slide["slide"].get("creativeId") or "",
        "mediaAssetIds": [item["slide"].get("mediaAssetId") for item in slide_outputs if item["slide"].get("mediaAssetId")],
        "slideCompositions": [item["composed"] for item in slide_outputs],
        "thumbnail": first_slide["composed"].get("thumbnailRender") or first_slide["output"].get("previewRef") or "",
    }


def build_video_job_handoff(outputs, request_payload):
    for o in outputs:
        metadata = o.get("metadata")
        if isinstance(metadata, dict) and metadata.get("creativeId"):
            return {"workflowType": "video", "creativeId": metadata["creativeId"]}
    return {}


def serialize_generation_job(conn, row):
    model = get_generation_model_row(conn, row["model_catalog_id"])
    request_payload = safe_diagnostics(json_loads(row["request_json"], {}))
    settings_payload = safe_diagnostics(json_loads(row["settings_json"], {}))
    attempts = [
        serialize_generation_attempt(attempt)
        for attempt in conn.execute(
            "select * from generation_attempts where generation_job_id = ? order by attempt_number, created_at, id",
            (row["id"],),
        ).fetchall()
    ]
    outputs = [
        serialize_generation_output(output)
        for output in conn.execute(
            "select * from generation_outputs where generation_job_id = ? order by created_at, id",
            (row["id"],),
        ).fetchall()
    ]
    payload = {
        "id": row["id"],
        "merchantId": row["merchant_id"],
        "modelId": model["id"],
        "modelDisplayName": model["display_name"],
        "creditCost": model["credit_cost"],
        "model": serialize_generation_model(model),
        "providerKey": row["provider_key"],
        "modelKey": row["model_key"],
        "capability": row["capability"],
        "prompt": row["prompt"],
        "request": request_payload,
        "settings": settings_payload,
        "status": row["status"],
        "reservedCredits": row["reserved_credits"],
        "failureReason": row["failure_reason"],
        "attempts": attempts,
        "outputs": outputs,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }
    payload.update(build_carousel_job_handoff(outputs, request_payload))
    payload.update(build_video_job_handoff(outputs, request_payload))
    return payload


def list_generation_jobs(conn, merchant_id):
    rows = conn.execute(
        "select * from generation_jobs where merchant_id = ? order by updated_at desc, created_at desc, id desc",
        (merchant_id,),
    ).fetchall()
    return [serialize_generation_job(conn, row) for row in rows]


def create_generation_job(conn, merchant_id, payload):
    model_id = (payload.get("modelId") or "").strip()
    prompt = (payload.get("prompt") or "").strip()
    settings = payload.get("settings") or {}
    workflow_type = (payload.get("workflowType") or "").strip().lower()
    if not model_id:
        raise StoreError(400, "modelId is required.")
    if not prompt:
        raise StoreError(400, "Prompt is required.")
    model = get_generation_model_row(conn, model_id)
    if model["readiness_status"] not in {"ready", "preview"}:
        raise StoreError(409, "Selected generation model is not available.")
    if workflow_type == CAROUSEL_WORKFLOW_TYPE:
        model_limits = json_loads(model["limits_json"], {})
        if model["capability"] != "image" or not model_limits.get("supportsCarousel"):
            raise StoreError(409, "Selected generation model does not support carousel generation.")
        _brand_row, normalized_request, settings = normalize_carousel_request(conn, merchant_id, payload, prompt, settings)
    else:
        normalized_request = dict(payload)

    cost = model["credit_cost"]
    if current_credit_balance(conn, merchant_id) < cost:
        raise StoreError(409, "Insufficient generation credits.")

    now = utc_now()
    job_id = new_id("generation_job")
    conn.execute("savepoint generation_admission")
    try:
        conn.execute(
            """
            insert into generation_jobs (
              id, merchant_id, model_catalog_id, provider_key, model_key, capability,
              prompt, request_json, settings_json, status, reserved_credits, failure_reason,
              created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                merchant_id,
                model["id"],
                model["provider_key"],
                model["model_key"],
                model["capability"],
                prompt,
                json_dumps(normalized_request),
                json_dumps(settings),
                "queued",
                cost,
                None,
                now,
                now,
            ),
        )
        conn.execute(
            """
            insert into generation_attempts (
              id, generation_job_id, attempt_number, status, diagnostics_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("generation_attempt"),
                job_id,
                1,
                "queued",
                "{}",
                now,
                now,
            ),
        )
        reservation = reserve_generation_credits(conn, merchant_id, job_id, cost)
        conn.execute("release savepoint generation_admission")
    except Exception:
        conn.execute("rollback to savepoint generation_admission")
        conn.execute("release savepoint generation_admission")
        raise

    conn.commit()
    return {
        "job": serialize_generation_job(conn, get_generation_job(conn, merchant_id, job_id)),
        "reservation": serialize_credit_ledger_entry(reservation),
        "credits": get_generation_credit_summary(conn, merchant_id),
        "model": serialize_generation_model(model),
    }


def get_phase3_workspace(conn, merchant_id=DEMO_MERCHANT_ID):
    brand = conn.execute("select * from brand_kits where merchant_id = ? order by updated_at desc limit 1", (merchant_id,)).fetchone()
    batches = [serialize_content_batch(conn, row["id"]) for row in conn.execute("select * from content_batches where merchant_id = ? order by created_at desc", (merchant_id,))]
    creatives = [
        serialize_generated_creative(conn, row["id"])
        for row in conn.execute("select * from generated_creatives where merchant_id = ? order by created_at desc, platform", (merchant_id,))
    ]
    slots = [
        serialize_calendar_slot(row)
        for row in conn.execute("select * from calendar_slots where merchant_id = ? order by created_at desc, slot_label", (merchant_id,))
    ]
    sources = [
        serialize_competitor_source(row)
        for row in conn.execute("select * from competitor_sources where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    content_sources = [
        serialize_content_source(row)
        for row in conn.execute("select * from content_sources where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    ai_replies = [
        serialize_ai_assistant_reply(row)
        for row in conn.execute("select * from ai_assistant_replies where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    ideas = [
        serialize_competitor_idea(row)
        for row in conn.execute("select * from competitor_ideas where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    events = [
        serialize_proof_event(row)
        for row in conn.execute("select * from proof_events where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    templates = [
        serialize_creative_template(row)
        for row in conn.execute("select * from creative_templates where merchant_id = ? order by created_at, id", (merchant_id,))
    ]
    imported_templates = [
        serialize_imported_template(row)
        for row in conn.execute("select * from imported_templates where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    approval_review_links = [
        serialize_approval_review_link(row)
        for row in conn.execute("select * from approval_review_links where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    approval_feedback = [
        serialize_approval_feedback(row)
        for row in conn.execute("select * from approval_feedback where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    review_notifications = [
        serialize_review_notification(row)
        for row in conn.execute("select * from review_notifications where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    asset_library = [
        serialize_asset_library_item(row)
        for row in conn.execute("select * from asset_library_items where merchant_id = ? order by created_at, id", (merchant_id,))
    ]
    performance_snapshots = [
        serialize_performance_snapshot(row)
        for row in conn.execute("select * from performance_snapshots where merchant_id = ? order by platform", (merchant_id,))
    ]
    analytics_insights = [
        serialize_analytics_insight(row)
        for row in conn.execute("select * from analytics_insights where merchant_id = ? order by created_at desc", (merchant_id,))
    ]
    creator_workflows = creator_style_workflows_for_workspace(conn, merchant_id)
    return {
        "status": "ok",
        "brandKit": serialize_brand_kit(brand),
        "contentBatches": batches,
        "generatedCreatives": creatives,
        "calendarSlots": slots,
        "contentSources": content_sources,
        "aiAssistantReplies": ai_replies,
        "competitorSources": sources,
        "competitorIdeas": ideas,
        "proofEvents": events,
        "creativeTemplates": templates,
        "importedTemplates": imported_templates,
        "approvalReviewLinks": approval_review_links,
        "approvalFeedback": approval_feedback,
        "reviewNotifications": review_notifications,
        "assetLibraryItems": asset_library,
        "performanceSnapshots": performance_snapshots,
        "analyticsInsights": analytics_insights,
        "creatorStyleWorkflows": creator_workflows,
        "creatorStyleOptions": creator_style_options(),
        "analyticsSummary": get_phase3_analytics_summary(conn, merchant_id),
        "usage": get_phase3_usage_summary(conn, merchant_id),
    }


def update_brand_kit(conn, payload):
    brand = conn.execute("select * from brand_kits where merchant_id = ? order by updated_at desc limit 1", (DEMO_MERCHANT_ID,)).fetchone()
    if brand is None:
        raise StoreError(404, "Brand kit not found.")
    now = utc_now()
    current = serialize_brand_kit(brand)
    conn.execute(
        """
        update brand_kits
        set logo_ref = ?, website = ?, social_handle = ?, colors_json = ?, voice_json = ?,
            hashtags_json = ?, typography_json = ?, logos_json = ?, integrations_json = ?,
            approved_terms_json = ?, avoid_terms_json = ?, examples_json = ?, updated_at = ?
        where id = ?
        """,
        (
            payload.get("logoRef") or current["logoRef"],
            payload.get("website") or current["website"],
            payload.get("socialHandle") or current["socialHandle"],
            json_dumps(payload.get("colors") or current["colors"]),
            json_dumps(payload.get("voice") or current["voice"]),
            json_dumps(payload.get("hashtags") or current["hashtags"]),
            json_dumps(payload.get("typography") or current["typography"]),
            json_dumps(payload.get("logos") or current["logos"]),
            json_dumps(payload.get("integrations") or current["integrations"]),
            json_dumps(payload.get("approvedTerms") or current["approvedTerms"]),
            json_dumps(payload.get("avoidTerms") or current["avoidTerms"]),
            json_dumps(payload.get("examples") or current["examples"]),
            now,
            brand["id"],
        ),
    )
    conn.commit()
    return {"brandKit": serialize_brand_kit(conn.execute("select * from brand_kits where id = ?", (brand["id"],)).fetchone())}


def idea_variant_templates(creative, objective):
    platform = creative["platform"].replace("_", " ").title()
    base_caption = creative["caption"]
    return [
        {
            "variantLabel": "High-intent service CTA",
            "hook": f"{platform}: Book the tune-up before the next hot stretch",
            "caption": f"{base_caption} This version leads with the homeowner pain point, then asks for a call today.",
            "cta": "Call today for this week's tune-up window",
            "score": 93,
            "scoreBreakdown": {
                "objectiveFit": 95,
                "localTrust": 91,
                "brandSafety": 96,
                "ctaClarity": 94,
                "rationale": f"Best fit for {objective or 'booking local calls'} because the CTA is direct and time-bound.",
            },
        },
        {
            "variantLabel": "Owner trust builder",
            "hook": f"{platform}: What Aurora checks before peak AC season",
            "caption": f"{base_caption} This version sounds like a practical owner tip and makes the service feel local and credible.",
            "cta": "Ask Aurora what your system needs",
            "score": 88,
            "scoreBreakdown": {
                "objectiveFit": 86,
                "localTrust": 96,
                "brandSafety": 95,
                "ctaClarity": 82,
                "rationale": "Strong trust and brand safety, with a softer conversion ask.",
            },
        },
        {
            "variantLabel": "Neighborhood proof angle",
            "hook": f"{platform}: Ann Arbor homes are booking AC checks early",
            "caption": f"{base_caption} This version adds local momentum and turns proof into an easy decision cue.",
            "cta": "Reserve a local service slot",
            "score": 84,
            "scoreBreakdown": {
                "objectiveFit": 84,
                "localTrust": 89,
                "brandSafety": 92,
                "ctaClarity": 80,
                "rationale": "Good local relevance, but less urgent than the top-scoring service CTA.",
            },
        },
    ]


def bulk_variant_templates(creative, objective):
    platform = creative["platform"].replace("_", " ").title()
    base_caption = creative["caption"]
    title = creative["title"]
    objective_text = objective or "book local calls"
    return [
        {
            "variantLabel": "Owner face reel",
            "hook": f"{platform}: The owner explains why tune-ups matter this week",
            "caption": f"{base_caption} Test an owner-led intro for warmer trust and faster calls.",
            "visualDirection": "Vertical owner-to-camera opening, service truck cutaway, phone CTA end card.",
            "format": "9:16 short video storyboard",
            "score": 94,
            "metadata": {"hookTest": "owner trust", "copyTest": objective_text, "visualTest": "face-led reel"},
        },
        {
            "variantLabel": "Checklist carousel",
            "hook": f"{platform}: 3 checks before the next hot stretch",
            "caption": f"{base_caption} Test a saveable checklist that makes the service feel useful before it sells.",
            "visualDirection": "Three-slide carousel with headline, checklist icons, and final call-to-book card.",
            "format": "4:5 carousel",
            "score": 91,
            "metadata": {"hookTest": "education", "copyTest": "saveable proof", "visualTest": "carousel checklist"},
        },
        {
            "variantLabel": "Bold offer card",
            "hook": title,
            "caption": f"{base_caption} Test the direct offer against softer educational variants.",
            "visualDirection": "Square branded offer card with large headline, badge, phone CTA, and proof hook footer.",
            "format": "1:1 social image",
            "score": 88,
            "metadata": {"hookTest": "direct offer", "copyTest": "fast CTA", "visualTest": "bold card"},
        },
        {
            "variantLabel": "Proof-first post",
            "hook": f"{platform}: Local homeowners are booking early",
            "caption": f"{base_caption} Test local proof and neighborhood momentum without promising exact ROI.",
            "visualDirection": "Before/after service detail crop, small proof badge, local area tag, understated CTA.",
            "format": "Facebook/Google local update",
            "score": 86,
            "metadata": {"hookTest": "local proof", "copyTest": "neighborhood cue", "visualTest": "proof crop"},
        },
        {
            "variantLabel": "Behind-the-scenes",
            "hook": f"{platform}: What Aurora checks on every visit",
            "caption": f"{base_caption} Test practical technician process content for credibility and shares.",
            "visualDirection": "Technician hands, gauges, clean checklist overlay, brand color CTA strip.",
            "format": "16:9 explainer clip",
            "score": 83,
            "metadata": {"hookTest": "process trust", "copyTest": "expert guidance", "visualTest": "service detail"},
        },
    ]


def create_creative_bulk_variations(conn, creative_id, payload):
    creative = conn.execute(
        "select * from generated_creatives where id = ? and merchant_id = ?",
        (creative_id, DEMO_MERCHANT_ID),
    ).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found.")
    now = utc_now()
    objective = (payload.get("objective") or "test hooks, copy, and visuals for local appointment booking").strip()
    requested_count = payload.get("count") or 5
    try:
        count = max(1, min(8, int(requested_count)))
    except (TypeError, ValueError):
        raise StoreError(400, "count must be a number.")
    variant_ids = []
    for template in bulk_variant_templates(creative, objective)[:count]:
        variant_id = new_id("bulk_variant")
        metadata = {
            **template["metadata"],
            "objective": objective,
            "sourceCreativeStatus": creative["status"],
            "predisParity": "bulk hook copy visual variation",
        }
        conn.execute(
            """
            insert into creative_bulk_variants (
              id, creative_id, merchant_id, variant_label, hook, caption,
              visual_direction, format, score, metadata_json, status, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                variant_id,
                creative_id,
                DEMO_MERCHANT_ID,
                template["variantLabel"],
                template["hook"],
                template["caption"],
                template["visualDirection"],
                template["format"],
                template["score"],
                json_dumps(metadata),
                "ready_to_test",
                now,
                now,
            ),
        )
        variant_ids.append(variant_id)
    conn.commit()
    variants = [
        serialize_creative_bulk_variant(row)
        for row in conn.execute(
            "select * from creative_bulk_variants where id in ({}) order by score desc".format(",".join("?" for _ in variant_ids)),
            variant_ids,
        )
    ]
    return {"variants": variants, "creative": serialize_generated_creative(conn, creative_id), "workspace": get_phase3_workspace(conn)}


def ugc_voiceover_package_for_creative(creative, payload):
    package_label = (payload.get("packageLabel") or "Owner explainer UGC package").strip()
    avatar = {
        "type": "local_owner_avatar",
        "ageRange": payload.get("ageRange") or "35-50",
        "genderPresentation": payload.get("genderPresentation") or "any",
        "ethnicity": payload.get("ethnicity") or "diverse local spokesperson",
        "wardrobe": "branded work polo, approachable service-business look",
        "disclosure": "demo storyboard only; production requires owner approval and platform AI disclosure checks",
    }
    voiceover = {
        "tone": "neighborly expert",
        "pace": "clear 10-second hook followed by calm service explanation",
        "language": payload.get("language") or "English",
        "durationSeconds": 24,
        "direction": "friendly local service owner, no exaggerated savings claims",
    }
    script_lines = [
        f"Hook: {creative['title']}",
        "Problem: The next hot stretch is when small AC issues become urgent calls.",
        f"Proof: {creative['proof_hook']}",
        f"CTA: {creative['cta']}",
    ]
    scenes = [
        {
            "secondRange": "0-3",
            "shot": "Avatar opens direct-to-camera with brand color lower-third.",
            "caption": creative["title"],
        },
        {
            "secondRange": "4-10",
            "shot": "B-roll of technician checking vents, filters, and outdoor unit.",
            "caption": "Three checks before the next hot stretch.",
        },
        {
            "secondRange": "11-18",
            "shot": "Owner explains the service promise with a simple checklist overlay.",
            "caption": creative["caption"][:90],
        },
        {
            "secondRange": "19-24",
            "shot": "End card with phone CTA, local service area, and proof hook.",
            "caption": creative["cta"],
        },
    ]
    export_spec = {
        "format": "9:16 UGC short video",
        "resolution": "1080x1920",
        "frameRate": "60fps target",
        "safeZones": ["caption safe zone", "CTA lower-third safe zone", "platform disclosure safe zone"],
        "productionNextStep": "connect to selected video/avatar provider before claiming rendered output",
    }
    return package_label, avatar, voiceover, {"lines": script_lines, "caption": creative["caption"]}, scenes, export_spec


def create_creative_ugc_voiceover_package(conn, creative_id, payload):
    creative = conn.execute(
        "select * from generated_creatives where id = ? and merchant_id = ?",
        (creative_id, DEMO_MERCHANT_ID),
    ).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found.")
    now = utc_now()
    package_label, avatar, voiceover, script, scenes, export_spec = ugc_voiceover_package_for_creative(creative, payload)
    package_id = new_id("ugc_package")
    conn.execute(
        """
        insert into creative_ugc_packages (
          id, creative_id, merchant_id, package_label, avatar_json, voiceover_json,
          script_json, scenes_json, export_json, status, created_at, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            package_id,
            creative_id,
            DEMO_MERCHANT_ID,
            package_label,
            json_dumps(avatar),
            json_dumps(voiceover),
            json_dumps(script),
            json_dumps(scenes),
            json_dumps(export_spec),
            "storyboard_ready",
            now,
            now,
        ),
    )
    conn.commit()
    package = conn.execute("select * from creative_ugc_packages where id = ?", (package_id,)).fetchone()
    return {
        "package": serialize_creative_ugc_package(package),
        "creative": serialize_generated_creative(conn, creative_id),
        "workspace": get_phase3_workspace(conn),
    }


LANGUAGE_PROFILES = {
    "english": {
        "code": "en-US",
        "label": "English",
        "prefix": "Local-first",
        "captionLead": "Neighborhood-ready version:",
        "cta": "Call Aurora to book",
        "hashtags": ["#localbusiness", "#annarbor", "#hvac"],
        "notes": "Keeps the same proof hook in clear English for owner review.",
    },
    "spanish": {
        "code": "es-US",
        "label": "Spanish",
        "prefix": "Vecinos locales",
        "captionLead": "Version en espanol para clientes locales:",
        "cta": "Llame a Aurora para reservar",
        "hashtags": ["#negociolocal", "#annarbor", "#aireacondicionado"],
        "notes": "Localized for Spanish-speaking homeowners while preserving the appointment CTA.",
    },
    "chinese": {
        "code": "zh-CN",
        "label": "Chinese",
        "prefix": "本地安心服务",
        "captionLead": "面向本地住户的中文版本：",
        "cta": "联系 Aurora 预约",
        "hashtags": ["#本地服务", "#安娜堡", "#空调保养"],
        "notes": "Localized for Chinese-speaking local homeowners; not a literal word-for-word translation.",
    },
}


def normalize_language_key(value):
    normalized = str(value or "").strip().lower()
    if normalized in {"en", "en-us", "english"}:
        return "english"
    if normalized in {"es", "es-us", "spanish", "espanol", "español"}:
        return "spanish"
    if normalized in {"zh", "zh-cn", "chinese", "mandarin", "中文"}:
        return "chinese"
    return "english"


def localized_copy_for_creative(creative, language):
    profile = LANGUAGE_PROFILES[normalize_language_key(language)]
    return {
        "languageCode": profile["code"],
        "languageLabel": profile["label"],
        "localizedTitle": f"{profile['prefix']}: {creative['title']}",
        "localizedCaption": f"{profile['captionLead']} {creative['caption']} Proof cue: {creative['proof_hook']}",
        "localizedCta": profile["cta"],
        "localizedHashtags": profile["hashtags"],
        "localizationNotes": profile["notes"],
    }


def create_creative_language_variants(conn, creative_id, payload):
    creative = conn.execute(
        "select * from generated_creatives where id = ? and merchant_id = ?",
        (creative_id, DEMO_MERCHANT_ID),
    ).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found.")
    raw_languages = payload.get("targetLanguages") or payload.get("languages") or ["English", "Spanish", "Chinese"]
    if isinstance(raw_languages, str):
        raw_languages = [raw_languages]
    if not isinstance(raw_languages, list):
        raise StoreError(400, "targetLanguages must be a list.")
    language_keys = []
    for language in raw_languages:
        key = normalize_language_key(language)
        if key not in language_keys:
            language_keys.append(key)
    if not language_keys:
        raise StoreError(400, "At least one target language is required.")
    now = utc_now()
    variant_ids = []
    for language_key in language_keys[:6]:
        localized = localized_copy_for_creative(creative, language_key)
        variant_id = new_id("language_variant")
        conn.execute(
            """
            insert into creative_language_variants (
              id, creative_id, merchant_id, language_code, language_label,
              localized_title, localized_caption, localized_cta,
              localized_hashtags_json, localization_notes, status, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                variant_id,
                creative_id,
                DEMO_MERCHANT_ID,
                localized["languageCode"],
                localized["languageLabel"],
                localized["localizedTitle"],
                localized["localizedCaption"],
                localized["localizedCta"],
                json_dumps(localized["localizedHashtags"]),
                localized["localizationNotes"],
                "localized",
                now,
                now,
            ),
        )
        variant_ids.append(variant_id)
    conn.commit()
    variants = [
        serialize_creative_language_variant(row)
        for row in conn.execute(
            "select * from creative_language_variants where id in ({}) order by language_label".format(",".join("?" for _ in variant_ids)),
            variant_ids,
        )
    ]
    return {"variants": variants, "creative": serialize_generated_creative(conn, creative_id), "workspace": get_phase3_workspace(conn)}


def create_creative_idea_variants(conn, creative_id, payload):
    creative = conn.execute(
        "select * from generated_creatives where id = ? and merchant_id = ?",
        (creative_id, DEMO_MERCHANT_ID),
    ).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found.")
    now = utc_now()
    objective = (payload.get("objective") or "book local calls and appointments").strip()
    variant_ids = []
    for template in idea_variant_templates(creative, objective):
        variant_id = new_id("idea_variant")
        conn.execute(
            """
            insert into creative_idea_variants (
              id, creative_id, merchant_id, variant_label, hook, caption, cta,
              score, score_json, status, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                variant_id,
                creative_id,
                DEMO_MERCHANT_ID,
                template["variantLabel"],
                template["hook"],
                template["caption"],
                template["cta"],
                template["score"],
                json_dumps(template["scoreBreakdown"]),
                "suggested",
                now,
                now,
            ),
        )
        variant_ids.append(variant_id)
    conn.commit()
    variants = [
        serialize_creative_idea_variant(row)
        for row in conn.execute(
            "select * from creative_idea_variants where id in ({}) order by score desc".format(",".join("?" for _ in variant_ids)),
            variant_ids,
        )
    ]
    return {"variants": variants, "creative": serialize_generated_creative(conn, creative_id), "workspace": get_phase3_workspace(conn)}


def apply_creative_idea_variant(conn, variant_id):
    variant = conn.execute(
        "select * from creative_idea_variants where id = ? and merchant_id = ?",
        (variant_id, DEMO_MERCHANT_ID),
    ).fetchone()
    if variant is None:
        raise StoreError(404, "Idea Lab variant not found.")
    creative = conn.execute("select * from generated_creatives where id = ?", (variant["creative_id"],)).fetchone()
    if creative is None:
        raise StoreError(404, "Generated creative not found.")
    now = utc_now()
    conn.execute(
        "update creative_idea_variants set status = ?, updated_at = ? where creative_id = ?",
        ("suggested", now, creative["id"]),
    )
    conn.execute(
        "update creative_idea_variants set status = ?, updated_at = ? where id = ?",
        ("applied", now, variant_id),
    )
    conn.execute(
        """
        update generated_creatives
        set title = ?, caption = ?, cta = ?, status = ?, updated_at = ?
        where id = ?
        """,
        (
            variant["hook"],
            variant["caption"],
            variant["cta"],
            "variant_applied",
            now,
            creative["id"],
        ),
    )
    conn.commit()
    return {
        "variant": serialize_creative_idea_variant(conn.execute("select * from creative_idea_variants where id = ?", (variant_id,)).fetchone()),
        "creative": serialize_generated_creative(conn, creative["id"]),
        "workspace": get_phase3_workspace(conn),
    }


def update_generated_creative(conn, creative_id, payload):
    row = conn.execute("select * from generated_creatives where id = ?", (creative_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Generated creative not found.")
    now = utc_now()
    hashtags = payload.get("hashtags")
    if hashtags is None:
        hashtags_json = row["hashtags_json"]
    elif isinstance(hashtags, list):
        hashtags_json = json_dumps(hashtags)
    else:
        hashtags_json = json_dumps([str(hashtags)])
    conn.execute(
        """
        update generated_creatives
        set title = ?, caption = ?, hashtags_json = ?, cta = ?, proof_hook = ?,
            schedule_slot = ?, status = ?, updated_at = ?
        where id = ?
        """,
        (
            payload.get("title") or row["title"],
            payload.get("caption") or row["caption"],
            hashtags_json,
            payload.get("cta") or row["cta"],
            payload.get("proofHook") or row["proof_hook"],
            payload.get("scheduleSlot") or row["schedule_slot"],
            payload.get("status") or row["status"],
            now,
            creative_id,
        ),
    )
    if payload.get("scheduleSlot"):
        conn.execute(
            "update calendar_slots set slot_label = ?, updated_at = ? where creative_id = ?",
            (payload["scheduleSlot"], now, creative_id),
        )
    conn.commit()
    return {"creative": serialize_generated_creative(conn, creative_id), "workspace": get_phase3_workspace(conn)}


def update_calendar_slot(conn, slot_id, payload):
    row = conn.execute("select * from calendar_slots where id = ?", (slot_id,)).fetchone()
    if row is None:
        raise StoreError(404, "Calendar slot not found.")
    now = utc_now()
    slot_label = payload.get("slotLabel") or row["slot_label"]
    status = payload.get("status") or row["status"]
    scheduled_for = payload.get("scheduledFor")
    if scheduled_for is None:
        scheduled_for = row["scheduled_for"]
    conn.execute(
        """
        update calendar_slots
        set slot_label = ?, scheduled_for = ?, status = ?, updated_at = ?
        where id = ?
        """,
        (slot_label, scheduled_for, status, now, slot_id),
    )
    conn.execute(
        "update generated_creatives set schedule_slot = ?, status = ?, updated_at = ? where id = ?",
        (slot_label, status, now, row["creative_id"]),
    )
    conn.commit()
    return {
        "slot": serialize_calendar_slot(conn.execute("select * from calendar_slots where id = ?", (slot_id,)).fetchone()),
        "creative": serialize_generated_creative(conn, row["creative_id"]),
        "workspace": get_phase3_workspace(conn),
    }


def record_proof_event(conn, payload, commit=True):
    now = utc_now()
    creative_id = payload.get("creativeId")
    proof_link_id = payload.get("proofLinkId")
    if creative_id and not proof_link_id:
        proof = conn.execute("select * from proof_links where creative_id = ? order by created_at desc limit 1", (creative_id,)).fetchone()
        proof_link_id = proof["id"] if proof else None
    if not creative_id and proof_link_id:
        proof = conn.execute("select * from proof_links where id = ?", (proof_link_id,)).fetchone()
        creative_id = proof["creative_id"] if proof else None
    event_type = (payload.get("eventType") or "manual_evidence").strip()
    label = (payload.get("label") or event_type.replace("_", " ").title()).strip()
    try:
        value = int(payload.get("value") or 1)
    except (TypeError, ValueError):
        raise StoreError(400, "Proof event value must be numeric.")
    conn.execute(
        "insert into proof_events values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            new_id("proof_event"),
            proof_link_id,
            creative_id,
            DEMO_MERCHANT_ID,
            event_type,
            label,
            value,
            payload.get("source") or "operator",
            now,
        ),
    )
    if commit:
        conn.commit()
    row = conn.execute("select * from proof_events where created_at = ? order by rowid desc limit 1", (now,)).fetchone()
    return {"event": serialize_proof_event(row), "workspace": get_phase3_workspace(conn)}


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

    tiktok_creator_info = None
    tiktok_confirmations = None
    if version["platform"] == "tiktok":
        tiktok_creator_info = get_tiktok_creator_info(conn, channel["id"], ensure=True)
        tiktok_confirmations = validate_tiktok_confirmations(
            tiktok_creator_info, payload.get("tiktokConfirmations")
        )

    approved_at = utc_now()
    snapshot = build_approval_snapshot(
        draft,
        version,
        media_assets,
        channel,
        row_to_boundary(boundary_row),
        {"name": approver["name"], "email": approver["email"]},
        approved_at=approved_at,
        tiktok_creator_info=tiktok_creator_info,
        tiktok_confirmations=tiktok_confirmations,
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


def should_manual_fallback(error_class):
    normalized = str(error_class or "").strip().lower()
    return bool(normalized) and normalized != "none" and normalized not in MANUAL_FALLBACK_RETRYABLE_CLASSES


def resolve_operator(conn, token, *, allow_localhost=False):
    if not token:
        if not allow_localhost:
            raise StoreError(401, "Operator session is required.")
        token = DEMO_SESSION_ID

    try:
        resolved = sessions.resolve_session(conn, token)
    except sessions.SessionError as exc:
        raise StoreError(401, str(exc)) from exc

    user = conn.execute("select * from users where id = ?", (resolved["user_id"],)).fetchone()
    if user is None or user["merchant_id"] != resolved["merchant_id"]:
        raise StoreError(403, "Operator account not found for this tenant.")
    if user["role"] not in {"owner", "operator"}:
        raise StoreError(403, "Operator access is restricted to owner/operator roles.")

    return {
        "userId": user["id"],
        "merchantId": user["merchant_id"],
        "role": user["role"],
        "name": user["name"],
        "email": user["email"],
    }


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


def mark_publish_job_manual_fallback(conn, job_id, error_class, summary):
    if not should_manual_fallback(error_class):
        return False

    failure_label = str(error_class or "").strip().lower() or "blocked"
    parts = [f"Manual fallback required after {failure_label} failure."]
    if summary:
        parts.append(str(summary).strip())
    attempt_number = conn.execute(
        "select max(attempt_number) from publish_attempts where publish_job_id = ?",
        (job_id,),
    ).fetchone()[0] or next_attempt_number(conn, job_id)
    update_publish_job_status(conn, job_id, "manual_fallback_required")
    append_publish_event(
        conn,
        job_id,
        "manual_fallback_required",
        " ".join(part for part in parts if part),
        "system",
        attempt_number,
    )
    return True


def mark_publish_job_support_path(conn, job_id, note):
    attempt_number = conn.execute(
        "select max(attempt_number) from publish_attempts where publish_job_id = ?",
        (job_id,),
    ).fetchone()[0] or 1
    parts = ["Operator opened a manual support path for this publish job."]
    if note:
        parts.append(str(note).strip())
    append_publish_event(
        conn,
        job_id,
        "manual_support",
        " ".join(part for part in parts if part),
        "operator",
        attempt_number,
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


def record_publish_outcome(conn, job_id, attempt_id, snapshot, provider="fake", provider_result_ref=None):
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
    provider_result_ref = provider_result_ref or f"{provider}:{platform}:{idempotency[-8:]}"
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
            provider,
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


def build_publish_job_evidence(conn, job_id):
    job_row = conn.execute("select * from publish_jobs where id = ?", (job_id,)).fetchone()
    if job_row is None:
        raise StoreError(404, "Publish job not found.")

    job = serialize_debug_publish_job(conn, job_row)
    approval = conn.execute("select * from approvals where id = ?", (job_row["approval_id"],)).fetchone()
    if approval is None:
        raise StoreError(400, "Publish job has no approval snapshot.")
    snapshot = json_loads(approval["snapshot_json"], {})
    latest_attempt = job["attempts"][-1] if job["attempts"] else {}
    diagnostics = safe_diagnostics(latest_attempt.get("diagnostics") or {})

    connected_channel_row = conn.execute(
        "select * from connected_channels where id = ?",
        (approval["connected_channel_id"],),
    ).fetchone()
    connected_channel = (
        serialize_channel_health(conn, connected_channel_row)
        if connected_channel_row is not None
        else safe_diagnostics(snapshot.get("connectedChannelRef") or {})
    )

    required_scopes = []
    if connected_channel_row is not None:
        registry_id = connected_channel_row["channel_registry_id"] or connected_channel_row["platform"]
        registry = conn.execute(
            "select required_scopes_json from channel_registry where id = ?",
            (registry_id,),
        ).fetchone()
        if registry is not None:
            required_scopes = json_loads(registry["required_scopes_json"], [])

    app_review = {
        "requiredScopes": required_scopes,
        "grantedScopesSatisfied": ((diagnostics.get("directPost") or {}).get("checks") or {}).get("requiredScopesGranted"),
        "route": diagnostics.get("route"),
        "requestedRoute": diagnostics.get("requestedRoute"),
        "deliveryMode": diagnostics.get("deliveryMode") or diagnostics.get("result"),
        "directPost": diagnostics.get("directPost"),
        "creatorInfoSnapshot": snapshot.get("creatorInfoSnapshot") or {},
        "tiktokConfirmations": snapshot.get("tiktokConfirmations") or {},
        "terminalErrorClass": debug_error_class(diagnostics),
        "nextRecommendedAction": debug_next_action(diagnostics),
    }

    return safe_diagnostics(
        {
            "job": job,
            "merchant": job["merchant"],
            "connectedChannel": connected_channel,
            "attempts": job["attempts"],
            "events": job["events"],
            "appReview": app_review,
            "exportedAt": utc_now(),
        }
    )


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


def _mime_type_from_url(url):
    lower = url.lower().split("?")[0]
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def patch_draft_media_ref(conn, draft_id, generation_output_id):
    if not generation_output_id:
        raise StoreError(400, "generationOutputId is required.")
    output = conn.execute(
        "select * from generation_outputs where id = ?",
        (generation_output_id,),
    ).fetchone()
    if output is None:
        raise StoreError(404, "Generation output not found.")
    storage_ref = output["storage_ref"]
    if not (storage_ref.startswith("http://") or storage_ref.startswith("https://")):
        raise StoreError(400, "Image URL must be publicly accessible for Facebook publishing.")
    draft = get_draft(conn, draft_id)
    version_id = draft["current_version_id"]
    existing_assets = get_media_assets_for_version(conn, version_id)
    now = utc_now()
    mime_type = _mime_type_from_url(storage_ref)
    if existing_assets:
        existing_row = existing_assets[0]
        conn.execute(
            "update media_assets set storage_ref = ?, kind = ?, storage_mode = ? where id = ?",
            (storage_ref, "image", "url", existing_row["id"]),
        )
    else:
        conn.execute(
            "insert into media_assets values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_id("media"),
                DEMO_MERCHANT_ID,
                version_id,
                "url",
                storage_ref,
                "image",
                mime_type,
                "",
                "",
                now,
            ),
        )
    conn.commit()
    return get_serialized_draft(conn, draft_id)


def upsert_facebook_page_token(conn, merchant_id, connected_channel_id, page_id, ciphertext, credential_fingerprint, expires_at=None, issued_at=None, status="active"):
    now = utc_now()
    existing = conn.execute(
        "select id from facebook_page_tokens where merchant_id = ? and connected_channel_id = ? and page_id = ?",
        (merchant_id, connected_channel_id, str(page_id)),
    ).fetchone()
    if existing:
        conn.execute(
            """update facebook_page_tokens
               set ciphertext = ?, credential_fingerprint = ?, token_expires_at = ?,
                   issued_at = ?, status = ?, updated_at = ?
               where id = ?""",
            (ciphertext, credential_fingerprint, expires_at, issued_at, status, now, existing["id"]),
        )
        return existing["id"]
    row_id = new_id("fpt")
    conn.execute(
        """insert into facebook_page_tokens
           (id, merchant_id, connected_channel_id, page_id, ciphertext, credential_fingerprint,
            token_expires_at, issued_at, status, is_active, created_at, updated_at)
           values (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
        (row_id, merchant_id, connected_channel_id, str(page_id), ciphertext,
         credential_fingerprint, expires_at, issued_at, status, now, now),
    )
    return row_id


def get_facebook_page_token_row(conn, page_id, merchant_id=DEMO_MERCHANT_ID):
    return conn.execute(
        "select * from facebook_page_tokens where page_id = ? and merchant_id = ?",
        (str(page_id), merchant_id),
    ).fetchone()


def list_facebook_page_token_rows(conn, merchant_id=DEMO_MERCHANT_ID):
    return conn.execute(
        "select * from facebook_page_tokens where merchant_id = ? order by page_id",
        (merchant_id,),
    ).fetchall()


def set_active_facebook_page(conn, merchant_id, page_id):
    conn.execute(
        "update facebook_page_tokens set is_active = 0, updated_at = ? where merchant_id = ?",
        (utc_now(), merchant_id),
    )
    conn.execute(
        "update facebook_page_tokens set is_active = 1, updated_at = ? where merchant_id = ? and page_id = ?",
        (utc_now(), merchant_id, str(page_id)),
    )


def mark_facebook_page_reconnect_required(conn, page_id):
    conn.execute(
        "update facebook_page_tokens set status = 'reconnect_required', updated_at = ? where page_id = ?",
        (utc_now(), str(page_id)),
    )


def get_active_facebook_page_row(conn, merchant_id=DEMO_MERCHANT_ID):
    return conn.execute(
        "select * from facebook_page_tokens where merchant_id = ? and is_active = 1",
        (merchant_id,),
    ).fetchone()


def _oauth_session_expires_at(ttl_seconds):
    return (
        datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_oauth_session(conn, provider, session_type, payload, ttl_seconds):
    session_id = new_id("oauth")
    created_at = utc_now()
    expires_at = _oauth_session_expires_at(ttl_seconds)
    conn.execute(
        """insert into oauth_sessions
           (id, provider, session_type, payload_json, created_at, expires_at)
           values (?, ?, ?, ?, ?, ?)""",
        (session_id, provider, session_type, json_dumps(payload or {}), created_at, expires_at),
    )
    logger.info(
        "oauth_session_created provider=%s type=%s session_id=%s expires_at=%s",
        provider,
        session_type,
        session_id,
        expires_at,
    )
    return session_id


def get_oauth_session(conn, session_id, session_type, consume=False):
    row = conn.execute(
        "select * from oauth_sessions where id = ? and session_type = ?",
        (session_id, session_type),
    ).fetchone()
    if row is None:
        raise StoreError(400, "OAuth session not found.")
    if row["expires_at"] <= utc_now():
        conn.execute("delete from oauth_sessions where id = ?", (session_id,))
        raise StoreError(400, "OAuth session expired.")

    payload = json_loads(row["payload_json"], {})
    if consume:
        conn.execute("delete from oauth_sessions where id = ?", (session_id,))
        logger.info(
            "oauth_session_consumed provider=%s type=%s session_id=%s",
            row["provider"],
            row["session_type"],
            session_id,
        )
    else:
        logger.info(
            "oauth_session_loaded provider=%s type=%s session_id=%s",
            row["provider"],
            row["session_type"],
            session_id,
        )
    return payload


def cleanup_expired_oauth_sessions(conn):
    cursor = conn.execute(
        "delete from oauth_sessions where expires_at <= ?",
        (utc_now(),),
    )
    removed = cursor.rowcount or 0
    logger.info("oauth_session_cleanup removed=%s", removed)
    return removed


class StoreError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message
