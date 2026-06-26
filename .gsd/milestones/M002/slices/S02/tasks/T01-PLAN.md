---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T01: R003 verified: 19 tests prove Fernet encrypt/decrypt round-trip, ciphertext-not-plaintext, production fails-closed, vault encrypted storage, and reconnect marking

Run automated checks against token_crypto.py and facebook_token_vault.py to prove: (1) encrypt_secret/decrypt_secret round-trip works, (2) put_page_token stores encrypted data in SQLite, (3) get_page_token decrypts correctly, (4) missing LOCALPILOT_TOKEN_KEY fails closed. AiToEarn reference: their FacebookService uses accessToken exchange; our Fernet approach is stronger (encryption at rest).

## Inputs

- `backend/app/token_crypto.py`
- `backend/app/facebook_token_vault.py`
- `backend/app/store.py`

## Expected Output

- `backend/tests/test_token_crypto.py`

## Verification

python -m pytest backend/tests/test_token_crypto.py -v exits 0
