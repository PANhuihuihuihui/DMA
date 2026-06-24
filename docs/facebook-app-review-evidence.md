# Facebook Page Publishing — App Review Evidence (FB-01)

> Canonical evidence artifact for Meta app review, production readiness, and internal reference.
> Grounded in the actual `backend/app/facebook_oauth.py` code and Graph API v25.0.

---

## 1. App Configuration

| Setting | Value / Source |
|---------|---------------|
| App ID | Env: `FACEBOOK_APP_ID` (never committed) |
| App Secret | Env: `FACEBOOK_APP_SECRET` (never committed) |
| Redirect URI | Env: `FACEBOOK_REDIRECT_URI`, default `http://127.0.0.1:8787/api/v1/facebook/oauth/callback` |
| OAuth Return URL | Env: `FACEBOOK_OAUTH_RETURN_URL`, default `http://127.0.0.1:5173/app?facebookConnected=1` |
| Graph API Version | v25.0 (both OAuth and publisher — aligned in Phase 4) |
| Dialog Base | `https://www.facebook.com/v25.0/dialog/oauth` |
| Flow | Authorization Code flow (`response_type=code`) with server-side code exchange |

The OAuth flow is implemented in `backend/app/facebook_oauth.py`:
- `build_login_url()` constructs the dialog redirect with a random CSRF `state` token (TTL 600s).
- `complete_callback()` exchanges the authorization code for a user token, extends to a long-lived user token, fetches managed Pages, and (after Phase 4) returns the Page list for merchant selection.
- The app secret is used **only server-side** in `exchange_code_for_user_token()` and `exchange_for_long_lived_user_token()` — it never reaches the browser.

---

## 2. Permissions & Scopes

Requested scopes (from `REQUIRED_SCOPES` in `facebook_oauth.py`):

| Scope | Purpose in LocalPilot | Access Level |
|-------|----------------------|--------------|
| `pages_show_list` | Fetch the merchant's managed Pages via `me/accounts` for the Page picker | Standard Access |
| `pages_read_engagement` | Read post insights and engagement (future analytics; required for full Page API access) | Standard Access |
| `pages_manage_posts` | **Publish posts** to the merchant-selected Page (`/{page-id}/feed`, `/{page-id}/photos`) | **Advanced Access** — requires App Review + Business Verification |

### App Review Requirements for `pages_manage_posts`

- **Standard Access** (no review needed): Only the app admin and test users can publish. Sufficient for development and internal testing.
- **Advanced Access** (requires review): Required to publish to Pages managed by merchants who are NOT the app admin.
  - Submit for App Review in the Meta App Dashboard → App Review → Permissions and Features.
  - **Business Verification** must be completed before Advanced Access can be granted.
  - Provide a screencast demonstrating the connect → select Page → approve → publish flow (see Section 4).
  - Explain the use case: "LocalPilot helps local business owners generate and publish approved Facebook Page posts from within the LocalPilot app. The merchant connects their own Facebook account, selects one of their managed Pages, reviews and approves the generated content, then publishes through the official Graph API."

---

## 3. Test Page & Test User Setup

### Creating a Test Environment

1. **Meta App Dashboard → Roles → Test Users:**
   - Create a test user (or use an existing one).
   - The test user must have a Facebook account and be added as a tester for the app.

2. **Create a Test Page:**
   - Log in as the test user.
   - Create a Facebook Page (e.g., "LocalPilot Test Café").
   - The test user must be an admin of this Page.

3. **Verify Page Capabilities:**
   - Call `GET /me/accounts?fields=id,name,category,tasks,access_token` with the test user's token.
   - Confirm the test Page includes `CREATE_CONTENT` and/or `MANAGE` in the `tasks` array.
   - If `tasks` is empty or missing `CREATE_CONTENT`, the Page may not have publishing capability — check that the test user has admin role.

4. **Configure LocalPilot for Testing:**
   ```bash
   export FACEBOOK_APP_ID="<your-app-id>"
   export FACEBOOK_APP_SECRET="<your-app-secret>"
   export FACEBOOK_REDIRECT_URI="http://127.0.0.1:8787/api/v1/facebook/oauth/callback"
   npm run dev:full
   ```

5. **Test the Flow:**
   - Navigate to `/app`, click "Connect Facebook".
   - Authorize with the test user account.
   - Select the test Page in the picker.
   - Create a campaign, approve a draft, and publish.

---

## 4. Screencast Checklist

Record a screencast demonstrating these steps for App Review submission:

| Step | Action | Expected On-Screen Result |
|------|--------|--------------------------|
| 1 | Navigate to LocalPilot `/app` workspace | App dashboard loads |
| 2 | Click "Connect Facebook" | Redirects to Facebook login/authorization dialog |
| 3 | Authorize the app with required permissions | Redirects back to LocalPilot with managed Pages listed |
| 4 | Select a Page in the picker, click "Use this Page" | Page is marked as active; health badge shows "Connected" |
| 5 | Enter a campaign offer/promotion | Campaign draft is generated with Facebook-specific copy |
| 6 | Review the generated Facebook draft | Draft shows caption, CTA, and any media guidance |
| 7 | Approve the draft for publishing | Draft status changes to "Approved" |
| 8 | Click "Publish to Facebook" (text-only post) | Post is published; post ID and permalink are displayed |
| 9 | Click "Publish to Facebook" (post with link) | Link post is published; permalink is displayed |
| 10 | Click "Publish to Facebook" (post with single image) | Photo post is published via `/{page}/photos`; post ID captured |
| 11 | Verify the post exists on the Facebook Page | Navigate to the Page on facebook.com — post is visible |

**Tips for the screencast:**
- Show the browser URL bar to prove the redirect flow.
- Pause briefly on each permission grant screen.
- Show the health badge changing from "Reconnect required" to "Connected" after authorization.
- Show a clear "Published" status with the post ID after each publish action.

---

## 5. Data Handling & Privacy Evidence

### Token Security

- **Server-side encrypted storage:** Facebook Page access tokens are encrypted at rest using Fernet (AES-128-CBC + HMAC-SHA256) with a server-side key (`LOCALPILOT_TOKEN_KEY` env var). The token encryption module is `backend/app/token_crypto.py`.
- **Never in the browser:** Tokens are never stored in `localStorage`, cookies, or any client-accessible storage. The frontend only ever receives redacted token-boundary references (`backend/app/token_boundary.py` → `serialize_token_boundary_ref()`), which contain:
  - `id` (opaque boundary ref ID)
  - `provider` ("facebook")
  - `storageMode` ("external_secret_ref")
  - `visibility` ("redacted")
  - `rotation.status` ("active" / "reconnect_required")
- **Never committed:** App secrets, tokens, and encryption keys are loaded from environment variables and never appear in source code or version control.
- **Redacted diagnostics:** Publish job diagnostics (`backend/app/facebook_publisher.py` → `provider_diagnostics()`) never include token material. The diagnostic redaction is tested in `backend/tests/test_token_boundary.py`.

### Audit Trail

- Every publish attempt is recorded as an immutable `publish_attempt` row with request digest, trace ID, timestamps, and redacted diagnostics.
- Every draft approval creates a frozen snapshot (`approval_snapshot`) that includes the exact draft version, approver, and timestamp — ensuring the published content matches what was approved.

---

## 6. Open Items / Blockers

| Item | Status | Blocker? |
|------|--------|----------|
| Meta developer app created with correct redirect URI | Required before first OAuth test | Yes — must be configured |
| Business Verification completed | Required for Advanced Access to `pages_manage_posts` | Yes — blocks publishing to non-owned Pages |
| Advanced Access approved for `pages_manage_posts` | Required for merchant publishing | Yes — blocks production use |
| Screencast recorded and submitted | Required for App Review | Yes — must demonstrate the full flow |
| Production redirect URI configured | Replace localhost with production domain | Yes — before production deployment |

**Current state:** Live publishing works for app admins and test users (Standard Access). Merchant publishing requires completing Business Verification and App Review for Advanced Access.

---

*Last updated: 2026-06-23*
*Phase: 4 — Facebook Page Publishing Hardening*
*Requirement: FB-01*
