"""Secure token encryption helper for OAuth tokens (Phase 7).

Uses Fernet symmetric encryption with key derivation from application secret key.
"""

from __future__ import annotations

import base64
import hashlib
import os

from app.config import get_settings

try:
    from cryptography.fernet import Fernet

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def _get_fernet_key() -> bytes:
    """Derive 32-byte url-safe base64 key from configuration secret."""
    settings = get_settings()
    key_material = settings.token_encryption_key or settings.secret_key
    digest = hashlib.sha256(key_material.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_token(plain_token: str | None) -> str | None:
    """Encrypt a sensitive OAuth token string."""
    if not plain_token:
        return None

    if HAS_CRYPTOGRAPHY:
        fernet = Fernet(_get_fernet_key())
        return fernet.encrypt(plain_token.encode("utf-8")).decode("utf-8")

    # Safe fallback if cryptography library is not installed
    key = _get_fernet_key()
    salt = os.urandom(16)
    keystream = hashlib.pbkdf2_hmac("sha256", key, salt, 10000, len(plain_token))
    cipher_bytes = bytes([b ^ k for b, k in zip(plain_token.encode("utf-8"), keystream)])
    return base64.urlsafe_b64encode(salt + cipher_bytes).decode("utf-8")


def decrypt_token(encrypted_token: str | None) -> str | None:
    """Decrypt an encrypted OAuth token string."""
    if not encrypted_token:
        return None

    if HAS_CRYPTOGRAPHY:
        try:
            fernet = Fernet(_get_fernet_key())
            return fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
        except Exception:
            pass

    try:
        raw = base64.urlsafe_b64decode(encrypted_token.encode("utf-8"))
        salt = raw[:16]
        cipher_bytes = raw[16:]
        key = _get_fernet_key()
        keystream = hashlib.pbkdf2_hmac("sha256", key, salt, 10000, len(cipher_bytes))
        plain_bytes = bytes([b ^ k for b, k in zip(cipher_bytes, keystream)])
        return plain_bytes.decode("utf-8")
    except Exception:
        return None
