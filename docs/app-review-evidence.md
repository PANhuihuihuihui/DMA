# App Review Evidence Preparation (M002/S01/T04)

> Phase 4 Meta App Review preparation guide. Resolves the three open questions
> from `.gsd/milestones/M002/slices/S01/S01-CONTEXT.md` and provides the
> walkthrough + screencast checklist needed to record evidence.
>
> Companion reference: `docs/facebook-app-review-evidence.md` (FB-01 canonical
> evidence artifact — covers App Configuration, Permissions, Tokens, and
> Data Handling in more depth).

---

## 1. Required Graph API Permissions

The minimum permission set for the Phase 4 publish flow is three scopes — no
additional permissions are needed beyond these.

| Scope | Purpose | Where it is used |
|-------|---------|------------------|
| `pages_show_list` | List Pages the merchant manages so the inline Page picker can render after OAuth. | `me/accounts` call inside `complete_callback()` in `backend/app/facebook_oauth.py`. |
| `pages_read_engagement` | Read back post state after publish (post id / permalink) and confirm publish success. Also unlocks full Page API access for the publisher. | `backend/app/facebook_publisher.py` after a `/{page-id}/feed` or `/{page-id}/photos` POST. |
| `pages_manage_posts` | Publish posts (text, link, single image) to the merchant-selected Page. **Advanced Access** scope — requires App Review + Business Verification. | `backend/app/facebook_publisher.py` POST calls. |

**Rationale (resolves S01-CONTEXT open question 1):** The three scopes above are
sufficient for the Phase 4 publish flow (text / link / single-image posts to a
merchant-selected Page). No `pages_manage_metadata`, `pages_messaging`, or
other Page scopes are needed for the in-scope publish surface. Confirm scope
selection in the Meta App Dashboard matches `REQUIRED_SCOPES` in
`facebook_oauth.py` before recording the screencast.

---

## 2. Test Account Setup

**Resolves S01-CONTEXT open question 2: the existing dev-mode Facebook App is
sufficient. No separate Meta Developer App is needed for Phase 4 review
evidence.**

Steps for a clean test environment:

1. **Use the existing dev-mode Facebook App.** Same `FACEBOOK_APP_ID` /
   `FACEBOOK_APP_SECRET` already used for local development. Confirm the
   redirect URI `http://127.0.0.1:8787/api/v1/facebook/oauth/callback` is
   registered in the Meta App Dashboard → Facebook Login → Settings.
2. **Create or reuse a test Page owned by the same Business account** that owns
   the dev app. Either:
   - Meta App Dashboard → Roles → Test Users → create a test user, then sign in
     as that user and create a Facebook Page (e.g. "LocalPilot Test Café"), or
   - Use an existing Page where the dev-app admin is also a Page admin.
3. **Verify the Page has publishing capability.** Call
   `GET /me/accounts?fields=id,name,category,tasks,access_token` with the
   logged-in user's token and confirm the Page's `tasks` array contains
   `CREATE_CONTENT` (or `MANAGE`).
4. **Run the stack locally:**
   ```bash
   export FACEBOOK_APP_ID="<your-app-id>"
   export FACEBOOK_APP_SECRET="<your-app-secret>"
   export FACEBOOK_REDIRECT_URI="http://127.0.0.1:8787/api/v1/facebook/oauth/callback"
   npm run dev:full
   ```

**Why no separate dev app is needed:** App Review judges the flow as
demonstrated. Standard Access on the existing dev app is enough for the
admin / test-user demo. Advanced Access for `pages_manage_posts` is what the
review process *grants*; it is not a prerequisite for recording the evidence.

---

## 3. Page Switching

**Resolves S01-CONTEXT open question 3: no dedicated "change Page" UI is needed
in Phase 4.** The disconnect-and-reconnect path through the Connected Accounts
screen covers Page switching end-to-end.

Flow for a merchant who wants to switch Pages:

1. Navigate to **Brand & Social Accounts** → find the Facebook tile.
2. Click **Disconnect**. The frontend calls the disconnect endpoint and clears
   the active page token reference. Health badge flips to "Reconnect required".
3. Click **Connect Facebook** again. OAuth re-runs and the inline Page picker
   appears with all manageable Pages listed (per Section 1's
   `pages_show_list` scope).
4. Select the new Page → "Use this Page". The new token becomes the active
   Page token and the badge returns to "Connected".

No new UI surface is required for this flow — the Connected Accounts page
picker added in S01/T01 is the switching mechanism. Document this behavior in
the screencast voiceover if the reviewer asks about Page switching.

---

## 4. Full Publish Flow Walkthrough

Step-by-step instructions for the end-to-end demo. Each numbered step is
recordable in the screencast.

1. **Start the backend and frontend** together:
   ```bash
   npm run dev:full
   ```
   Confirm backend is listening on `http://127.0.0.1:8787` and frontend on
   `http://127.0.0.1:5173`.
2. **Log in** to the LocalPilot demo (any demo email — the publish path uses
   the backend session, not the demo login).
3. **Navigate to Brand & Social Accounts.** The Facebook tile shows
   "Not connected" or "Reconnect required".
4. **Click "Connect Facebook".** Browser redirects to
   `https://www.facebook.com/v25.0/dialog/oauth?...`. Show the URL bar.
5. **Authorize with the test user account** and grant the three requested
   permissions (`pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts`). Pause briefly on the permission grant screen.
6. **Return to LocalPilot.** The redirect lands at
   `/app?connectSession=<id>` and the inline Page picker renders the
   manageable Pages from `me/accounts`.
7. **Select the test Page → "Use this Page".** The health badge changes to
   "Connected" and the active Page token is persisted (Fernet-encrypted
   server-side per `backend/app/token_crypto.py`).
8. **Navigate to AI Studio.** Click "Generate" on an image workflow and wait
   for `succeeded` status.
9. **Click "Use for Facebook post"** on a generated image output. A toast
   confirms the image is attached to the matching Facebook draft (via
   `POST /drafts/{id}/media`, per S01/T03).
10. **Navigate to Approval Queue.** The Facebook draft now shows the attached
    media reference. Click **Approve**, then **Publish Live**, then confirm
    the modal.
11. **Verify publish success.** The publish timeline updates to "Published"
    with the returned Graph post ID. If the publisher returned
    `manual_fallback_required`, the manual-fallback hint block (per S01/T02)
    appears with an error-class-aware hint and a **Reconnect** CTA pointing
    back to Brand & Social Accounts.
12. **Open the Facebook Page** in a new tab (`facebook.com/<page-id>`) and
    confirm the post is live — same caption, same image.

---

## 5. Screencast Recording Checklist

**Recommended length:** ~5 minutes. **Recommended tools:** QuickTime Player
(macOS, free) or Loom (cross-platform, free tier sufficient). Record at
1080p; speak briefly over each key moment.

### What to show on screen

- Browser URL bar visible throughout — proves the OAuth redirect host and the
  return to `127.0.0.1:5173`.
- LocalPilot `/app` workspace at the start; Brand & Social Accounts tile with
  the "Not connected" / "Reconnect required" state.
- The Facebook OAuth dialog with the three permissions listed.
- The inline Page picker rendering the test user's managed Pages.
- The Connected health badge flipping to "Connected".
- AI Studio with a generated image and the **Use for Facebook post** button.
- Approval Queue showing the draft with the attached image and the
  **Publish Live** confirmation modal.
- The Facebook Page itself (`facebook.com/<page-id>`) with the freshly
  published post.

### Key moments to highlight (pause / voice-over)

| # | Moment | What to say |
|---|--------|-------------|
| 1 | OAuth redirect | "The merchant authorizes LocalPilot to access only the three scopes shown — `pages_show_list`, `pages_read_engagement`, and `pages_manage_posts`." |
| 2 | Page picker | "After authorization, LocalPilot lists the Pages this merchant manages. The merchant selects one — only this Page is used for publishing." |
| 3 | Image attachment | "Generated image is attached to the matching Facebook draft via a server-side draft-media reference, not by uploading from the browser." |
| 4 | Approval | "Every publish requires explicit owner approval. The approval freezes the exact draft version that will be published." |
| 5 | Publish confirmation | "Publish goes through the official Graph API at v25.0; the post ID returned is recorded as an immutable publish_attempt audit row." |
| 6 | Live post on Page | "The published post matches the approved draft. The merchant can stop here, or disconnect and reconnect to switch Pages — no special UI needed." |

### Submission notes

- Trim dead time and authentication password entry.
- Add a short title card: app name, version, date, scopes requested.
- Upload the file as MP4 with the App Review submission in the Meta App
  Dashboard → App Review → Permissions and Features → `pages_manage_posts`.

---

## Failure Modes

Not applicable. This task produces a documentation artifact only — it does not
add code paths, runtime dependencies, or external API calls. The publish flow
failure modes (OAuth state expiry, page-token revocation, publisher
`manual_fallback_required`, image-attachment 500s) are covered in
`docs/facebook-app-review-evidence.md` and in the S01/T01–T03 task summaries
where those code paths were implemented.

## Load Profile

Not applicable. This task produces a documentation artifact only — no runtime
load dimension.

## Negative Tests

Not applicable. This task produces a documentation artifact only — there is no
code surface to assert against. The publishing flow it documents already has
negative-test coverage in `backend/tests/` (publisher diagnostics, token
boundary redaction, OAuth state validation).
