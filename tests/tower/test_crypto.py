"""Tests for tower.utils.crypto.

These exist primarily to pin the wire-format byte layout against the Rust
``crates/crypto`` implementation. The helper ``_rust_compatible_encrypt``
mirrors what that crate produces; a drift between the two would cause these
tests to fail and signal that callers need to update the Python side.
"""

from __future__ import annotations

import base64
import os

import pytest

pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tower.utils import crypto


def _rust_compatible_encrypt(public_key, plaintext: str) -> str:
    """Mirror of ``crates/crypto::encrypt`` for round-trip testing."""
    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext.encode("utf-8"), None)
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(encrypted_key + nonce + ciphertext).decode("utf-8")


class TestKeypair:
    def test_generate_keypair_returns_pem_public_key(self):
        priv, pem = crypto.generate_keypair()
        assert pem.startswith("-----BEGIN PUBLIC KEY-----")
        pub = serialization.load_pem_public_key(pem.encode("utf-8"))
        assert pub.key_size == 2048
        # private and public halves belong to the same key
        assert priv.public_key().public_numbers() == pub.public_numbers()


class TestDecrypt:
    def test_round_trip(self):
        priv, pem = crypto.generate_keypair()
        pub = serialization.load_pem_public_key(pem.encode("utf-8"))

        plaintext = "catalog_uri=https://example.com"
        blob = _rust_compatible_encrypt(pub, plaintext)
        assert crypto.decrypt(priv, blob) == plaintext

    def test_round_trip_unicode_and_long_payload(self):
        priv, pem = crypto.generate_keypair()
        pub = serialization.load_pem_public_key(pem.encode("utf-8"))

        plaintext = "ünîçodé " + ("x" * 10_000)
        blob = _rust_compatible_encrypt(pub, plaintext)
        assert crypto.decrypt(priv, blob) == plaintext

    def test_truncated_blob_raises(self):
        priv, _ = crypto.generate_keypair()
        with pytest.raises(crypto.CryptoError):
            crypto.decrypt(priv, base64.b64encode(b"too short").decode())

    def test_invalid_base64_raises(self):
        priv, _ = crypto.generate_keypair()
        with pytest.raises(crypto.CryptoError):
            crypto.decrypt(priv, "!!!not base64!!!")

    def test_wrong_key_raises(self):
        _, pem = crypto.generate_keypair()
        pub = serialization.load_pem_public_key(pem.encode("utf-8"))
        blob = _rust_compatible_encrypt(pub, "secret")

        other_priv, _ = crypto.generate_keypair()
        with pytest.raises(crypto.CryptoError):
            crypto.decrypt(other_priv, blob)


class TestLayoutConstants:
    def test_rsa_key_bytes_is_256(self):
        # 2048 bits / 8 = 256 bytes — encoded with the Rust side.
        assert crypto.RSA_KEY_BYTES == 256

    def test_nonce_bytes_is_12(self):
        # AES-GCM standard 96-bit nonce.
        assert crypto.AES_GCM_NONCE_BYTES == 12
