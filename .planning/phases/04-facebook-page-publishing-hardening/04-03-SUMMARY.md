# 04-03 Summary — Encrypted SQLite Page-Token Store

**One-liner:** Replaced the in-memory `_PAGE_TOKENS` dict with durable, encrypted SQLite persistence wired through `token_boundary`, keeping the existing vault API backward-compatible.

## What Was Built

- `backend/app/store.py` — new `facebook_page_tokens` table (ciphertext BLOB, unique index on merchant/channel/page) + CRUD helpers: `upsert_facebook_page_token`, `get_facebook_page_token_row`, `list_facebook_page_token_rows`, `set_active_facebook_page`, `mark_facebook_page_reconnect_required`, `get_active_facebook_page_row`.
- `backend/app/facebook_token_vault.py` — rewritten to encrypt via `token_crypto.encrypt_secret` + persist via store helpers when a `conn` + key are available; falls back to in-memory dict with `INSECURE:` warning when no key is set in dev. Existing function names/signatures preserved with optional `conn`/`merchant_id`/`connected_channel_id`/`expires_at`/`issued_at` kwargs.
- `backend/tests/test_facebook_token_store.py` — expanded to 19 tests across 3 classes (TestTokenCrypto, TestFacebookPageTokensStore, TestFacebookTokenVault) covering encrypted round-trip, ciphertext-only DB storage, upsert-in-place, single-active invariant, reconnect_required, dev fallback, and list-no-token.

## Key Decisions

- D-01/D-02: ciphertext + `credential_fingerprint` stored, wired through `token_boundary.create_token_boundary`.
- D-05: dev fallback is in-memory + `emit_insecure_warning()` (once); vault checks `encryption_available()` before the DB path.
- D-06: `token_expires_at` + `issued_at` columns persisted; `status` column supports `active`/`reconnect_required`.
- D-07: keyed per `(merchant_id, connected_channel_id, page_id)`.

## Self-Check: PASSED

- 19/19 token tests green.
- 10/10 existing Facebook/token tests still pass (backward compatibility verified).
- Raw DB dump assertions confirm plaintext tokens never appear in any column.
