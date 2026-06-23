# Phase 4: Facebook Page Publishing Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-23
**Phase:** 4-Facebook Page Publishing Hardening
**Areas discussed:** Token persistence, Page selection, Media validation

---

## Token Persistence

### Storage mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Encrypted column in SQLite | Add a tokens table, store ciphertext only, reuse existing DB + token_boundary refs | ✓ |
| External secret-ref store | Write secret to separate file/secret manager, keep ref+fingerprint in SQLite | |
| Pluggable boundary now | TokenVault interface with SQLite-encrypted default + seam for KMS/Vault later | |

### Encryption key source

| Option | Description | Selected |
|--------|-------------|----------|
| Single app key from env var | LOCALPILOT_TOKEN_KEY, Fernet/AES-GCM, fail closed if missing | ✓ |
| Key derived from env passphrase via KDF | scrypt/PBKDF2, no raw key handling | |
| Per-record data keys (envelope) | Wrapped by master env key, most robust/rotatable | |

### Dev-vs-production story

| Option | Description | Selected |
|--------|-------------|----------|
| Graceful dev fallback | Insecure labeled dev mode when no key; production requires key | ✓ |
| Always require the key | Even local dev must set the key; no insecure mode | |
| Always encrypt, auto-gen dev key | Generate+persist a gitignored dev key; explicit key in prod | |

### Token lifecycle

| Option | Description | Selected |
|--------|-------------|----------|
| Store metadata + detect on use | Persist expiry/issued-at; mark reconnect_required on auth error | ✓ |
| Proactive validation/refresh | Periodic debug_token/refresh before expiry | |
| Store metadata only | No active detection; rely on publish-time failure classification | |

### Schema scope

| Option | Description | Selected |
|--------|-------------|----------|
| Per (merchant, page) | Future-proofs multi-page/multi-merchant, ties to connected_channels | ✓ |
| Per page_id only | Simplest, mirrors current vault keying | |
| Single demo channel | Scoped to one seeded Facebook channel | |

**User's choice:** Encrypted SQLite column + single env-var key (fail-closed prod) + graceful dev fallback + store-and-detect lifecycle + per-(merchant,page) scope.
**Notes:** Headline gap was in-memory token loss on restart.

---

## Page Selection

### Selection flow

| Option | Description | Selected |
|--------|-------------|----------|
| Picker after OAuth | Callback returns Pages (no auto-commit); UI picker; second call commits + stores token | ✓ |
| Connections/settings picker | OAuth links account; select/change active Page later | |
| Auto-pick + confirm | Keep default but require explicit confirm/change before publish | |

### Page multiplicity

| Option | Description | Selected |
|--------|-------------|----------|
| Connect multiple, one active | Store all connected Pages, mark one active publish target | ✓ |
| Single active Page | Exactly one at a time; reconnect replaces | |
| Multiple, each publishable | Choose target per campaign | |

### Switch/disconnect scope

| Option | Description | Selected |
|--------|-------------|----------|
| Switch active + reconnect | Change active Page, re-run OAuth to refresh tokens | ✓ |
| Select-at-connect only | No switching; change = reconnect from scratch | |
| Full connect/switch/disconnect | Richest, but disconnect (ACCT-07) is Phase 5 | |

**User's choice:** Picker right after OAuth + connect-multiple-one-active + switch & reconnect (disconnect deferred to Phase 5).

---

## Media Validation

### Media scope

| Option | Description | Selected |
|--------|-------------|----------|
| Link + single image | Most common local post; simple Graph calls | ✓ |
| Link/text only | Add link preview, defer all image/video | |
| Link + single + multi-photo | Also multi-image via attached_media | |
| Include video | Add /videos upload flow | |

### Validation depth

| Option | Description | Selected |
|--------|-------------|----------|
| Facebook spec checks | File type/size + server-accessibility; clear pre-job errors | ✓ |
| Basic presence/type only | Confirm asset exists + allowed type | |
| Strict full validation | Also dimensions/aspect ratio/resolution | |

### Media delivery

| Option | Description | Selected |
|--------|-------------|----------|
| By public URL | Pass server-hosted asset URL to Graph /photos | ✓ |
| Upload bytes | Multipart upload for non-public assets | |
| You decide | Let planner pick based on asset serving | |

**User's choice:** Link + single image, Facebook spec validation pre-job, deliver by public URL.

---

## the agent's Discretion

- Capability & permission health (ACCT-03): user chose not to deep-dive; mechanism/timing/UI left to the planner, which can infer from existing `facebook_publisher.py` failure classification.
- Exact tokens-table schema, crypto library choice, Graph media endpoint orchestration, and Meta app-review evidence depth.

## Deferred Ideas

- Multi-photo and video Facebook publishing.
- Proactive token validation/refresh before expiry.
- Full account disconnect (ACCT-07) — Phase 5.
- Manual fallback package lifecycle (STATUS-03/04/05) — Phase 6.
- Per-campaign Page targeting.
- Envelope encryption / KMS/Vault integration.
