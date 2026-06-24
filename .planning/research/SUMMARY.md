# Milestone v2.0 Research Summary — Generative Engine + Smart Onboarding

**Date:** 2026-06-24
**Scope:** NEW capabilities for v2.0 only (generation engine, website-crawl onboarding, Google login, credit metering). Builds on the v1.0 backend (sessions/auth, connected channels, publish lifecycle, brand kit, Phase 3 creative workflow).

## 1. Generative model providers (image + video)

**Recommendation: build a provider-agnostic abstraction and start on an aggregator (fal.ai) so model choice is a config/string change, not a code change.** ([fal vs Replicate 2026](https://www.teamday.ai/blog/ai-image-video-api-providers-comparison-2026), [AI video API pricing 2026](https://devtk.ai/en/blog/ai-video-generation-pricing-2026/))

- **Aggregators (single API key, pay-per-use, async queue):**
  - **fal.ai** — broadest coverage (400+ image, 450+ video models), lowest prices, fast inference; HTTP API + SDKs, queue + webhook/`onQueueUpdate`. ([fal video API](https://fal.ai/docs/model-api-reference/video-generation-api/overview))
  - **Replicate** — similar aggregator, per-prediction pricing.
- **Direct providers:** Google **Vertex/Gemini** (Nano Banana Pro + Imagen 4 image, Veo 3.1 video), **OpenAI** (GPT Image; **Sora 2 API discontinued Mar 2026**), ByteDance **ModelArk** (Seedream image, Seedance 2.0 video).
- **Indicative pricing** (verify at build): images — Flux 2 Pro ~$0.05/img, SDXL ~$0.003/img, Nano Banana Pro (Gemini); video (per second) — Kling 3.0 Pro ~$0.09, Seedance 2.0 Fast ~$0.04, Veo 3.1 Lite ~$0.05, Veo 3.1 + audio ~$0.20. ([pricing](https://devtk.ai/en/blog/ai-video-generation-pricing-2026/))
- **Architecture implication:** This validates v2.0's `GenerationProvider` contract — route by `{provider, model_id}`, normalize an async job lifecycle (`queued → running → succeeded/failed` + result URL), keep all provider keys server-side. This mirrors the Phase 2 "publishing engine reuse" decision pattern.

## 2. Website-crawl → brand/customer profile (onboarding)

**Recommendation: use a crawl/extract API (Firecrawl) with schema-based extraction + its `branding` format.** ([Firecrawl scrape](https://docs.firecrawl.dev/features/scrape), [lead enrichment](https://docs.firecrawl.dev/use-cases/lead-enrichment))

- **Firecrawl `/scrape`** returns markdown/JSON; **JSON mode** takes a schema or prompt and returns structured company info (name, mission, description, products). ([llm-extract](http://docs.firecrawl.dev/features/llm-extract))
- **`branding` format** extracts a `BrandingProfile`: colors, fonts/typography, logo URL, color scheme — directly seeds the LocalPilot brand kit. **`product` format** extracts product title/price/variants.
- Maps exactly to Predis "Fetch details from website" → Business identity + Style + Content settings.
- **Compliance/security:** fetch public info only (matches Predis's own copy), store no site credentials, treat extracted content as untrusted input (sanitize before display/use). Open-source self-host option exists if we want to avoid a vendor.

## 3. Google login

**Recommendation: Sign in with Google (button/One Tap) → POST ID token to backend over HTTPS → verify with `google-auth` `verify_oauth2_token`.** ([Google backend auth](https://developers.google.com/identity/sign-in/web/backend-auth), [best practices](https://developers.google.com/identity/siwg/best-practices))

- Backend MUST verify: signature (Google public keys, cached), `aud` == our client ID, `iss` ∈ {accounts.google.com, https://accounts.google.com}, `exp` not passed. **Never trust plain client-sent user IDs.**
- Use the **`sub` claim** as the permanent user key (not email — emails change); store `sub` on the user, link to merchant, issue a LocalPilot session.
- **Integration:** extends the Phase 5 `sessions` table and `resolve_session` — add a Google identity → user/merchant resolution path, then reuse the existing session issuance. Python: `from google.oauth2 import id_token`.

## 4. Pitfalls to design around

- **Cost runaway** — video credits dominate; enforce credit metering + plan limits BEFORE generation, and default to the cheapest compliant model (echoes the v1.0 "strictest-channel-first" media policy).
- **Async everywhere** — generation and crawl are long-running; reuse the v1.0 job/event/outcome lifecycle pattern rather than blocking requests.
- **Secret boundary** — provider API keys, Google client secret, and crawl keys are server-only (consistent with PROJECT.md security constraints); never in the browser or committed files.
- **Untrusted external content** — crawled site text/images and model outputs must be sanitized and owner-approved before publish (preserve the v1.0 approval gate).
- **Vendor lock-in** — keep the provider abstraction thin so fal.ai/Replicate/direct providers are swappable.

## 5. Reuse from v1.0 (do not rebuild)

- Sessions/auth + `resolve_session` (Phase 5) → extend for Google.
- Brand kit, Phase 3 creative/carousel/UGC workflow scaffolding → swap templated output for real generation.
- Publish job/attempt/event/outcome lifecycle + redaction → reuse shape for generation jobs.
- Channel health + approval gates → keep before any publish of generated assets.

---
*Research for milestone v2.0 — provider-agnostic, async-first, secret-safe.*
