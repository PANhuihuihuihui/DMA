# LocalPilot AI Publishing Stack Research

**Project:** LocalPilot AI
**Research date:** 2026-06-09
**Scope:** Real publishing foundation for Facebook first, TikTok second, Xiaohongshu deferred unless a compliant official path exists.
**Overall confidence:** MEDIUM-HIGH. TikTok and Postiz findings are from current official/public docs. Meta official docs were partially inaccessible without login, so Facebook details combine visible Meta access limitation, stable Graph API endpoint patterns, secondary current references, and local symbo Meta integration patterns.

## Executive Recommendation

Build LocalPilot v1 around a backend-owned publishing foundation, not browser-local state and not direct client-side platform calls.

Recommended path:

1. Keep the current React/Vite frontend for the merchant workflow.
2. Add a FastAPI backend with PostgreSQL, SQLAlchemy/Alembic, Authlib, httpx, Redis-backed jobs, and object storage for media assets.
3. Model publishing as LocalPilot-owned entities: business, user, connected_account, channel, campaign, post_draft, media_asset, publish_attempt, publish_event.
4. Implement Facebook Page publishing first through official Meta Graph/Page APIs or through a proven engine only after a focused Postiz spike.
5. Implement TikTok second using official Content Posting API upload-to-draft first, direct post after TikTok app audit succeeds.
6. Treat Postiz as a candidate publishing engine behind an adapter boundary, not as the whole LocalPilot product.
7. Treat AutoCLI as research/scraping/browser automation only; do not use it for production publishing.
8. Defer Xiaohongshu direct publishing until an official/partner API path is confirmed. Do not ship cookie, scraping, or browser automation posting.

The important product boundary: LocalPilot owns merchant onboarding, local-business content generation, approval, audit trail, status UX, and ROI metadata. A publishing engine may own OAuth/channel plumbing and platform-specific submission if it proves compliant and reliable.

## Recommended Stack for v1 Publishing Foundation

| Layer | Recommendation | Why |
|---|---|---|
| Frontend | Existing React/Vite app | Lowest-risk path from prototype to real workflow. Keep current UX while replacing localStorage persistence with API calls. |
| Backend API | FastAPI on Python 3.11+ | Matches local symbo patterns, simple OAuth callback handling, good Pydantic schemas, and strong fit for integration-heavy services. |
| Data model | PostgreSQL + SQLAlchemy 2 + Alembic | Needed for merchants, connected accounts, tokens, drafts, publish attempts, and status history. Symbo already uses SQLAlchemy/Alembic. |
| Auth | Backend sessions/JWT plus OAuth provider later | Current fake login must be replaced before real token storage. Do not place social tokens in the browser. |
| Social OAuth | Authlib for OAuth flows; platform SDKs only where useful | Symbo already depends on Authlib. For publishing, use clear HTTP clients unless an SDK materially reduces risk. |
| HTTP/platform calls | httpx/requests wrapper with per-platform adapters | Keep platform contracts testable and isolate Graph/TikTok quirks. Prefer httpx for async-capable service code. |
| Background work | Redis + Celery/RQ/Arq worker | Publishing and media transfer are asynchronous, retryable, and status-driven. Do not block HTTP requests on long media uploads. |
| Media storage | S3/R2-compatible object storage with public/verified delivery URL support | TikTok URL pull and many publishing flows require platform-accessible media URLs; Postiz docs also note platforms reject unprepared external media links. |
| Secrets | Server env/secret manager only | OAuth client secrets, refresh tokens, and page/user tokens must never be stored in localStorage or committed files. |
| Observability | Structured logs, trace IDs, publish_event table, error-code mapping | Publishing failures need merchant-visible recovery plus developer diagnosis. Reuse symbo-style trace/error patterns. |
| Optional engine | Self-hosted Postiz behind `PublishingProvider` adapter | Evaluate before custom wrappers; do not couple LocalPilot domain model to Postiz internals. |

Do not bring over symbo's Airflow/BigQuery analytics stack for v1. It is useful as a pattern for scheduled/retryable integration jobs, but it is too heavy for the first merchant publishing loop.

## Facebook Official API Feasibility

**Verdict:** Feasible for Facebook Pages first. HIGH confidence on overall feasibility; MEDIUM confidence on exact current permission/review mechanics because Meta official docs were not accessible without login from this environment.

Target use case: merchant connects a Facebook Page they administer, reviews a generated post, and publishes to that Page. Do not attempt personal profile publishing.

Likely official flow:

1. Create Meta developer app and configure Facebook Login/OAuth redirect.
2. Request Page-related permissions and complete required review/access verification before non-test merchants can use it.
3. Merchant authorizes LocalPilot and selects/grants Page access.
4. Backend exchanges and stores tokens server-side.
5. Backend obtains and stores Page identity plus Page access token metadata.
6. Backend publishes approved posts through versioned Graph API endpoints.
7. Backend records Graph response ID, status, errors, and retryability.

Likely scopes/permissions for v1:

| Need | Permission/scope | Notes |
|---|---|---|
| List/select merchant Pages | `pages_show_list` | Commonly needed to show Pages the user can grant. |
| Read Page engagement/basic post context | `pages_read_engagement` | Common dependency for Page post management. |
| Create/update/delete Page posts | `pages_manage_posts` | Core publishing permission. Requires review/access for real merchants. |
| Publish Page videos/Reels | `publish_video` and/or video-specific Page access | Treat video/Reels as a later Facebook subphase unless app review confirms requirements. |
| Webhooks/page management | `pages_manage_metadata` | Not required for first text/photo publish unless using webhooks or deeper Page settings. |

Known endpoint patterns:

| Content | Endpoint pattern | v1 stance |
|---|---|---|
| Text/link post | `POST /{page-id}/feed` | First Facebook target. |
| Photo post | `POST /{page-id}/photos` | Include if LocalPilot has image assets ready. |
| Video | `POST /{page-id}/videos` or resumable upload flow | Defer until text/photo works. |
| Reels | `/{page-id}/video_reels` style flow | Defer; more review/moderation complexity. |

Implementation constraints:

- Use explicit Graph API versions, not unversioned calls.
- Expect app review friction. The product must show a real end-to-end flow for reviewer screencasts: connect Page, generate/approve post, publish through LocalPilot, and show result.
- Token storage must be encrypted or otherwise protected server-side. Browser localStorage is unacceptable for OAuth tokens.
- Build a status model that distinguishes `failed_auth`, `failed_permission`, `failed_validation`, `failed_platform`, `published`, and `unknown`.
- Add a manual reconnect path for expired/revoked access.

Meta docs access note: `https://developers.facebook.com/docs/pages-api/posts/` returned "Not Logged In - Please log in to see this page" from this environment. Use an authenticated Meta developer session during implementation to confirm exact 2026 permission names, review requirements, and endpoint versions.

## TikTok Official API Feasibility

**Verdict:** Feasible, but start with upload-to-draft/inbox for v1 and graduate to direct post after app audit. HIGH confidence from official TikTok docs.

TikTok has two relevant official Content Posting API paths:

| Path | Endpoint | Scope | Product fit |
|---|---|---|---|
| Direct video post | `/v2/post/publish/video/init/` | `video.publish` | Best final UX, but unaudited clients are restricted to private visibility until audit succeeds. |
| Video upload to inbox/draft | `/v2/post/publish/inbox/video/init/` | `video.upload` | Best v1 fallback: LocalPilot uploads content, merchant finishes in TikTok after notification. |
| Photo direct/upload | `/v2/post/publish/content/init/` | `video.publish` or `video.upload` | Useful later for photo posts; requires creator info and correct `post_mode`/`media_type`. |
| Status polling | `/v2/post/publish/status/fetch/` | User token | Required to update publish lifecycle. Webhooks may also report final outcome. |

Official constraints to design around:

- Direct Post requires querying creator info before publishing so the app can render TikTok-required UI choices.
- The user must explicitly consent before content is sent to TikTok.
- Unaudited clients' direct-post content is restricted to private viewing mode until TikTok audits the API client.
- Each user access token is limited to 6 init requests per minute.
- Media transfer supports `FILE_UPLOAD` and `PULL_FROM_URL`; URL pull requires a verified domain or URL prefix.
- Status is asynchronous. Processing/moderation can delay final post ID, especially for public posts.
- TikTok requires settings such as privacy level and may require duet/stitch/comment toggles and commercial/AI-generated labels.

Recommended TikTok phase plan:

1. Implement OAuth/token storage and creator info query.
2. Implement upload-to-draft/inbox for video using `video.upload`.
3. Add status polling and publish lifecycle events.
4. Add direct post only after app audit and UX compliance are validated.
5. Add photo support after video flow is stable.

## AutoCLI Assessment

**Verdict:** Not useful as a production publisher. Useful only for research, content discovery, competitive intelligence, or internal automation experiments. MEDIUM-HIGH confidence from GitHub README.

AutoCLI describes itself as a Rust CLI for fetching information from websites, covering Twitter/X, Reddit, YouTube, HackerNews, Bilibili, Zhihu, Xiaohongshu, and many other sites, with browser session reuse and AI-native discovery. That makes it directionally useful for:

- Xiaohongshu trend/research exploration.
- Scraping public competitor/social examples when permitted.
- Internal one-off automation for research.

It is not appropriate for:

- Posting to merchant-owned Facebook/TikTok accounts.
- Storing or using customer platform credentials.
- Bypassing official API limits or unavailable platform APIs.
- Any Xiaohongshu "publishing" path for LocalPilot customers.

Reason: LocalPilot's explicit requirement is compliant official publishing. Browser/session automation is fragile, hard to review with platform policies, and risky for merchant trust.

## Postiz Assessment

**Verdict:** Evaluate seriously as a publishing engine, but wrap it. Do not make LocalPilot a skin over Postiz. HIGH confidence that Postiz is a credible candidate; MEDIUM confidence that it will satisfy LocalPilot's Facebook/TikTok compliance and app-review needs without custom work.

Why Postiz is worth evaluating:

- Public API, CLI, MCP, and Node SDK are documented.
- CLI supports listing integrations, creating posts, drafts, media upload, platform-specific settings, and JSON output.
- Public API supports integrations, OAuth connection flows, posts, uploads, analytics, and platform-specific settings.
- Supported platform settings include Facebook and TikTok. TikTok settings include privacy, duet/stitch/comment toggles, commercial content toggles, and content posting method.
- Self-hosting is supported; the main repo is AGPL-3.0 and uses NextJS, NestJS, Prisma/PostgreSQL, and Temporal.
- The README says hosted service uses official platform-approved OAuth flows and does not scrape social platforms.

Why Postiz needs a spike before adoption:

- LocalPilot still needs its own merchant approval workflow, generated content model, local ROI metadata, and status language.
- Self-hosting means LocalPilot still needs Meta/TikTok developer apps, credentials, callback domains, storage, and operational ownership.
- The AGPL-3.0 license matters if modifying or integrating deeply. A legal/product review is needed before embedding or distributing modified code.
- TikTok publishing through any engine still depends on TikTok app scope approval/audit.
- Postiz's generic scheduler model may not map exactly to LocalPilot's "one local offer -> platform-native approved posts" workflow.

Recommended Postiz spike:

1. Self-host Postiz in a sandbox.
2. Configure a test Meta app and TikTok app.
3. Connect one Facebook Page and one TikTok test account.
4. Use Public API or CLI to create:
   - Facebook text post draft/now post.
   - Facebook photo post.
   - TikTok upload/draft video.
   - TikTok direct post attempt if allowed.
5. Verify returned IDs, status transitions, error payloads, and reconnect behavior.
6. Verify where tokens are stored and whether encryption/rotation meets LocalPilot needs.
7. Decide whether LocalPilot's backend calls Postiz API, invokes CLI, or implements direct adapters.

Preferred integration if it passes: LocalPilot backend -> `PublishingProvider` interface -> Postiz Public API. Avoid shelling out to CLI in production unless API gaps force it; CLI is excellent for spike/dev tooling.

## Reusable Patterns from symbo

The symbo repo should inform LocalPilot's backend shape, but not be copied wholesale.

| Pattern | Source file | Reuse in LocalPilot |
|---|---|---|
| FastAPI app factory, router modules, CORS/session/middleware setup | `/Users/huijie/Documents/symbo/apps/api/symbiosys/main.py` | Use a small version: `app/main.py`, `routers/auth.py`, `routers/publishing.py`, `routers/webhooks.py`, `routers/health.py`. |
| Environment-backed settings with Pydantic | `/Users/huijie/Documents/symbo/apps/api/symbiosys/core/config.py` | Use typed settings for app URL, DB URL, OAuth client IDs/secrets, object storage, queue URL. Do not read secrets in frontend. |
| Request timeout middleware | `/Users/huijie/Documents/symbo/apps/api/symbiosys/middleware/request_timeout.py` | Add timeouts and return traceable 504s. Publishing endpoints should enqueue jobs rather than run long media uploads inline. |
| Rate-limit middleware | `/Users/huijie/Documents/symbo/apps/api/symbiosys/middleware/rate_limiter.py` | Add stricter limits to OAuth callbacks, login, regenerate, and publish approval endpoints. |
| Trace/build/error middleware | `/Users/huijie/Documents/symbo/apps/api/symbiosys/main.py` and middleware directory | Add trace IDs to every publish attempt and platform call. |
| Router-level platform isolation | `/Users/huijie/Documents/symbo/apps/api/apps/meta/router.py`, `/Users/huijie/Documents/symbo/apps/api/apps/tiktok/router.py` | Keep Meta/TikTok code behind distinct adapters/routes. Do not mix platform code into React components. |
| Platform account lookup and per-account params | `/Users/huijie/Documents/symbo/apps/composer/meta_ads_intraday.py`, `/Users/huijie/Documents/symbo/apps/composer/tiktok_ads_intraday.py` | Model connected accounts explicitly and pass account/token/media/settings as structured job params. |
| Retry/timeouts/scheduled integration jobs | `/Users/huijie/Documents/symbo/apps/composer/meta_ads_intraday.py`, `/Users/huijie/Documents/symbo/apps/composer/tiktok_ads_intraday.py` | Use publish jobs with retries, backoff, idempotency keys, and account-scoped limits. |
| YAML/config-driven task expansion | `/Users/huijie/Documents/symbo/apps/composer/custom_conversion_meta.py`, `/Users/huijie/Documents/symbo/apps/composer/custom_conversion_tiktok.py` | Consider config-driven platform capability definitions: max caption length, supported media, settings schema, required scopes. |
| Anomaly/error checks after integration runs | `/Users/huijie/Documents/symbo/apps/composer/meta_ads_intraday.py`, `/Users/huijie/Documents/symbo/apps/composer/tiktok_ads_intraday.py` | Add publish health checks: failure rate by platform, permission failures, stuck publishing jobs, missing external IDs. |
| Pydantic/FastAPI dependency style | `/Users/huijie/Documents/symbo/apps/api/apps/tiktok/router.py` | Use dependency-injected DB/session/current-user and raise domain-specific HTTP errors. |

What not to reuse for v1:

- Airflow DAGs as the publishing runtime. Too heavy for first product slice.
- BigQuery-first analytics. Store LocalPilot publishing events in PostgreSQL first.
- Ad APIs and conversion upload concepts. The current LocalPilot goal is organic publishing, not paid ads.
- Cookie-based TikTok report download patterns. They are not acceptable for customer publishing.

## Proposed Architecture

```text
React/Vite frontend
  -> LocalPilot FastAPI backend
      -> PostgreSQL domain tables
      -> Redis queue / worker
      -> Object storage for media
      -> PublishingProvider interface
          -> PostizProvider (spike candidate)
          -> MetaGraphProvider (fallback/first direct adapter)
          -> TikTokContentPostingProvider (fallback/second direct adapter)
      -> Webhook/status polling handlers
```

Core lifecycle:

1. Merchant logs in.
2. Merchant connects Facebook Page or TikTok account via OAuth.
3. Backend stores connected account metadata and protected tokens.
4. Merchant enters offer/service/promotion.
5. Backend or frontend generates channel-specific drafts.
6. Merchant edits and explicitly approves a draft.
7. Backend creates a publish_attempt and enqueues a job.
8. Worker submits to provider.
9. Worker records external ID, status, error payload, and retry metadata.
10. Frontend shows `draft`, `needs_review`, `approved`, `publishing`, `published`, `failed`, or `retry_needed`.

Minimum database entities:

- `business`
- `user`
- `connected_account`
- `channel`
- `campaign`
- `post_draft`
- `media_asset`
- `publish_attempt`
- `publish_event`
- `oauth_state`

## Open Questions

1. Meta: exact 2026 permission set and access-verification path must be confirmed in an authenticated Meta developer account.
2. Meta: does the first version need photo publishing, or is text/link Page publishing enough for a field-sales proof point?
3. TikTok: can LocalPilot pass `video.publish` audit quickly, or should the public pitch promise "upload to TikTok for final review" first?
4. TikTok: will merchants provide videos, or must LocalPilot generate/render short videos before publishing?
5. Postiz: does self-hosted Postiz store tokens and media in a way LocalPilot can operate securely and legally?
6. Postiz: does AGPL-3.0 constrain the desired deployment/commercial model if LocalPilot modifies or tightly embeds it?
7. Postiz: can it expose enough status/error detail for merchant-facing retry guidance?
8. Xiaohongshu: is there an official partner publishing program available to LocalPilot's target customers? If not, keep it deferred.

## Confidence Assessment

| Area | Confidence | Reason |
|---|---|---|
| Recommended backend stack | HIGH | LocalPilot lacks backend/persistence; symbo provides strong local FastAPI/Postgres/OAuth patterns. |
| Facebook Page publishing feasibility | MEDIUM-HIGH | Stable Graph/Page API pattern, but official docs required login in this environment and exact 2026 review/access details need authenticated confirmation. |
| TikTok Content Posting feasibility | HIGH | Official TikTok docs clearly document direct post, upload, scopes, creator info, status, rate limits, and audit constraints. |
| AutoCLI recommendation | MEDIUM-HIGH | Public README positions it as web information fetching/browser automation, not official publisher infrastructure. |
| Postiz evaluation recommendation | HIGH | Current docs/repo show API/CLI/MCP, Facebook/TikTok support, self-hosting, and platform OAuth posture. Production fit still needs spike. |
| Xiaohongshu deferral | MEDIUM | Strong compliance reasoning; official publishing path was not confirmed in this scope. |

## Sources

- LocalPilot project context: `/Users/huijie/DMA/.planning/PROJECT.md`
- LocalPilot codebase stack: `/Users/huijie/DMA/.planning/codebase/STACK.md`
- LocalPilot integration audit: `/Users/huijie/DMA/.planning/codebase/INTEGRATIONS.md`
- Symbo API README: `/Users/huijie/Documents/symbo/apps/api/README.md`
- Symbo Python/project config: `/Users/huijie/Documents/symbo/pyproject.toml`
- Symbo API dependencies: `/Users/huijie/Documents/symbo/apps/api/requirements.txt`
- Symbo FastAPI app: `/Users/huijie/Documents/symbo/apps/api/symbiosys/main.py`
- Symbo settings: `/Users/huijie/Documents/symbo/apps/api/symbiosys/core/config.py`
- Symbo Meta router: `/Users/huijie/Documents/symbo/apps/api/apps/meta/router.py`
- Symbo TikTok router: `/Users/huijie/Documents/symbo/apps/api/apps/tiktok/router.py`
- Symbo Meta ads intraday DAG: `/Users/huijie/Documents/symbo/apps/composer/meta_ads_intraday.py`
- Symbo TikTok ads intraday DAG: `/Users/huijie/Documents/symbo/apps/composer/tiktok_ads_intraday.py`
- Symbo Meta conversion DAG: `/Users/huijie/Documents/symbo/apps/composer/custom_conversion_meta.py`
- Symbo TikTok conversion DAG: `/Users/huijie/Documents/symbo/apps/composer/custom_conversion_tiktok.py`
- TikTok Direct Post docs: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- TikTok Upload docs: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
- TikTok Photo Post docs: https://developers.tiktok.com/doc/content-posting-api-reference-photo-post
- TikTok Status docs: https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status
- Meta Pages API docs access attempt: https://developers.facebook.com/docs/pages-api/posts/
- AutoCLI GitHub: https://github.com/nashsu/AutoCLI
- Postiz CLI introduction: https://docs.postiz.com/cli/introduction
- Postiz Public API: https://docs.postiz.com/public-api/introduction
- Postiz CLI integrations: https://docs.postiz.com/cli/integrations
- Postiz CLI media upload: https://docs.postiz.com/cli/media-upload
- Postiz app GitHub: https://github.com/gitroomhq/postiz-app
- Postiz Docker Compose GitHub: https://github.com/gitroomhq/postiz-docker-compose
