# 04-01 Summary — Token Encryption Foundation

**One-liner:** Introduced the first third-party Python dependency (`cryptography==49.0.0`) and a Fernet encryption boundary module for Facebook Page token persistence.

## What Was Built

- `backend/requirements.txt` — pins `cryptography==49.0.0` (first third-party Python backend dep).
- `backend/app/token_crypto.py` — `encrypt_secret`, `decrypt_secret`, `resolve_key`, `is_production`, `encryption_available`, `emit_insecure_warning`, `generate_dev_key`, `TokenEncryptionError`.
- `backend/tests/test_facebook_token_store.py` — 9 tests covering round-trip, ciphertext inequality, production fail-closed, dev-no-key detection, and key generation.
- `README.md` — added "Backend Setup (Phase 4+)" section with token encryption dev docs.

## Key Decisions

- Fernet (`cryptography.fernet.Fernet`) for authenticated symmetric encryption.
- Key from env `LOCALPILOT_TOKEN_KEY`; production determined by `LOCALPILOT_ENV=production`.
- Fail-closed in production (raises `TokenEncryptionError`); dev callers branch on `encryption_available()` for the insecure fallback.

## Self-Check: PASSED

- 9/9 tests green (`python3 -m unittest backend.tests.test_facebook_token_store -v`).
- 10/10 existing Facebook/token tests still pass (no regressions).
- No key committed; README instructs env-only key management.
