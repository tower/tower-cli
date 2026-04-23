"""Hybrid RSA + AES-GCM decryption for payloads from the Tower API.

Mirrors the Rust implementation in ``crates/crypto``: a random AES-256 key
encrypts the payload with GCM, and the AES key itself is wrapped with
RSA-OAEP-SHA256 using the caller's public key. The wire format is a
base64-encoded concatenation::

    [ RSA-OAEP(AES_KEY) | 12-byte GCM nonce | AES-GCM ciphertext ]

Callers generate an ephemeral keypair with :func:`generate_keypair`, send the
PEM-encoded public key to the Tower API, and then feed the re-encrypted
property values back into :func:`decrypt` to recover plaintext.

The ``cryptography`` package is imported lazily so importing this module is
cheap even when decryption is never invoked.
"""

from __future__ import annotations

import base64
from typing import Any, Tuple

# RSA-2048 wraps the AES key in exactly ``modulus_bits / 8`` bytes. The Tower
# server always emits 2048-bit-wrapped payloads today; if that changes, the
# layout in ``crates/crypto`` changes too and both sides need to be updated.
RSA_KEY_BYTES = 256
AES_GCM_NONCE_BYTES = 12


class CryptoError(Exception):
    """Raised on malformed or undecryptable payloads."""


def generate_keypair() -> Tuple[Any, str]:
    """Generate an ephemeral RSA-2048 keypair.

    Returns a ``(private_key, public_key_pem)`` tuple. The PEM string is what
    you hand to the Tower API; the private key stays in-process and is fed
    into :func:`decrypt`.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_key, pem.decode("utf-8")


def decrypt(private_key: Any, encrypted_value: str) -> str:
    """Decrypt a hybrid-encrypted blob to its UTF-8 plaintext.

    Raises :class:`CryptoError` if the blob is truncated or cannot be
    decrypted (wrong key, tampered ciphertext, etc.).
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    try:
        blob = base64.b64decode(encrypted_value)
    except (ValueError, TypeError) as exc:
        raise CryptoError(f"payload is not valid base64: {exc}") from exc

    if len(blob) < RSA_KEY_BYTES + AES_GCM_NONCE_BYTES:
        raise CryptoError("encrypted payload is truncated")

    encrypted_key = blob[:RSA_KEY_BYTES]
    nonce = blob[RSA_KEY_BYTES : RSA_KEY_BYTES + AES_GCM_NONCE_BYTES]
    ciphertext = blob[RSA_KEY_BYTES + AES_GCM_NONCE_BYTES :]

    try:
        aes_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        plaintext = AESGCM(aes_key).decrypt(nonce, ciphertext, associated_data=None)
    except Exception as exc:
        raise CryptoError(f"decryption failed: {exc}") from exc

    return plaintext.decode("utf-8")
