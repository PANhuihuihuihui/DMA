# LocalPilot AI Feature Gap Priority Review

Date: 2026-06-06

Audience: CEO, product, engineering

## CEO Summary

LocalPilot AI already has the right product wedge: a local-business AI marketing operator, not another social scheduler. The current demo communicates the concept with a public landing page, fake login, platform-native channel plans, Xiaohongshu positioning, local ROI signals, approval actions, and reviewable module tabs.

The biggest missing product capabilities are the systems that make the demo real: business onboarding memory, AI campaign generation backed by stored business context, publishing/export workflows, conversion tracking, inbox/reply operations, integrations, and an internal admin console for concierge pilots.

Recommendation: prioritize features that help us close pilot customers and prove weekly ROI before investing deeply in full automation.

## Current Product Signals Already Present

- Public landing page and investor/customer story.
- Post-login demo workspace.
- One offer to multiple platform-native channel plans.
- Channel-specific hooks, captions, CTAs, KPIs, publishing mode, and owner tasks.
- Xiaohongshu/RED as a native channel, not just translated Instagram copy.
- Approval and change-request actions.
- Calendar, inbox, analytics, reports, media library, approvals, clients, settings modules as reviewable demo surfaces.
- Local ROI concepts: calls, bookings, DMs, coupon scans, saves, map clicks.

## Missing Features By Priority

### P0: Pilot-Closing Features

These features turn the prototype into a usable concierge MVP for the first paying customers.

| Feature | Why it matters | Engineering assignment | Success metric |
| --- | --- | --- | --- |
| Business onboarding profile | The AI cannot produce specific campaigns unless it knows the business, location, services, audience, tone, languages, offers, and goals. | Full-stack engineer owns data model, frontend form, persistence. AI engineer defines profile schema used in prompts. | 5 pilot businesses can complete onboarding without manual setup. |
| Real campaign generation flow | The current demo uses generated/sample data. We need a real prompt-to-campaign workflow that creates platform-native outputs from a business profile and offer. | AI engineer owns structured output pipeline. Frontend engineer owns generation UX and loading/error states. | Owner can generate a weekly plan in under 10 minutes. |
| Assisted publishing package export | API publishing will be hard. The fastest usable workflow is to export captions, cover text, hashtags, checklist, and assets per channel. | Full-stack engineer owns export endpoint and package model. Frontend engineer owns download/share UI. | A pilot customer can publish manually from a LocalPilot package. |
| Approval queue with saved state | Agencies and owners need approve/request-change history, not temporary demo clicks. | Full-stack engineer owns approvals table/API. Frontend engineer owns queue UX. | Every generated asset has an approval status and revision note. |
| Pilot lead capture and CRM handoff | We need to turn landing-page interest into discovery calls and paid pilots. | Frontend/full-stack engineer owns form submission, notifications, CRM/export. | 50 waitlist leads and 10 discovery calls can be tracked cleanly. |

### P1: ROI-Proving Features

These features prove the product is worth paying for every month.

| Feature | Why it matters | Engineering assignment | Success metric |
| --- | --- | --- | --- |
| Conversion tracking starter kit | The product must connect content to business outcomes: calls, bookings, DMs, coupon redemptions, QR scans, website clicks, and map clicks. | Backend engineer owns conversion event model. Frontend engineer owns ROI dashboard. | 30% of pilot users connect at least one measurable action. |
| UTM, coupon, and QR code generator | Attribution is hard, so start with simple links and codes we control. | Full-stack engineer owns generator and tracking redirect. | Every campaign package includes trackable actions. |
| Weekly ROI report | Owners do not want a complex dashboard. They need a plain-language weekly explanation and next actions. | AI engineer owns report generation. Frontend engineer owns report view/export. | Pilot users receive one useful weekly report per business. |
| Inbox/reply assistant | Comments, DMs, and reviews create leads. Drafting replies is high-value and easier than full publishing automation. | AI engineer owns reply templates and escalation rules. Full-stack engineer owns message storage/import. | Users can approve reply drafts for common lead and complaint scenarios. |
| Local business analytics dashboard | We need simple metrics by channel and by business outcome, not vanity-only graphs. | Frontend engineer owns dashboard. Backend engineer owns analytics snapshots. | CEO can see which channels produced customer intent. |

### P2: Growth And Automation Features

These features reduce manual work after the concierge MVP proves demand.

| Feature | Why it matters | Engineering assignment | Success metric |
| --- | --- | --- | --- |
| Meta publishing integration | Facebook and Instagram direct publishing can reduce owner friction where API permissions allow. | Integrations engineer owns OAuth, permissions, token refresh, posting jobs. | Eligible accounts can schedule at least one supported post type. |
| TikTok direct post/upload-to-draft | TikTok is core to the pitch but API eligibility and media constraints need careful handling. | Integrations engineer owns TikTok flow. Backend engineer owns media validation. | Pilot user can send one approved TikTok asset to draft/post. |
| Google Business Profile workflow | Local search is important for real local businesses. | Integrations engineer owns Google auth and posting. | Businesses can prepare or publish local updates. |
| Team and agency workflow | Agencies need multiple clients, roles, approvals, and white-label reporting. | Full-stack engineer owns organizations, roles, client workspaces. | One agency can manage 3 client profiles. |
| Media library and brand assets | Reusable photos, videos, logos, offers, and brand rules make output more specific. | Full-stack engineer owns asset storage. Frontend engineer owns library UI. | Campaign generator can use approved customer assets. |

### P3: Defensibility Features

These features become the moat after we have usage data.

| Feature | Why it matters | Engineering assignment | Success metric |
| --- | --- | --- | --- |
| Trend-to-action analyzer | A trend feed alone is not enough. The value is telling a local business whether to use, adapt, ignore, or avoid a trend. | Data/AI engineer owns collection and classification. | Weekly recommendations include trend decisions by industry. |
| Competitor watcher | Local businesses care what nearby competitors are doing. This makes recommendations more specific. | Data engineer owns competitor profiles and content snapshots. | Reports include useful competitor insights for pilot accounts. |
| Xiaohongshu KOL/KOC brief workflow | RED is the strongest cross-cultural wedge, but KOL workflows are more complex than basic content generation. | Product + AI engineer define brief format. Integrations/data engineer researches compliant routes. | Generate a reviewable KOC brief for one pilot business. |
| Recommendation engine from campaign history | The product becomes smarter when it learns which content drives demand. | AI/data engineer owns feedback loop and campaign memory. | Next-week plan changes based on prior campaign results. |
| Compliance and brand safety service | Needed for clinics, med spas, financial services, real estate, and regulated claims. | AI engineer owns rules and flagged-output workflow. | Risky claims are flagged before publishing/export. |

## Recommended Build Order

1. Business onboarding profile.
2. Real campaign generation from business profile and offer.
3. Approval queue and revision notes.
4. Assisted publishing package export.
5. Pilot lead capture and CRM handoff.
6. Conversion tracking starter kit with UTM/coupon/QR codes.
7. Weekly ROI report.
8. Inbox/reply assistant.
9. Meta/TikTok/Google integrations after pilot validation.
10. Trend, competitor, Xiaohongshu KOL/KOC, and recommendation intelligence.

## Engineering Team Split

| Role | First ownership |
| --- | --- |
| Product manager | Pilot use cases, acceptance criteria, customer interview script, weekly prioritization. |
| Frontend engineer | Onboarding, campaign workbench, approval queue, export UI, ROI report views. |
| Backend/full-stack engineer | Auth, database, organizations, campaign APIs, approvals, conversion events, export service. |
| AI engineer | Business profile schema, campaign generator, reply assistant, weekly report generator, compliance checks. |
| Integrations engineer | Meta, TikTok, Google Business, token handling, posting jobs, API eligibility checks. |
| Data engineer | Trend collection, competitor watcher, analytics snapshots, recommendation memory. |
| Design/product UX | Owner-friendly workflows, no-login review package, agency/client review surfaces. |

## CEO Discussion Questions

1. Who is the first paying customer: owner-operated restaurant/salon, Chinese-community business, or agency managing local clients?
2. Are we selling the first pilot as software only, or AI plus light human review?
3. Which promise matters most for the landing page: Xiaohongshu growth, local ROI, or one offer to all channels?
4. What is the first measurable conversion we will require from every pilot: phone calls, bookings, DMs, coupon scans, or QR codes?
5. Do we want to build direct publishing early, or deliberately sell assisted publishing as the safer MVP path?

