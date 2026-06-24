import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch

from backend.app import facebook_token_vault, store, token_crypto


def _generate_test_key():
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode("utf-8")


FORBIDDEN_TERMS = ["EAAGm0PX4", "exampletoken", "fakepagetoken"]


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


class TestFacebookPageTokensStore(unittest.TestCase):

    def setUp(self):
        self.test_key = _generate_test_key()
        self.env_patch = patch.dict(
            os.environ,
            {"LOCALPILOT_TOKEN_KEY": self.test_key},
            clear=False,
        )
        self.env_patch.start()
        os.environ.pop("LOCALPILOT_ENV", None)
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.env_patch.stop()

    def test_upsert_stores_ciphertext_only(self):
        plaintext = "EAAGm0PX4ZCpsBAKz1exampletoken"
        ciphertext = token_crypto.encrypt_secret(plaintext)
        store.upsert_facebook_page_token(
            self.conn, store.DEMO_MERCHANT_ID, store.FACEBOOK_CHANNEL_ID,
            "12345", ciphertext, "sha256:abc123", status="active",
        )
        self.conn.commit()
        row = store.get_facebook_page_token_row(self.conn, "12345")
        self.assertIsNotNone(row)
        raw_dump = str(dict(row))
        for term in FORBIDDEN_TERMS:
            self.assertNotIn(term, raw_dump)
        recovered = token_crypto.decrypt_secret(row["ciphertext"])
        self.assertEqual(recovered, plaintext)

    def test_upsert_updates_in_place(self):
        ct1 = token_crypto.encrypt_secret("token-v1")
        ct2 = token_crypto.encrypt_secret("token-v2")
        store.upsert_facebook_page_token(
            self.conn, store.DEMO_MERCHANT_ID, store.FACEBOOK_CHANNEL_ID,
            "12345", ct1, "fp1",
        )
        store.upsert_facebook_page_token(
            self.conn, store.DEMO_MERCHANT_ID, store.FACEBOOK_CHANNEL_ID,
            "12345", ct2, "fp2",
        )
        self.conn.commit()
        rows = store.list_facebook_page_token_rows(self.conn)
        self.assertEqual(len(rows), 1)
        self.assertEqual(token_crypto.decrypt_secret(rows[0]["ciphertext"]), "token-v2")

    def test_set_active_page_single_active(self):
        for pid in ["111", "222", "333"]:
            ct = token_crypto.encrypt_secret(f"tok-{pid}")
            store.upsert_facebook_page_token(
                self.conn, store.DEMO_MERCHANT_ID, store.FACEBOOK_CHANNEL_ID,
                pid, ct, f"fp-{pid}",
            )
        store.set_active_facebook_page(self.conn, store.DEMO_MERCHANT_ID, "222")
        self.conn.commit()
        active = store.get_active_facebook_page_row(self.conn)
        self.assertIsNotNone(active)
        self.assertEqual(active["page_id"], "222")
        rows = store.list_facebook_page_token_rows(self.conn)
        active_count = sum(1 for r in rows if r["is_active"])
        self.assertEqual(active_count, 1)

    def test_mark_reconnect_required(self):
        ct = token_crypto.encrypt_secret("tok")
        store.upsert_facebook_page_token(
            self.conn, store.DEMO_MERCHANT_ID, store.FACEBOOK_CHANNEL_ID,
            "12345", ct, "fp1",
        )
        store.mark_facebook_page_reconnect_required(self.conn, "12345")
        self.conn.commit()
        row = store.get_facebook_page_token_row(self.conn, "12345")
        self.assertEqual(row["status"], "reconnect_required")

    def test_missing_page_returns_none(self):
        row = store.get_facebook_page_token_row(self.conn, "nonexistent")
        self.assertIsNone(row)


class TestFacebookTokenVault(unittest.TestCase):

    def setUp(self):
        self.test_key = _generate_test_key()
        self.env_patch = patch.dict(
            os.environ,
            {"LOCALPILOT_TOKEN_KEY": self.test_key},
            clear=False,
        )
        self.env_patch.start()
        os.environ.pop("LOCALPILOT_ENV", None)
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)
        facebook_token_vault.clear()

    def tearDown(self):
        self.conn.close()
        self.env_patch.stop()
        facebook_token_vault.clear()

    def test_vault_encrypted_round_trip(self):
        plaintext_token = "EAAGm0PX4ZCpsBAKz1fakepagetoken"
        facebook_token_vault.put_page_token(
            "12345", plaintext_token, {"name": "Test Page"}, conn=self.conn,
        )
        recovered = facebook_token_vault.get_page_token("12345", conn=self.conn)
        self.assertEqual(recovered, plaintext_token)
        row = store.get_facebook_page_token_row(self.conn, "12345")
        raw_dump = str(dict(row))
        for term in FORBIDDEN_TERMS:
            self.assertNotIn(term, raw_dump)

    def test_vault_dev_fallback_no_key(self):
        os.environ.pop("LOCALPILOT_TOKEN_KEY", None)
        self.assertFalse(token_crypto.encryption_available())
        facebook_token_vault.put_page_token("99999", "devtoken", {"name": "Dev"})
        recovered = facebook_token_vault.get_page_token("99999")
        self.assertEqual(recovered, "devtoken")
        row = store.get_facebook_page_token_row(self.conn, "99999")
        self.assertIsNone(row)

    def test_list_connected_pages_no_token_field(self):
        facebook_token_vault.put_page_token(
            "12345", "secrettoken", {"name": "P1"}, conn=self.conn,
        )
        pages = facebook_token_vault.list_connected_pages(conn=self.conn)
        self.assertTrue(len(pages) >= 1)
        for page in pages:
            page_str = str(page)
            self.assertNotIn("secrettoken", page_str)
            self.assertNotIn("token", page.keys() - {"connectedAt", "credentialFingerprint"})

    def test_mark_reconnect_required_through_vault(self):
        facebook_token_vault.put_page_token(
            "12345", "tok", {"name": "P"}, conn=self.conn,
        )
        facebook_token_vault.mark_reconnect_required("12345", conn=self.conn)
        row = store.get_facebook_page_token_row(self.conn, "12345")
        self.assertEqual(row["status"], "reconnect_required")

    def test_set_active_page_through_vault(self):
        for pid in ["111", "222"]:
            facebook_token_vault.put_page_token(pid, f"tok-{pid}", {}, conn=self.conn)
        facebook_token_vault.set_active_page("222", conn=self.conn)
        active = store.get_active_facebook_page_row(self.conn)
        self.assertIsNotNone(active)
        self.assertEqual(active["page_id"], "222")


if __name__ == "__main__":
    unittest.main()
