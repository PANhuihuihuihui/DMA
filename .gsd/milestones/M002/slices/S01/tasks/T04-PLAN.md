---
estimated_steps: 8
estimated_files: 1
skills_used: []
---

# T04: Authored docs/app-review-evidence.md covering Phase 4 Graph API scopes, test-account setup, Page-switching path, full publish walkthrough, and screencast checklist — resolving all three S01-CONTEXT open questions.

Why: S01-CONTEXT scope lists 'app review screencast artifact' as an in-scope deliverable. This document records the required permissions, test account setup, full publish flow walkthrough, and screencast instructions needed to produce Meta App Review evidence. The three open questions from S01-CONTEXT are resolved here.

Do: Create docs/app-review-evidence.md with these sections:
1. Required Graph API Permissions: pages_show_list (list manageable Pages), pages_read_engagement (confirm publish success), pages_manage_posts (create posts). Rationale: these three are the minimum for the publish flow; no additional permissions needed for Phase 4.
2. Test Account Setup: use the existing dev-mode Facebook App; create or use a test Page owned by the same Business account; no separate Meta Developer App is needed (resolves open question 2 from S01-CONTEXT).
3. Page Switching: disconnect-and-reconnect via the Connected Accounts OAuth flow covers the Page switching case; no special 'change Page' UI is needed in Phase 4 (resolves open question 3).
4. Full Publish Flow Walkthrough: step-by-step instructions: start backend, log in, navigate to Connected Accounts, click Connect Facebook, complete OAuth, see Page picker, select test Page, navigate to AI Studio, generate an image, click 'Use for Facebook post', navigate to Approval Queue, approve the Facebook draft, click Publish Live, confirm, verify the post appears on the Facebook Page.
5. Screencast Recording Checklist: what to show on screen (each step above), key moments to highlight (OAuth redirect, Page picker, image attachment, approval, publish confirmation, live post), recommended duration (~5 minutes), recommended tool (QuickTime or Loom).

Done when: docs/app-review-evidence.md exists and contains all five sections with the open questions resolved.

## Inputs

- None specified.

## Expected Output

- `docs/app-review-evidence.md`

## Verification

test -f docs/app-review-evidence.md
