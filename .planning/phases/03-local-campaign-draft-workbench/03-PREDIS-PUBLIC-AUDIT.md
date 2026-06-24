---
phase: 03-local-campaign-draft-workbench
status: current-public-audit
captured: 2026-06-18
---

# Predis Public Feature Audit

This audit captures current public Predis.ai evidence used to guide the Phase 3 implementation. It is not a substitute for a logged-in product walkthrough, but it gives us a concrete public parity baseline.

## Sources

- Predis home page: https://predis.ai/
- Predis pricing page: https://predis.ai/pricing/
- Predis social media scheduler page: https://predis.ai/features/social-media-scheduler/
- Predis Shopify listing: https://apps.shopify.com/predisai

## Publicly Confirmed Predis Capabilities

- AI generation for ads, social posts, videos, carousels, captions, memes, hashtags, and creative variations.
- Built-in editor for generated creatives.
- Brand kits / brand management with logo, brand colors, tone of voice, key messaging, and connected social accounts.
- Content calendar, scheduling, auto-posting, and one-click publishing.
- Scheduling/auto-posting integrations across Instagram, Facebook, TikTok, YouTube Shorts, LinkedIn, Pinterest, Google Business, and X.
- Bulk generation and bulk scheduling for posts, carousels, stories, videos, accounts, and platforms.
- Approvals and collaboration with team members, comments, notes, feedback, and approval flow.
- Competitor analysis through linked Facebook Pages and Instagram accounts, with competitor runs as a metered plan concept.
- Analytics dashboard / performance tracking.
- Plan/usage model based on credits, brands, team members, social account limits, and competitor runs.
- Mobile apps for generating and scheduling social posts.

## Current LocalPilot Parity Implemented

- Dashboard/navigation reflects the major product surfaces.
- Brand Kit is now backend-backed through `brand_kits`.
- AI Generator creates backend `content_batches`, `generated_creatives`, `calendar_slots`, and `proof_links`.
- Creative Editor displays post/carousel/reel-style surfaces and keeps approval actions connected to existing backend draft approval.
- Content Calendar remains connected to existing publish workflow and now has backend calendar-slot data available.
- Approval Queue uses exact-version backend approval.
- Connected Accounts keeps Facebook OAuth as the first real adapter and marks other networks as assisted or placeholders.
- Competitor Ideas are backend-backed through `competitor_sources` and `competitor_ideas`.
- Proof Loop records backend `proof_events` and preserves lower-bound evidence language.

## Still Needed For Closer Parity

- Logged-in Predis screen audit and screenshot checklist.
- Real drag/drop calendar interaction and persisted rescheduling.
- More exact creative editor controls: layout, template selection, resizing, asset library, and preview by format.
- Real media/video generation or a selected rendering service.
- Connected-account adapters beyond Facebook.
- True competitor ingestion rather than seeded/demo competitor ideas.
- Usage/credits/plans UI if we want closer pricing/product parity.
