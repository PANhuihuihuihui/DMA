---
quick_task: facebook-demo-publish-loop
status: complete
created: 2026-06-17
phase: 03-facebook-customer-demo-loop
mode: gsd-quick
---

# Facebook Demo Publish Loop

## Goal

Wire the manually proven Facebook Page publishing flow into LocalPilot's backend and UI so a pilot operator can approve a Facebook draft, provide a Page user token for the request, publish through the official Graph API, and see the resulting post ID, permalink, and publish timeline.

## Scope

- Add a backend Facebook publisher that resolves a Page access token from a user token and publishes an approved Facebook draft through Graph API.
- Add an API route that accepts the short-lived token only in the publish request body and never persists or returns it.
- Keep approval snapshots, publish jobs, attempts, events, redacted diagnostics, and idempotency behavior under the existing backend workflow boundary.
- Add frontend client and UI controls for real Facebook publishing on approved Facebook drafts.
- Add backend tests for success and missing-permission failure without making live network calls.

## Acceptance

- A Facebook draft cannot be live-published before exact-version approval.
- Non-Facebook approvals cannot use the live Facebook publish endpoint.
- Successful publish records provider post ID and permalink in redacted diagnostics.
- Provider access tokens are not stored in localStorage, committed files, API responses, attempts, events, or diagnostics.
- Existing fake publish flow and build/test gates still pass.
