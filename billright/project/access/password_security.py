"""Turns a password and its salt into the form the database stores."""
import hashlib

from config import config


def hash_password(plain_password, password_salt):
    """Hash a password with its own salt, using the configured algorithm and rounds."""
    derived = hashlib.pbkdf2_hmac(config.PASSWORD_HASH_ALGORITHM,
                                  plain_password.encode("utf-8"),
                                  password_salt.encode("utf-8"),
                                  config.PASSWORD_HASH_ROUNDS)
    return derived.hex()
