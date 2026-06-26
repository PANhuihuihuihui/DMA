---
id: S01
milestone: M002
status: draft
---

# S01: Backlog placeholder — Context

## Goal

Define and bound the five remaining Phase 4 build items so the milestone can be sliced and executed: Fernet token persistence, merchant-driven Page selection on Connected Accounts, AI-image wiring with media validation, retry/fallback UX in the Approval Queue, and app review evidence prep.

## Why this Slice

M002 was registered as a placeholder while Phase 3 completed. All five remaining Phase 4 items need full implementation. This context file unblocks detailed slice planning by recording the confirmed behavioral decisions for each area.

## Scope

### In Scope

- Fernet-encrypted SQLite token persistence keyed from `LOCALPILOT_TOKEN_KEY` env var (D10)
- Split OAuth callback: fetch Pages → return to Connected Accounts UI for merchant selection → second call commits choice and stores encrypted token (D11)
- Page selection picker rendered inline on the Connected Accounts screen
- Single-image Facebook posts wired from AI Studio generation output (no manual upload) (D12)
- Media validation for single image + link post paths
- Graph API aligned to v25.0 across all Facebook calls (D13)
- Retry/fallback status badge in Approval Queue with redacted error class and next-step hint (D14)
- Token expiry detected on next publish attempt → authentication error → Connected Accounts screen surfaces a 'Reconnect' CTA; no silent retry
- App review evidence: recorded walkthrough of full publish flow using a test Business account and Page

### Out of Scope

- Manual image upload by the merchant (deferred beyond Phase 4)
- Multi-photo and video Facebook publishing (D12 — deferred)
- Proactive token expiry polling / banner
- Meta app review submission and acceptance (evidence prep is in scope; submission outcome is not)
- Publish trigger from the Creative Editor (Approval Queue is the only publish entry point in Phase 4)
- TikTok integration (Phase 4 is Facebook-only)

## Constraints

- D03: OAuth tokens must stay server-side; never in browser localStorage or committed files
- D04: Explicit merchant approval required before any platform publish request
- D05: Official Graph API paths only; no scraping, cookie-based posting, or browser automation
- D12: Single image + link posts only; no multi-photo or video
- D13: All Facebook Graph API calls must be at v25.0
- Production backend fails closed if `LOCALPILOT_TOKEN_KEY` env var is absent (D10)

## Integration Points

### Consumes

- `facebook_oauth.py` — existing OAuth initiation and callback handler (to be split per D11)
- `facebook_publisher.py` — existing publisher (Graph API version to be aligned to v25.0 per D13)
- Phase 13 `generation_outputs` — AI Studio image asset referenced as image source for single-image posts
- `src/main.jsx` Connected Accounts screen — render surface for Page picker UI
- `src/main.jsx` Approval Queue screen — render surface for publish trigger and failure status badge

### Produces

- Updated `facebook_oauth.py` with split callback and Fernet token persistence
- Updated `facebook_publisher.py` at v25.0 with image validation
- Connected Accounts screen with inline Page picker post-OAuth
- Approval Queue screen with publish button, job status badge, and `manual_fallback_required` error display
- App review screencast artifact (recorded walkthrough of full publish flow on test Business account)

## Open Questions

- Which Graph API permissions are needed for app review (`pages_manage_posts`, `pages_read_engagement`, others)? — Current thinking: those two are the minimum; confirm before recording the screencast.
- Does the test Business account setup require a separate Meta Developer App, or can it use the existing dev-mode app? — Current thinking: existing dev app with a test Page owned by the same account; no separate app needed.
- Page switching: if a merchant wants to disconnect one Page and connect a different one, does Phase 4 need an explicit "change Page" UI? — Current thinking: disconnect-and-reconnect through the existing Connected Accounts flow covers the case; no special path needed in Phase 4.
