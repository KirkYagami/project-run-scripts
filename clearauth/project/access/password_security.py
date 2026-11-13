import hashlib
from config import config as c


def hash_password(plain_password, password_salt):
    return hashlib.pbkdf2_hmac(
        c.PASSWORD_HASH_ALGORITHM,
        plain_password.encode(),
        password_salt.encode(),
        c.PASSWORD_HASH_ROUNDS,
    ).hex()
