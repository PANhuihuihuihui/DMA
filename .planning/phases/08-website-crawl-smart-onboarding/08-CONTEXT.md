# Phase 8: Website-Crawl Smart Onboarding - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 adds website-crawl smart onboarding. A merchant enters a URL → the backend fetches the page, extracts brand data via LLM, and presents a pre-filled profile the merchant can edit and confirm. This is self-built (AiToEarn has no equivalent).

In scope: ONBOARD-01, ONBOARD-02, ONBOARD-03, ONBOARD-04, ONBOARD-05.

Out of scope:
- Headless browser rendering or screenshot capture
- External crawl APIs (Jina, Firecrawl)
- Multi-page deep crawl (homepage only for MVP)
- Competitor analysis from crawled data
- Automatic re-crawl / scheduling
</domain>

<decisions>
## Implementation Decisions

### Crawl Strategy
- **D-01:** Use simple HTTP fetch (Python `urllib` or `requests`-style) to get the homepage HTML. No headless browser, no external crawl API. Local business sites (WordPress, Wix, Squarespace) have sufficient meta tags and visible text for extraction.
- **D-02:** Fetch the homepage only (single page). Do not spider or follow links for the MVP. The URL the merchant enters is the page we crawl.
- **D-03:** Set a reasonable User-Agent string, respect robots.txt for politeness, and apply a timeout (10-15s). If blocked or timing out, fail gracefully.

### Extraction Engine
- **D-04:** Use LLM-only extraction. Feed the fetched HTML content (stripped to meaningful text, meta tags, and structural hints) to the configured generation provider (GPT) with a structured prompt asking for the brand profile fields.
- **D-05:** The LLM prompt should request JSON output with the exact field schema. No deterministic regex/DOM parsing step — the LLM handles messy real-world HTML directly.
- **D-06:** Pre-process HTML before sending to LLM: strip scripts/styles/nav boilerplate, extract meta tags (og:*, description, theme-color, JSON-LD), keep meaningful body text. This reduces token cost and noise.

### Profile Schema (Predis-style)
- **D-07:** The auto-generated profile includes:
  - **Business identity:** name, description (1-2 sentences), industry/business type
  - **Brand style:** logo URL (from og:image or favicon), primary color, secondary color, accent color, font family suggestion
  - **Content settings:** language, timezone, tonality (formal / casual / playful / professional), target audience description
- **D-08:** These fields map onto the existing `brand_kits` table (Phase 3) where applicable. New fields (industry, tonality, target_audience, timezone) go into a `merchant_profiles` table or extend `merchants`.

### Content Defaults Presentation
- **D-09:** All inferred fields are auto-filled with the LLM's best guess. The merchant sees a pre-populated form and edits only what's wrong. No confidence indicators or mandatory confirmations per field.
- **D-10:** A single "Confirm" action saves the profile. Until confirmed, the profile is in draft state and does not affect generation or publishing.

### Review & Edit UX
- **D-11:** Present the generated profile as a single editable card (one scrollable form) with all fields pre-filled. "Confirm" button at the bottom saves to backend.
- **D-12:** The card appears immediately after crawl completes — no multi-step wizard, no side-by-side preview. Keep it fast: URL input → loading state → editable card → confirm.
- **D-13:** Re-fetch (entering a new URL) replaces the current draft with an explicit warning ("This will replace your current profile draft. Continue?") per ONBOARD-04.

### Error Handling
- **D-14:** When crawl fails (timeout, blocked, DNS error) or LLM extraction returns too little data, show what we got and leave sparse fields blank/with defaults. Let the merchant fill manually.
- **D-15:** Never block onboarding entirely due to crawl failure. The manual path (empty form) is always available as fallback.
- **D-16:** Sanitize all crawled content before display or storage (strip HTML, validate URLs, no script injection) per ONBOARD-05.

### Agent's Discretion
- Exact HTTP library choice (stdlib `urllib.request` vs adding `httpx`).
- Exact LLM prompt wording for extraction (as long as it produces the schema above).
- Exact pre-processing strategy for HTML→text reduction before LLM.
- Whether to add the profile fields to `merchants` table directly or a new `merchant_profiles` table.
- Exact UI layout of the editable card within the existing app shell.
- Token cost optimization (truncation strategy for large pages).
</decisions>

<canonical_refs>
## Canonical References

### Project And Scope
- `.planning/PROJECT.md` — platform priorities, v2.0 milestone scope.
- `.planning/ROADMAP.md` — Phase 8 goal, requirements ONBOARD-01 through ONBOARD-05, success criteria.
- `.planning/REQUIREMENTS.md` — Smart Onboarding requirements section.

### Existing LocalPilot Seams
- `backend/app/server.py` — current route and API registration style.
- `backend/app/store.py` — persistence patterns, `brand_kits` table, migration style.
- `backend/app/google_auth.py` — Phase 7 auth module (merchant must be authenticated to onboard).
- `src/main.jsx` — app shell, current onboarding surface.
- `src/api/publishingClient.js` — client boundary for backend APIs.

### No External Reference
- AiToEarn has no website-crawl onboarding equivalent. This is self-built based on Predis.ai's "Fetch details from website" UX pattern.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `brand_kits` table already stores name, colors, fonts, logo, website, social_handle, typography — the crawl output can seed this directly.
- Phase 7 Google auth means we have authenticated merchants with `merchant_id` to scope the profile.
- The existing `store.migrate_database` pattern handles additive columns cleanly.
- `src/api/publishingClient.js` with `credentials: "include"` is ready for new authenticated endpoints.

### Integration Points
- The onboarding flow should be accessible from the authenticated workspace (post-login, pre-generation).
- Generated profile data should seed the brand kit used by the generation workspace (Phase 13).
- The crawl endpoint should be merchant-scoped (requires active session from Phase 7).
</code_context>

<specifics>
## Specific Ideas

- The LLM extraction prompt should produce a flat JSON matching the target schema — no nested objects beyond what the DB needs.
- For MVP, the frontend can show a simple URL input → spinner → editable card. No preview of the website itself.
- Consider a character/token budget for the HTML fed to the LLM (e.g., first 8K tokens of cleaned text + all meta tags) to control cost.
- The "re-fetch" warning (D-13) should be a simple confirm dialog, not a diff view.
</specifics>

<deferred>
## Deferred Ideas

- Multi-page crawl (spider the site for more signal) — add if single-page extraction proves too sparse.
- Screenshot-based extraction (headless browser renders the page, feeds image to vision model).
- Automatic periodic re-crawl to keep brand data fresh.
- Competitor website analysis from the crawled domain.
- External crawl API integration (Jina, Firecrawl) as a quality upgrade path.
</deferred>

---

*Phase: 8-Website-Crawl Smart Onboarding*
*Context gathered: 2026-06-25*
