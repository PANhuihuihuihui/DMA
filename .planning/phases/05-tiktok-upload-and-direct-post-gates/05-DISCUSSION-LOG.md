# Phase 5: TikTok Upload And Direct-Post Gates - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents. Decisions are captured in `05-CONTEXT.md`.

**Date:** 2026-06-24
**Phase:** 5-TikTok Upload And Direct-Post Gates
**Areas discussed:** Conn / Health / Disconnect, Creator + Disclosure, Publish Path Gate, Media Validation

---

## Conn / Health / Disconnect

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Separate per-channel status model with hard states and persisted reason codes | ✓ |
| 2 | Backend on-demand health only (no persisted state) | |
| 3 | Hybrid persisted + event-based refresh (default + override) | |

**User's choice:** 1  
**Notes:** Channel health can be unhealthy while content continues. User can still build/edit drafts, but scheduling/publishing for that channel is blocked until status is connected.

---

## Creator + Disclosure

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Creator-info snapshot with immutable approval-time confirmation checks | ✓ |
| 2 | UI advisory checks + backend best effort | |
| 3 | Backend-only enforcement, UI advisory only | |

**User's choice:** 1  
**Notes:** Creator settings must be fetched and versioned with explicit user confirmation included in draft approvals before publish queue/publish is allowed.

---

## Publish Path Gate

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Upload-to-Inbox-first with strict Direct Post unlock gates | ✓ |
| 2 | Backend auto-route per job at publish time (user override not explicit) | |
| 3 | User-selectable route with guarded overrides | |

**User's choice:** 1  
**Notes:** Direct Post remains hidden/disabled until all required gates pass: app audit, permissions/scopes, creator-settings alignment, and disclosure confirmation.

---

## Media Validation

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Backend-authoritative media validation before job creation (primary guard) | ✓ |
| 2 | Frontend + backend redundant validation | |
| 3 | Validate only at publish attempt | |

**User's choice:** 1  
**Notes:** TikTok media and variants should follow strict channel-first constraints; generate additional variants only if necessary for performance and relevance.

---

## the agent's Discretion

- Exact health refresh cadence and status cache behavior.
- Exact media validation enum names and publish-route metadata storage location.
- Whether TikTok publish attempts should use unified publisher module or isolated service.

## Deferred Ideas

- None from this pass.
