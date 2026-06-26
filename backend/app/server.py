import argparse
import json
import os
import traceback
from contextlib import closing
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

def _load_env_local():
    env_file = Path(__file__).resolve().parents[2] / ".env.local"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()

_load_env_local()

from backend.app import facebook_oauth, facebook_publisher, fake_publisher, generation_dispatch, google_auth, sessions, store, tiktok_publisher, website_crawl
from backend.app.contracts import serialize_session


DEFAULT_DB_PATH = ".localpilot-dev/backend.sqlite"


class JsonHandler(BaseHTTPRequestHandler):
    db_path = DEFAULT_DB_PATH

    def log_message(self, fmt, *args):
        print(
            f'{self.address_string()} - - [{self.log_date_time_string()}] {fmt % args}',
            flush=True,
        )

    def do_GET(self):
        self.route_request("GET")

    def do_POST(self):
        self.route_request("POST")

    def do_PATCH(self):
        self.route_request("PATCH")

    def route_request(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        try:
            if method == "GET" and path == "/api/v1/health":
                self.send_json({"status": "ok", "service": "localpilot-backend"})
                return
            if method == "GET" and path == "/api/v1/auth":
                self.send_json({"devLoginEnabled": google_auth.dev_login_enabled()})
                return
            if method == "POST" and path == "/api/v1/auth/google":
                body = self.read_json()
                with closing(store.connect(self.db_path)) as conn:
                    if google_auth.dev_login_enabled() and body.get("devLogin"):
                        token = sessions.create_session(conn, store.DEMO_USER_ID, store.DEMO_MERCHANT_ID)
                        session_row = conn.execute("select * from sessions where id = ?", (token,)).fetchone()
                        self.send_json(
                            {"session": serialize_session(session_row)},
                            cookies=[self.set_session_cookie(token)],
                        )
                        return
                    credential = body.get("credential")
                    if not credential:
                        raise store.StoreError(400, "Missing credential.")
                    claims = google_auth.verify_google_id_token(credential)
                    user = google_auth.resolve_or_create_identity(conn, claims)
                    token = sessions.create_session(conn, user["id"], user["merchant_id"])
                    session_row = conn.execute("select * from sessions where id = ?", (token,)).fetchone()
                    self.send_json(
                        {"session": serialize_session(session_row)},
                        cookies=[self.set_session_cookie(token)],
                    )
                return
            if method == "POST" and path == "/api/v1/auth/logout":
                with closing(store.connect(self.db_path)) as conn:
                    token = self._parse_cookie("lp_session")
                    if token:
                        try:
                            sessions.expire_session(conn, token)
                        except Exception:
                            pass
                    self.send_json({"status": "ok"}, cookies=[self.clear_session_cookie()])
                return
            if method == "GET" and path == "/api/v1/auth/session":
                with closing(store.connect(self.db_path)) as conn:
                    token = self._parse_cookie("lp_session")
                    if not token:
                        raise store.StoreError(401, "No session cookie.")
                    try:
                        sessions.resolve_session(conn, token)
                    except sessions.SessionError as exc:
                        raise store.StoreError(401, str(exc)) from exc
                    session_row = conn.execute("select * from sessions where id = ?", (token,)).fetchone()
                    self.send_json({"session": serialize_session(session_row)})
                return
            if method == "GET" and path == "/api/v1/workflow":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.get_workflow(conn))
                return
            if method == "GET" and path == "/api/v1/phase3/workspace":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    self.send_json(store.get_phase3_workspace(conn, merchant_id))
                return
            if method == "GET" and path == "/api/v1/generation/models":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    self.send_json({"merchantId": merchant_id, "models": store.list_generation_models(conn)})
                return
            if method == "GET" and path == "/api/v1/generation/credits":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    self.send_json({"credits": store.get_generation_credit_summary(conn, merchant_id)})
                return
            if method == "GET" and path == "/api/v1/generation/jobs":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    self.send_json({"jobs": store.list_generation_jobs(conn, merchant_id)})
                return
            if method == "POST" and path == "/api/v1/onboarding/crawl":
                body = self.read_json()
                url = (body.get("url") or "").strip()
                if not url:
                    raise store.StoreError(400, "Missing url.")
                warning = None
                profile_data = {"crawl_url": url}
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_authenticated_merchant_id(conn, parsed)
                    try:
                        html_text = website_crawl.fetch_homepage(url)
                        cleaned_text = website_crawl.clean_html_for_llm(html_text)
                        profile_data.update(website_crawl.extract_brand_profile(cleaned_text))
                    except website_crawl.CrawlError as exc:
                        warning = exc.message
                        if isinstance(exc.partial, dict):
                            profile_data.update(exc.partial)
                    row = store.upsert_merchant_profile(conn, merchant_id, profile_data)
                payload = {"profile": store.serialize_merchant_profile(row)}
                if warning:
                    payload["warning"] = warning
                self.send_json(payload, status=201)
                return
            if method == "GET" and path == "/api/v1/onboarding/profile":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_authenticated_merchant_id(conn, parsed)
                    row = store.get_merchant_profile(conn, merchant_id)
                    if row is None:
                        raise store.StoreError(404, "Merchant profile not found.")
                    self.send_json({"profile": store.serialize_merchant_profile(row)})
                return
            if method == "PATCH" and path == "/api/v1/onboarding/profile":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_authenticated_merchant_id(conn, parsed)
                    row = store.update_merchant_profile(conn, merchant_id, self.read_json())
                    self.send_json({"profile": store.serialize_merchant_profile(row)})
                return
            if method == "POST" and path == "/api/v1/onboarding/profile/confirm":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_authenticated_merchant_id(conn, parsed)
                    row = store.confirm_merchant_profile(conn, merchant_id)
                    self.send_json({"profile": store.serialize_merchant_profile(row)})
                return
            if method == "POST" and path == "/api/v1/generation/jobs":
                body = self.read_json()
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    payload = store.create_generation_job(conn, merchant_id, body)
                if body.get("dispatch", True):
                    generation_dispatch.start_async_dispatch(self.db_path, payload["job"]["id"])
                self.send_json(payload, status=201)
                return
            generation_job = self.match_generation_job(path)
            if generation_job and method == "GET" and generation_job["action"] is None:
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    job = store.get_generation_job(conn, merchant_id, generation_job["job_id"])
                    self.send_json({"job": store.serialize_generation_job(conn, job)})
                return
            if generation_job and method == "POST" and generation_job["action"] == "retry":
                body = self.read_json()
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                payload = generation_dispatch.retry_generation_job(
                    self.db_path,
                    merchant_id,
                    generation_job["job_id"],
                    dispatch=body.get("dispatch", True),
                )
                self.send_json(payload, status=201)
                return
            review_route = self.match_review_route(path)
            if review_route and method == "GET":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.get_review_package(conn, review_route["token"]))
                return
            if review_route and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_review_feedback(conn, review_route["token"], self.read_json()), status=201)
                return
            if method == "PATCH" and path == "/api/v1/phase3/brand-kit":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.update_brand_kit(conn, self.read_json()))
                return
            if method == "POST" and path == "/api/v1/phase3/content-batches":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_content_batch(conn, self.read_json()), status=201)
                return
            if method == "POST" and path == "/api/v1/phase3/content-sources":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_content_source_import(conn, self.read_json()), status=201)
                return
            if method == "POST" and path == "/api/v1/phase3/creator-style-video-workflows":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_creator_style_video_workflow(conn, self.read_json()), status=201)
                return
            phase3_creator_style_generate = self.match_phase3_nested_action(
                path,
                "creator-style-video-workflows",
                "generate",
            )
            if phase3_creator_style_generate and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(
                        store.create_creator_style_video(
                            conn,
                            phase3_creator_style_generate["id"],
                            self.read_json(),
                        ),
                        status=201,
                    )
                return
            if method == "POST" and path == "/api/v1/phase3/ai-assistant/replies":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_ai_assistant_reply(conn, self.read_json()), status=201)
                return
            phase3_ai_reply_batch = self.match_phase3_nested_action(path, "ai-assistant/replies", "content-batch")
            if phase3_ai_reply_batch and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_content_batch_from_ai_reply(conn, phase3_ai_reply_batch["id"]), status=201)
                return
            if method == "POST" and path == "/api/v1/phase3/competitor-sources":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_competitor_source_analysis(conn, self.read_json()), status=201)
                return
            if method == "POST" and path == "/api/v1/phase3/template-imports":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_template_import(conn, self.read_json()), status=201)
                return
            if method == "POST" and path == "/api/v1/phase3/approval-feedback":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_approval_feedback(conn, self.read_json()), status=201)
                return
            if method == "POST" and path == "/api/v1/phase3/review-notifications":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_review_notification(conn, self.read_json()), status=201)
                return
            if method == "POST" and path == "/api/v1/phase3/proof-events":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.record_proof_event(conn, self.read_json()), status=201)
                return
            phase3_creative_idea_variants = self.match_phase3_nested_action(path, "creatives", "idea-variants")
            if phase3_creative_idea_variants and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(
                        store.create_creative_idea_variants(
                            conn,
                            phase3_creative_idea_variants["id"],
                            self.read_json(),
                        ),
                        status=201,
                    )
                return
            phase3_creative_language_variants = self.match_phase3_nested_action(path, "creatives", "language-variants")
            if phase3_creative_language_variants and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(
                        store.create_creative_language_variants(
                            conn,
                            phase3_creative_language_variants["id"],
                            self.read_json(),
                        ),
                        status=201,
                    )
                return
            phase3_creative_bulk_variants = self.match_phase3_nested_action(path, "creatives", "bulk-variations")
            if phase3_creative_bulk_variants and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(
                        store.create_creative_bulk_variations(
                            conn,
                            phase3_creative_bulk_variants["id"],
                            self.read_json(),
                        ),
                        status=201,
                    )
                return
            phase3_creative_ugc_package = self.match_phase3_nested_action(path, "creatives", "ugc-voiceover-package")
            if phase3_creative_ugc_package and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(
                        store.create_creative_ugc_voiceover_package(
                            conn,
                            phase3_creative_ugc_package["id"],
                            self.read_json(),
                        ),
                        status=201,
                    )
                return
            phase3_apply_idea_variant = self.match_phase3_nested_action(path, "idea-variants", "apply")
            if phase3_apply_idea_variant and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.apply_creative_idea_variant(conn, phase3_apply_idea_variant["id"]), status=201)
                return
            phase3_creative = self.match_phase3_action(path, "creatives")
            if phase3_creative and method == "PATCH":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.update_generated_creative(conn, phase3_creative["id"], self.read_json()))
                return
            phase3_media_variant = self.match_phase3_nested_action(path, "media-assets", "variants")
            if phase3_media_variant and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.create_creative_media_variant(conn, phase3_media_variant["id"], self.read_json()), status=201)
                return
            phase3_media_layer_layout = self.match_phase3_nested_action(path, "media-assets", "layer-layout")
            if phase3_media_layer_layout and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.update_creative_media_layer_layout(conn, phase3_media_layer_layout["id"], self.read_json()))
                return
            phase3_media_render = self.match_phase3_nested_action(path, "media-assets", "render")
            if phase3_media_render and method == "POST":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.render_creative_media_asset(conn, phase3_media_render["id"], self.read_json()), status=201)
                return
            phase3_media_asset = self.match_phase3_action(path, "media-assets")
            if phase3_media_asset and method == "PATCH":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.update_creative_media_asset(conn, phase3_media_asset["id"], self.read_json()))
                return
            phase3_slot = self.match_phase3_action(path, "calendar-slots")
            if phase3_slot and method == "PATCH":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.update_calendar_slot(conn, phase3_slot["id"], self.read_json()))
                return
            if method == "GET" and path == "/api/v1/debug/publish-jobs":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json({"status": "ok", "publishJobs": store.list_debug_publish_jobs(conn)})
                return
            admin_publish_job = self.match_admin_publish_job(path)
            if method == "GET" and path == "/api/v1/admin/publish-jobs":
                with closing(store.connect(self.db_path)) as conn:
                    self.resolve_operator_context(conn, parsed)
                    self.send_json({"status": "ok", "publishJobs": store.list_debug_publish_jobs(conn)})
                return
            if admin_publish_job and method == "GET" and admin_publish_job["action"] is None:
                with closing(store.connect(self.db_path)) as conn:
                    self.resolve_operator_context(conn, parsed)
                    job = store.get_publish_job(conn, admin_publish_job["job_id"])
                    self.send_json({"status": "ok", "job": store.serialize_debug_publish_job(conn, job)})
                return
            if admin_publish_job and method == "GET" and admin_publish_job["action"] == "evidence":
                with closing(store.connect(self.db_path)) as conn:
                    self.resolve_operator_context(conn, parsed)
                    self.send_json(
                        {"status": "ok", "evidence": store.build_publish_job_evidence(conn, admin_publish_job["job_id"])}
                    )
                return
            if admin_publish_job and method == "POST" and admin_publish_job["action"] == "retry":
                body = self.read_json()
                with closing(store.connect(self.db_path)) as conn:
                    self.resolve_operator_context(conn, parsed)
                    self.retry_publish_job(conn, admin_publish_job["job_id"], body)
                    job = store.get_publish_job(conn, admin_publish_job["job_id"])
                    self.send_json({"status": "ok", "job": store.serialize_debug_publish_job(conn, job)}, status=201)
                return
            if admin_publish_job and method == "POST" and admin_publish_job["action"] == "mark-support":
                body = self.read_json()
                with closing(store.connect(self.db_path)) as conn:
                    self.resolve_operator_context(conn, parsed)
                    store.get_publish_job(conn, admin_publish_job["job_id"])
                    store.mark_publish_job_support_path(conn, admin_publish_job["job_id"], body.get("note"))
                    conn.commit()
                    job = store.get_publish_job(conn, admin_publish_job["job_id"])
                    self.send_json({"status": "ok", "job": store.serialize_debug_publish_job(conn, job)}, status=201)
                return
            if method == "GET" and path == "/api/v1/channels/health":
                query = parse_qs(parsed.query)
                platform = (query.get("platform") or [None])[0]
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    self.send_json(store.get_channel_health(conn, merchant_id, platform=platform))
                return
            channel_action = self.match_channel_action(path)
            if channel_action and method == "POST" and channel_action["action"] == "disconnect":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    self.send_json(
                        store.disconnect_channel(conn, merchant_id, channel_action["channel_id"]),
                        status=201,
                    )
                return
            if channel_action and method == "POST" and channel_action["action"] == "reconnect":
                with closing(store.connect(self.db_path)) as conn:
                    merchant_id = self.resolve_merchant_id(conn, parsed)
                    self.send_json(
                        store.set_channel_health(conn, merchant_id, channel_action["channel_id"], "connected"),
                        status=201,
                    )
                return
            if method == "GET" and path == "/api/v1/tiktok/creator-info":
                query = parse_qs(parsed.query)
                channel_id = (query.get("channelId") or [store.TIKTOK_CHANNEL_ID])[0]
                with closing(store.connect(self.db_path)) as conn:
                    self.resolve_merchant_id(conn, parsed)
                    self.send_json({"creatorInfo": store.get_tiktok_creator_info(conn, channel_id)})
                return
            if method == "GET" and path == "/api/v1/tiktok/media-policy":
                with closing(store.connect(self.db_path)) as conn:
                    self.resolve_merchant_id(conn, parsed)
                    self.send_json({"mediaPolicy": store.strictest_channel_media_policy(conn)})
                return
            if method == "POST" and path == "/api/v1/tiktok/creator-info/refresh":
                with closing(store.connect(self.db_path)) as conn:
                    self.resolve_merchant_id(conn, parsed)
                    body = self.read_json()
                    channel_id = body.get("channelId") or store.TIKTOK_CHANNEL_ID
                    self.send_json({"creatorInfo": store.refresh_tiktok_creator_info(conn, channel_id)}, status=201)
                return
            if method == "GET" and path == "/api/v1/facebook/connection":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(facebook_oauth.connection_status(conn=conn))
                return
            if method == "GET" and path == "/api/v1/facebook/pages":
                query = parse_qs(parsed.query)
                session_id = (query.get("connectSession") or [None])[0]
                self.send_json({"pages": facebook_oauth.list_pages_for_session(session_id)})
                return
            if method == "POST" and path == "/api/v1/facebook/pages/select":
                with closing(store.connect(self.db_path)) as conn:
                    body = self.read_json()
                    self.send_json(facebook_oauth.select_page(conn, body.get("connectSession"), body.get("pageId")), status=201)
                return
            if method == "POST" and path == "/api/v1/facebook/pages/switch":
                with closing(store.connect(self.db_path)) as conn:
                    body = self.read_json()
                    self.send_json(facebook_oauth.switch_active_page(conn, body.get("pageId")))
                return
            if method == "GET" and path == "/api/v1/facebook/oauth/start":
                query = parse_qs(parsed.query)
                self.send_redirect(facebook_oauth.build_login_url(return_url=(query.get("returnTo") or [None])[0]))
                return
            if method == "GET" and path == "/api/v1/facebook/oauth/callback":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_redirect(facebook_oauth.complete_callback(conn, parse_qs(parsed.query)))
                return
            if method == "POST" and path == "/api/v1/campaigns":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json({"campaign": store.create_campaign(conn, self.read_json())}, status=201)
                return
            approval_action = self.match_approval_action(path)
            if approval_action and method == "POST" and approval_action["action"] == "publish":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(fake_publisher.queue_fake_publish(conn, approval_action["approval_id"]), status=201)
                return
            if approval_action and method == "POST" and approval_action["action"] == "publish-facebook":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(
                        facebook_publisher.queue_facebook_publish(
                            conn,
                            approval_action["approval_id"],
                            self.read_json(),
                        ),
                        status=201,
                    )
                return
            if approval_action and method == "POST" and approval_action["action"] == "publish-tiktok":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(
                        tiktok_publisher.queue_tiktok_publish(
                            conn,
                            approval_action["approval_id"],
                            self.read_json(),
                        ),
                        status=201,
                    )
                return
            publish_job = self.match_publish_job(path)
            if publish_job and method == "GET" and publish_job["action"] is None:
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json({"job": store.get_serialized_publish_job(conn, publish_job["job_id"])})
                return
            if publish_job and method == "POST" and publish_job["action"] == "retry":
                body = self.read_json()
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(self.retry_publish_job(conn, publish_job["job_id"], body), status=201)
                return
            draft_action = self.match_draft_action(path)
            if draft_action and method == "PATCH" and draft_action["action"] is None:
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.update_draft(conn, draft_action["draft_id"], self.read_json()))
                return
            if draft_action and method == "POST" and draft_action["action"] == "approve":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.approve_draft(conn, draft_action["draft_id"], self.read_json()), status=201)
                return
            if draft_action and method == "POST" and draft_action["action"] == "media":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.patch_draft_media_ref(conn, draft_action["draft_id"], self.read_json().get("generationOutputId")), status=201)
                return

            self.send_error_json(404, "Route not found.")
        except store.StoreError as exc:
            self.send_error_json(exc.status, exc.message)
        except json.JSONDecodeError:
            self.send_error_json(400, "Request body must be valid JSON.")
        except Exception:
            print(f"[backend] {method} {path} -> 500 unexpected error", flush=True)
            traceback.print_exc()
            self.send_error_json(500, "Unexpected backend error.")

    def match_draft_action(self, path):
        parts = path.split("/")
        if len(parts) == 5 and parts[:4] == ["", "api", "v1", "drafts"]:
            return {"draft_id": parts[4], "action": None}
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "drafts"]:
            return {"draft_id": parts[4], "action": parts[5]}
        return None

    def match_phase3_action(self, path, collection):
        parts = path.split("/")
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "phase3"] and parts[4] == collection:
            return {"id": parts[5]}
        return None

    def match_review_route(self, path):
        parts = path.split("/")
        if len(parts) == 5 and parts[:4] == ["", "api", "v1", "reviews"]:
            return {"token": parts[4]}
        return None

    def match_phase3_nested_action(self, path, collection, action):
        parts = path.split("/")
        if len(parts) == 7 and parts[:4] == ["", "api", "v1", "phase3"] and parts[4] == collection and parts[6] == action:
            return {"id": parts[5], "action": parts[6]}
        if (
            len(parts) == 8
            and parts[:4] == ["", "api", "v1", "phase3"]
            and "/".join(parts[4:6]) == collection
            and parts[7] == action
        ):
            return {"id": parts[6], "action": parts[7]}
        return None

    def match_channel_action(self, path):
        parts = path.split("/")
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "channels"]:
            return {"channel_id": parts[4], "action": parts[5]}
        return None

    def resolve_operator_context(self, conn, parsed):
        token = self.headers.get("X-LocalPilot-Session")
        if not token:
            token = (parse_qs(parsed.query).get("session") or [None])[0]
        return store.resolve_operator(conn, token, allow_localhost=True)

    def _parse_cookie(self, name):
        cookie_header = self.headers.get("Cookie")
        if not cookie_header:
            return None
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith(f"{name}="):
                return part[len(name) + 1:]
        return None

    def set_session_cookie(self, token):
        host = self.headers.get("Host", "")
        secure = "" if "localhost" in host or "127.0.0.1" in host else "; Secure"
        return f"lp_session={token}; HttpOnly; SameSite=Lax; Path=/{secure}"

    def clear_session_cookie(self):
        return "lp_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"

    def resolve_merchant_id(self, conn, parsed):
        token = self._session_token(parsed)
        if not token:
            return store.DEMO_MERCHANT_ID
        try:
            resolved = sessions.resolve_session(conn, token)
        except sessions.SessionError as exc:
            raise store.StoreError(401, str(exc)) from exc
        return resolved["merchant_id"]

    def resolve_authenticated_merchant_id(self, conn, parsed):
        token = self._session_token(parsed)
        if not token:
            raise store.StoreError(401, "Authentication required.")
        try:
            resolved = sessions.resolve_session(conn, token)
        except sessions.SessionError as exc:
            raise store.StoreError(401, str(exc)) from exc
        return resolved["merchant_id"]

    def _session_token(self, parsed):
        token = self._parse_cookie("lp_session")
        if not token:
            token = self.headers.get("X-LocalPilot-Session")
        if not token:
            token = (parse_qs(parsed.query).get("session") or [None])[0]
        return token

    def match_approval_action(self, path):
        parts = path.split("/")
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "approvals"]:
            return {"approval_id": parts[4], "action": parts[5]}
        return None

    def match_publish_job(self, path):
        parts = path.split("/")
        if len(parts) == 5 and parts[:4] == ["", "api", "v1", "publish-jobs"]:
            return {"job_id": parts[4], "action": None}
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "publish-jobs"]:
            return {"job_id": parts[4], "action": parts[5]}
        return None

    def match_generation_job(self, path):
        parts = path.split("/")
        if len(parts) == 6 and parts[:5] == ["", "api", "v1", "generation", "jobs"]:
            return {"job_id": parts[5], "action": None}
        if len(parts) == 7 and parts[:5] == ["", "api", "v1", "generation", "jobs"]:
            return {"job_id": parts[5], "action": parts[6]}
        return None

    def match_admin_publish_job(self, path):
        parts = path.split("/")
        if len(parts) == 6 and parts[:5] == ["", "api", "v1", "admin", "publish-jobs"]:
            return {"job_id": parts[5], "action": None}
        if len(parts) == 7 and parts[:5] == ["", "api", "v1", "admin", "publish-jobs"]:
            return {"job_id": parts[5], "action": parts[6]}
        return None

    def retry_publish_job(self, conn, job_id, body=None):
        body = body or {}
        job_row = conn.execute("select platform from publish_jobs where id = ?", (job_id,)).fetchone()
        if job_row and job_row["platform"] == "facebook":
            return facebook_publisher.retry_facebook_publish(conn, job_id)
        return fake_publisher.retry_fake_publish(
            conn,
            job_id,
            diagnostics_fixture=body.get("diagnosticsFixture"),
        )

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload, status=200, cookies=None):
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for cookie in (cookies or []):
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def send_redirect(self, location, status=302):
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_error_json(self, status, message):
        phrase = HTTPStatus(status).phrase if status in HTTPStatus._value2member_map_ else "Error"
        self.send_json({"error": {"status": status, "message": message, "code": phrase}}, status=status)


def create_app(host="127.0.0.1", port=8787, db_path=DEFAULT_DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    store.ensure_database(db_path)

    class BoundHandler(JsonHandler):
        pass

    BoundHandler.db_path = db_path
    return ThreadingHTTPServer((host, port), BoundHandler)


def run(host="127.0.0.1", port=8787, db_path=DEFAULT_DB_PATH):
    server = create_app(host=host, port=port, db_path=db_path)
    print(
        f"LocalPilot backend listening at http://{host}:{server.server_address[1]} "
        f"(db: {db_path})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run LocalPilot backend API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    run(host=args.host, port=args.port, db_path=args.db)


if __name__ == "__main__":
    main()
