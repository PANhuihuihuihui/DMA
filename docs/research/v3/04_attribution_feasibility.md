# Attribution Loop Feasibility — Accurate vs Directional

> Date: 2026-06-17
> Context: Pan challenged the v3 recommendation: "I don't think it's technically possible to make the loop accurate."
> Conclusion: Pan is right. Exact social → offline attribution is not technically possible for SMBs. But **directional attribution** is possible and still valuable if marketed honestly.

---

## Executive conclusion

**Do not claim: "We accurately prove every post drove X walk-ins."**

That is technically false for organic social and especially false for offline local businesses.

**Do claim: "We give you directional evidence of what drove clicks, calls, DMs, redemptions, and owner-confirmed visits — enough to stop guessing."**

This changes the product wedge from:

> ❌ "Exact attribution loop"

To:

> ✅ "Evidence loop" / "Directional ROI loop" / "Marketing signal loop"

This is still a good wedge because the current state for SMBs is worse: they have **zero clue** whether social posts did anything beyond likes.

---

## What is technically trackable

| Outcome | Trackability | How | Accuracy | Notes |
|---|---:|---|---:|---|
| Link click from supported surface | High | UTM-tagged short link | 80-95% | Works when the surface supports clickable links. In-app browsers often strip referrer; UTMs are required. |
| Website visit after click | High | UTM + first-party analytics | 80-95% | Loses attribution if user returns later/direct, switches device, or blocks tracking. |
| Call tap from landing page | Medium-high | `tel:` click event + call tracking number | 70-90% | Call tap is trackable; completed/qualified call requires call tracking provider. |
| Form / booking on website | Medium-high | UTM preserved to form submission | 70-90% | Best if we control landing page and booking form. |
| DM click / message intent | Medium | Platform CTA links, manual owner tagging, inbox API where available | 40-80% | Organic Instagram/TikTok DMs are hard to attribute without platform APIs. |
| Coupon redemption | Medium | Unique post code / QR code | 50-85% | Works if staff actually asks/scans code. Operational compliance matters. |
| In-store walk-in | Low | QR/coupon/staff question/geofence | 10-60% | Exact walk-in attribution is not reliable without POS/customer identity integration. |
| Revenue per post | Low-medium | POS/booking integration + coupon/lead ID | 20-80% | Depends on integration depth. For most SMBs, use estimates + confirmed redemptions. |
| Multi-touch journey | Low | MTA model | 10-50% | Broken by privacy, device switching, dark social, offline word-of-mouth. |

---

## Why exact attribution is impossible

### 1. Organic social links are constrained

Instagram feed captions are not reliably clickable for most normal organic posts. Attribution usually has to happen through:

- bio link
- story link sticker
- reel CTA / profile link
- paid ad CTA
- manually typed short code
- QR code on creative

This means per-post attribution on organic Instagram/TikTok is inherently lossy.

### 2. In-app browsers strip referrers

Search result from attribution docs:

> "Instagram's app browser does not pass an HTTP Referer header to the destination URL. The same is true for most in-app browsers (TikTok, Facebook). Without the referrer, GA4 cannot attribute the click to Instagram unless your link carries UTM parameters that say so explicitly."

So UTMs are mandatory, but they only track users who click the UTM link.

### 3. Offline conversions break the chain

For local restaurants, many real conversions are:

- customer sees TikTok, remembers restaurant, walks in later
- customer sees Facebook post, asks spouse, spouse calls
- customer sees Instagram reel, searches Google Maps later
- customer screenshots menu and visits 3 days later
- customer tells friend

No tracking system can deterministically connect these paths to the original post unless the customer identifies themselves via coupon/QR/booking link/tracking number.

### 4. Privacy and platform APIs limit visibility

TikTok/Meta can support offline conversions for **paid ads** via Events API / Conversions API, but:

- this is mostly ad-platform optimization, not SMB dashboard truth
- requires hashed identifiers like email/phone for matching
- lookback windows exist (TikTok max 28 days in searched docs)
- Meta deprecated its separate Offline Conversions API in May 2025; offline events now go through CAPI with `action_source=physical_store` or `system_generated`
- event acceptance/match rates vary; some migrations reported major drops

For organic social posts, the platform does not give reliable user-level attribution.

### 5. Operational compliance matters

Coupon / QR attribution only works if staff consistently asks:

> "Did you see this on Instagram/TikTok?"

or scans the QR/coupon at checkout.

For busy restaurants, this will be inconsistent. The product must assume missing data.

---

## What we can responsibly build

### MVP: Evidence loop, not exact attribution

Every generated campaign should include one or more measurement hooks:

1. **Short link**
   - `ourdomain.com/r/{post_id}`
   - stores channel, campaign, post, business, creative variant
   - redirects to menu / booking / Google Maps / phone page

2. **Trackable landing page**
   - Simple campaign page: dish/promo, CTA buttons
   - CTA events: `call_click`, `directions_click`, `order_click`, `reservation_click`, `dm_click`

3. **Unique coupon / code**
   - Example: `TACO17`, `CAFEJUNE`, `LP10`
   - Owner/staff marks redemption manually or customer enters it online

4. **QR code**
   - Best for in-store flyers, table tents, physical menus, stories/reels where users can screenshot
   - Not reliable for feed posts alone

5. **Owner confirmation prompt**
   - Weekly email asks: "Did any customers mention this post/coupon? Approx count?"
   - This is manual but surprisingly valuable for early pilots

6. **Optional call tracking number**
   - Use Twilio / CallRail-style number per campaign only for businesses where phone is important
   - More accurate for services (HVAC, dental, salon), less important for casual restaurants

### What the dashboard should say

Use honest language:

- "Tracked responses" not "total customers"
- "Attributed signals" not "exact attribution"
- "Known impact" not "full ROI"
- "Estimated lift" only if baseline exists
- "Owner-confirmed" for manually entered data

Example:

> "This week's posts generated 42 tracked clicks, 9 call taps, 4 direction taps, and 3 owner-confirmed coupon redemptions. Because many walk-ins do not click or use coupons, this is a lower-bound signal, not total impact."

This is credible and defensible.

---

## Better product language

### Bad / false

- "Prove exact ROI from every social post"
- "Know exactly how many walk-ins each post drove"
- "Accurate conversion loop from posts to revenue"
- "Attribution solved"

### Good / defensible

- "Stop guessing which posts create real customer signals"
- "Track known clicks, calls, DMs, directions, and coupon redemptions"
- "See lower-bound evidence of what worked"
- "Build a weekly feedback loop from posts to real business actions"
- "Human-approved content with measurable response signals"

---

## Revised moat

The moat is NOT exact attribution.

The moat is:

> **A practical feedback loop that is good enough for SMB decisions.**

An owner doesn't need a data-science-grade causal model. They need to know:

- Did this post get more real response than the last one?
- Did people click/call/ask for directions/use the coupon?
- Should I post more like this next week?
- Did this promotion bring any known customers?

That is technically feasible.

---

## MVP measurement stack recommendation

### No backend-heavy version (fastest)

- Generate unique Bitly-like short links using our backend
- Redirect to existing business URL / Google Maps / phone landing page
- Track click events server-side
- Generate printable / downloadable QR code
- Weekly owner email with simple metrics
- Manual redemption form: owner clicks `+1 redeemed` in email or dashboard

### Better version (still simple)

- First-party campaign landing page per post
- CTA buttons:
  - Call now
  - Get directions
  - Order / reserve
  - DM us
  - Claim coupon
- Track CTA events before redirecting
- Optional Twilio call tracking for call-heavy businesses
- Optional Google Business Profile UTM guidance

### Avoid for MVP

- Multi-touch attribution model
- Geofencing-based walk-in tracking
- POS integrations
- Meta/TikTok offline conversion APIs
- Full CRM identity resolution

Those are expensive, brittle, and distract from PMF.

---

## CEO decision update

Change v3 language from:

> "real attribution loop"

To:

> **"measurable response loop"**

or

> **"evidence loop"**

The product should not promise accuracy. It should promise **less guessing**.

---

## Updated feature priority

1. **Short link + QR generator** — must have
2. **CTA event tracking** — must have
3. **Manual coupon redemption counter** — must have
4. **Weekly response summary email** — must have
5. **Call tracking integration** — optional, vertical-specific
6. **POS / booking integrations** — post-PMF
7. **Platform offline conversion APIs** — paid ads feature, not organic MVP

---

## Final answer to Pan's concern

Pan is correct: **the loop cannot be accurate in the strict sense.**

But the product does not need exact attribution to be useful. The right MVP is an **evidence loop** that captures the measurable lower bound of response: clicks, call taps, direction taps, DMs, coupon redemptions, owner-confirmed mentions.

The competitive claim becomes:

> "Predis/Buffer tell you likes and scheduled posts. We tell you which posts produced measurable customer actions — with honest lower-bound tracking."

That is technically possible and strategically strong.