import os
import unittest
from unittest.mock import patch

from backend.app import token_crypto


def _generate_test_key():
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode("utf-8")


class TestTokenCrypto(unittest.TestCase):

    def setUp(self):
        self.test_key = _generate_test_key()
        self.env_patch = patch.dict(
            os.environ,
            {"LOCALPILOT_TOKEN_KEY": self.test_key},
            clear=False,
        )
        self.env_patch.start()
        os.environ.pop("LOCALPILOT_ENV", None)

    def tearDown(self):
        self.env_patch.stop()

    def test_round_trip(self):
        token = "EAAGm0PX4ZCpsBAKz1exampletoken"
        ciphertext = token_crypto.encrypt_secret(token)
        result = token_crypto.decrypt_secret(ciphertext)
        self.assertEqual(result, token)

    def test_ciphertext_not_equal_to_plaintext(self):
        token = "EAAGm0PX4ZCpsBAKz1exampletoken"
        ciphertext = token_crypto.encrypt_secret(token)
        self.assertNotEqual(ciphertext, token.encode("utf-8"))
        self.assertNotIn(token.encode("utf-8"), ciphertext)

    def test_prod_no_key_fails_closed_encrypt(self):
        with patch.dict(
            os.environ,
            {"LOCALPILOT_ENV": "production"},
            clear=False,
        ):
            os.environ.pop("LOCALPILOT_TOKEN_KEY", None)
            with self.assertRaises(token_crypto.TokenEncryptionError) as ctx:
                token_crypto.encrypt_secret("some-token")
            self.assertIn("production", str(ctx.exception))

    def test_prod_no_key_fails_closed_decrypt(self):
        ciphertext = token_crypto.encrypt_secret("some-token")
        with patch.dict(
            os.environ,
            {"LOCALPILOT_ENV": "production"},
            clear=False,
        ):
            os.environ.pop("LOCALPILOT_TOKEN_KEY", None)
            with self.assertRaises(token_crypto.TokenEncryptionError):
                token_crypto.decrypt_secret(ciphertext)

    def test_dev_no_key_encryption_not_available(self):
        os.environ.pop("LOCALPILOT_TOKEN_KEY", None)
        os.environ.pop("LOCALPILOT_ENV", None)
        self.assertFalse(token_crypto.encryption_available())

    def test_dev_no_key_encrypt_raises(self):
        os.environ.pop("LOCALPILOT_TOKEN_KEY", None)
        os.environ.pop("LOCALPILOT_ENV", None)
        with self.assertRaises(token_crypto.TokenEncryptionError):
            token_crypto.encrypt_secret("some-token")

    def test_encryption_available_with_key(self):
        self.assertTrue(token_crypto.encryption_available())

    def test_is_production(self):
        os.environ.pop("LOCALPILOT_ENV", None)
        self.assertFalse(token_crypto.is_production())
        with patch.dict(os.environ, {"LOCALPILOT_ENV": "production"}):
            self.assertTrue(token_crypto.is_production())

    def test_generate_dev_key(self):
        key = token_crypto.generate_dev_key()
        self.assertIsInstance(key, str)
        self.assertTrue(len(key) > 20)


if __name__ == "__main__":
    unittest.main()
