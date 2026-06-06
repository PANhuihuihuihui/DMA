# Karen Demo Functional Redesign Plan

Date: 2026-06-05

## Product Direction

The post-login demo should stop feeling like a generic social media dashboard. It should feel like a working LocalPilot AI growth operator for a local small business: one business offer goes in, channel-native content plans come out, the owner can approve or request edits, and the agency can explain exactly what business outcome each post is designed to create.

This pass stays frontend-only in React + Vite. No backend is needed yet.

## Main Problem To Solve

The current demo has the right ingredients, but the value is not obvious enough:

- The bottom area is not useful enough for a customer review.
- LocalPilot-specific features are present but not prominent.
- The app still reads like a simple dashboard with cards and graphs.
- Channel details do not yet feel specific enough to justify paying for the product.
- The responsive layout needs to stay usable all the way down the page.

## Target Demo Story

The customer should understand this flow in under one minute:

1. Pick a local business type and offer.
2. LocalPilot creates a weekly growth plan.
3. Each channel gets its own role, hook, copy, CTA, KPI, publishing note, and owner task.
4. Xiaohongshu is handled as a native strategy, not a translation.
5. Local ROI is tracked through calls, bookings, DMs, coupon scans, saves, and map clicks.
6. The owner or agency can approve, request changes, complete checklist items, and save the posting package.

## First Screen Requirements

The default `/app` route should show a single useful workbench, not many unrelated panels:

- Business setup row: business type, offer, goal, audience, regenerate plan, reset demo.
- LocalPilot value strip: platform-native generation, Xiaohongshu-native strategy, Local ROI loop, assisted publishing.
- Channel tabs: TikTok, Instagram, Facebook, Xiaohongshu, Google Local.
- Selected channel detail: post preview, hook, caption, CTA, KPI, publishing method, asset list, owner task, why it works.
- Right rail: approval queue, local ROI signals, competitor/trend alerts, and package readiness.

## Channel Detail Requirements

Each channel needs enough information for a customer to inspect the output:

- Format: video, reel/story, community post, RED note, Google Business update.
- Post angle: what the creative is trying to say.
- Hook: first line or first 2 seconds.
- Caption: platform-native caption.
- Cover text: what appears on the content.
- CTA: the intended customer action.
- KPI: the business signal to track.
- Publishing mode: direct schedule, assisted publish, manual owner publish, or profile update.
- Assets included: video cut, caption, hashtags, cover copy, comment reply, coupon code, tracking event.
- Owner/agency checklist: approve creative, confirm offer, attach tracking, schedule or publish.

## LocalPilot Differentiators To Highlight

These should be obvious inside the app, not hidden in a side note:

- Platform-native generation: different role, copy, CTA, and KPI per channel.
- Xiaohongshu-native growth: Chinese copy, save-first note structure, search keywords, cover text, and KOC/UGC brief.
- Local ROI: calls, bookings, DMs, coupon scans, saves, and map clicks instead of vanity-only analytics.
- Competitor watcher: nearby offer patterns and posting angles that are working.
- Assisted publishing: packaged outputs for platforms with restricted APIs.
- Agency approval workflow: approve, request changes, checklist completion, and saved package.

## Implementation Tasks

- Replace generic bottom cards with a functional delivery package section.
- Add richer sample data per channel: publishing mode, assets, risk note, tracking events, and sample schedule slot.
- Make the selected channel detail the heart of the page.
- Move LocalPilot differentiators near the top of the workbench.
- Add a package readiness summary that updates as approvals/checklist items change.
- Keep all state in localStorage so demo clicks persist during review.
- Improve responsive CSS so the right rail stacks below the main workbench and bottom sections remain usable on tablet and mobile.

## Acceptance Checks

- `/app` communicates the LocalPilot workflow without needing a spoken explanation.
- A user can switch business type, regenerate a plan, inspect each channel, approve/request changes, complete checklist items, and save a package.
- The Xiaohongshu and Local ROI features stand out on the first app screen.
- The lower page contains useful deliverables, not filler cards.
- Desktop and mobile layouts have no horizontal overflow or clipped controls.
- `npm run build` passes.

## Review Links

Use these direct module links during customer review:

- Home workbench: `/app?module=home`
- AI Studio: `/app?module=ai-studio`
- Publish: `/app?module=publish`
- Calendar: `/app?module=calendar`
- Inbox: `/app?module=inbox`
- Discover: `/app?module=discover`
- Analytics: `/app?module=analytics`
- Reports: `/app?module=reports`
- Media Library: `/app?module=media-library`
- Approvals: `/app?module=approvals`
- Clients: `/app?module=clients`
- Settings: `/app?module=settings`

## Deployment Status

The demo is ready as a frontend-only deployable package:

- Build command: `npm run build`
- Package command: `npm run package:sites`
- Archive path: `/tmp/localpilot-ai-karen-demo-sites.tar.gz`
- Required artifact files are generated under `dist/server`, `dist/client`, and `dist/.openai`.

Remote Sites deployment is currently blocked because the Sites connector returned: `Sites is not yet enabled for this workspace.`

## Open Product Questions For Discussion

- Should the default business be restaurant, HVAC, or a customer-provided real estate example?
- Should the strongest hero feature be Xiaohongshu strategy, Local ROI, or one-offer-to-five-channel generation?
- Should the demo speak more to a small business owner or to an agency managing multiple local clients?
