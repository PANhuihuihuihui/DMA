import os

_INSECURE_WARNING_EMITTED = False


class TokenEncryptionError(Exception):
    pass


def is_production():
    return os.environ.get("LOCALPILOT_ENV") == "production"


def resolve_key():
    raw = os.environ.get("LOCALPILOT_TOKEN_KEY", "").strip()
    return raw.encode("utf-8") if raw else None


def encryption_available():
    return resolve_key() is not None


def encrypt_secret(plaintext):
    key = resolve_key()
    if key is None:
        if is_production():
            raise TokenEncryptionError(
                "Refusing to handle tokens without LOCALPILOT_TOKEN_KEY in production"
            )
        raise TokenEncryptionError(
            "LOCALPILOT_TOKEN_KEY is not set — cannot encrypt"
        )
    from cryptography.fernet import Fernet

    return Fernet(key).encrypt(plaintext.encode("utf-8"))


def decrypt_secret(ciphertext):
    key = resolve_key()
    if key is None:
        if is_production():
            raise TokenEncryptionError(
                "Refusing to handle tokens without LOCALPILOT_TOKEN_KEY in production"
            )
        raise TokenEncryptionError(
            "LOCALPILOT_TOKEN_KEY is not set — cannot decrypt"
        )
    from cryptography.fernet import Fernet

    return Fernet(key).decrypt(ciphertext).decode("utf-8")


def emit_insecure_warning():
    global _INSECURE_WARNING_EMITTED
    if not _INSECURE_WARNING_EMITTED:
        _INSECURE_WARNING_EMITTED = True
        print("INSECURE: token encryption disabled — LOCALPILOT_TOKEN_KEY is not set")


def generate_dev_key():
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode("utf-8")
