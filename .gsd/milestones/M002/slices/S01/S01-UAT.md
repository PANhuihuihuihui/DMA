# S01: Backlog placeholder — UAT

**Milestone:** M002
**Written:** 2026-06-26T06:45:24.119Z

## UAT: S01 Phase 4 Integration

### Preconditions

- Dev server: `npm run dev` running at `http://localhost:5173`
- Backend: `python backend/app/server.py` running at `http://localhost:5000`
- Database: SQLite at `backend/app/data.db` with schema initialized
- Meta dev app credentials: `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` set in `.env` or test harness

### Test Case 1: connectSession OAuth Page Picker Flow

**Goal:** Verify OAuth callback with `connectSession` param triggers page picker rendering and selection persists.

**Steps:**
1. Navigate to `/app` and click "Connect Facebook" in Brand & Social Accounts
2. Follow OAuth redirect to Meta login (or use dev-mode pre-filled)
3. Approve app permissions
4. Observe: page picker appears in "Social Platforms" tab with list of merchant's Pages
5. Click a Page card
6. Observe: picker closes, selected page displays in Connected Accounts list, connectSession param removed from URL

**Expected Outcome:**
- Page picker renders only during connectSession flow (hidden otherwise)
- Selected Page persists to database (facebook_page_tokens.current_page_id)
- App toast confirms success
- No errors in console or backend logs

**Edge Cases:**
- Session expired: backend returns 401 → app toast "Session expired"
- Invalid pageId: backend returns 400 → app toast with error message
- Network timeout: app toast shows timeout message
- User navigates away during picker: connectSession clears, picker hides on return

---

### Test Case 2: manual-fallback-hint in Approval Queue

**Goal:** Verify Approval Queue shows next-step hints and Reconnect CTA for failed publish jobs.

**Steps:**
1. Trigger a publish job that fails with `manual_fallback_required` status
2. Navigate to Approval Queue
3. Observe: failed job shows status badge + hint block
4. Verify: hint text matches error class (e.g., "auth" → "Your account needs reconnection")
5. Click Reconnect button (if auth error)
6. Observe: navigates to Brand & Social Accounts screen

**Expected Outcome:**
- Hint block renders only for manual_fallback_required status
- Error class redacted (no system details exposed)
- Reconnect button appears only for auth errors
- Navigation to reconnection UI works

**Edge Cases:**
- Non-auth error (e.g., daily limit): Reconnect button hidden, hint text differs
- No manual_fallback_required status: hint block hidden
- Multiple failed jobs: each shows its own hint

---

### Test Case 3: AI Studio Image Attachment to Facebook Draft

**Goal:** Verify AI-generated images can be attached to Facebook drafts via "Use for Facebook post" button.

**Steps:**
1. Generate image in AI Studio (or use mock generation_outputs table entry)
2. Observe: "Use for Facebook post" button appears (visible only if facebook draft exists)
3. Click button
4. Observe: app toast shows "Image attached to draft" (or similar)
5. Navigate to Drafts & Posts
6. Observe: Facebook draft now references the attached image in media section

**Expected Outcome:**
- Button visible only when both image and facebook draft exist
- Image attached via POST `/api/v1/drafts/{id}/media`
- Draft media_refs updated in database
- Image asset ready for publishing

**Edge Cases:**
- No Facebook draft: button hidden
- No images: button disabled or not rendered
- Attachment fails: backend returns 400/500 → app toast with error
- Image already attached: button disabled or shows "attached" state

---

### Test Case 4: App Review Evidence Documentation

**Goal:** Verify docs/app-review-evidence.md provides complete walkthrough for Meta App Review.

**Steps:**
1. Read `docs/app-review-evidence.md`
2. Verify: contains Graph API permissions (pages_manage_posts, pages_read_engagement)
3. Verify: test account setup section present
4. Verify: full publish flow walkthrough documented
5. Verify: screencast checklist provided
6. Verify: all three S01-CONTEXT open questions answered

**Expected Outcome:**
- Document is complete and self-contained
- Permissions section lists required scopes with rationale
- Test setup section allows reviewer to reproduce the flow
- Walkthrough is step-by-step and unambiguous
- Screencast checklist is actionable (e.g., "record Page picker flow", "show token persistence")

---

## UAT Type

- UAT mode: browser-executable (TC1, TC2, TC3 use localhost + screenshots + form interactions)
- UAT mode: artifact-check (TC4 verifies document completeness via grep + section count)
