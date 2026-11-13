"""Turns passwords into safe stored values, checks typed passwords, and issues session tokens.

The only place a typed password is ever handled.
"""

import hashlib
import hmac
import secrets

from config import config


def create_password_salt():
    """A fresh random salt, written as lower-case hex."""
    return secrets.token_hex(config.PASSWORD_SALT_BYTES)


def create_password_hash(plain_password, password_salt):
    """PBKDF2 over the UTF-8 password with the salt's raw bytes, as lower-case hex."""
    derived = hashlib.pbkdf2_hmac(
        config.PASSWORD_HASH_ALGORITHM,
        plain_password.encode("utf-8"),
        bytes.fromhex(password_salt),
        config.PASSWORD_HASH_ROUNDS,
    )
    return derived.hex()


def verify_password_matches(plain_password, stored_hash, stored_salt):
    """Hash the typed password the same way and compare in constant time."""
    if not plain_password:
        return False
    candidate = create_password_hash(plain_password, stored_salt)
    return hmac.compare_digest(candidate, stored_hash)


def create_session_token():
    """A fresh unguessable session token, written as lower-case hex."""
    return secrets.token_hex(config.SESSION_TOKEN_BYTES)
