---
quick_task: facebook-oauth-connect
status: complete
created: 2026-06-17
phase: 03-facebook-customer-demo-loop
mode: gsd-quick
---

# Facebook OAuth Connect

## Goal

Replace Graph API Explorer token paste with a clickable Facebook auth flow: merchant clicks Connect Facebook, grants Page permissions in Meta, LocalPilot stores the resulting Page access token server-side for the local session, and publish uses that connected Page without exposing tokens in the browser.

## Scope

- Add backend OAuth start and callback endpoints using Facebook Login code flow.
- Request `pages_show_list`, `pages_read_engagement`, and `pages_manage_posts`.
- Exchange code server-side using `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, and redirect URI.
- Resolve manageable Pages and connect the selected Page in the backend.
- Store Page tokens in an in-memory local demo token vault, not browser localStorage or committed files.
- Update UI to show a Connect Facebook button and use connected Page publishing.
- Keep the old request-scoped token endpoint out of the primary UI.

## Acceptance

- UI offers clickable Facebook authorization.
- App secret is read only from backend environment.
- Callback validates `state`.
- Publish live works with the connected server-side Page token.
- Tests cover OAuth URL generation, state validation, callback connection, and token redaction.
