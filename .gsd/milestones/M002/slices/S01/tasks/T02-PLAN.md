---
estimated_steps: 12
estimated_files: 2
skills_used: []
---

# T02: Added manual-fallback-hint block with error-class-aware hint text and Reconnect CTA to PublishTimeline; wired onReconnect to Brand & Social Accounts navigation in both call sites

Why: PublishTimeline shows the manual_fallback_required status label but provides no actionable guidance. D14 requires a next-step hint with redacted error class. D11 requires a Reconnect CTA when the error class is authentication (token expiry detected on next publish attempt).

Do:
1. In PublishTimeline.jsx, after the lifecycle steps ol, add a conditional block: when currentStatus === 'manual_fallback_required', render a div with className 'manual-fallback-hint'.
2. Read normalizedJob.latestAttempt?.errorClass and normalizedJob.latestAttempt?.nextAction (both already present from normalizePublishAttempt in publishing.js — errorClass comes from diagnostics.errorClass, nextAction from diagnostics.nextRecommendedAction).
3. Map errorClass to a human-readable hint:
   - authentication or missing_permission: 'Facebook authorization expired or missing. Reconnect this Page to resume publishing.'
   - validation: 'The post content or image failed validation. Edit the draft and re-approve.'
   - rate_limit: 'Facebook rate limit reached. Retry after the limit window passes.'
   - default: 'This post requires manual review before it can be published.'
4. If errorClass is authentication or missing_permission and an onReconnect prop is provided, render a 'Reconnect Facebook' button that calls onReconnect().
5. In main.jsx, pass onReconnect={()=>setActiveModule('Connected Accounts')} (or equivalent navigation to the Connected Accounts module) to both PublishTimeline usages.

Done when: A hint block with human-readable text renders in PublishTimeline when status is manual_fallback_required; a Reconnect Facebook button appears for authentication/missing_permission error class.

## Inputs

- `src/components/PublishTimeline.jsx`
- `src/models/publishing.js`
- `src/main.jsx`

## Expected Output

- `src/components/PublishTimeline.jsx`
- `src/main.jsx`

## Verification

grep -q "manual-fallback-hint" src/components/PublishTimeline.jsx
