"""Creates the database, its tables and the accounts people sign in with.

Safe to run again on a machine that already has a database.
"""
import os
import secrets

from config import config


def main():
    """Create the tables and seed the accounts. Returns how many accounts this run created."""
    from access.password_security import hash_password
    from persistence.database import database_engine, session_factory
    from persistence.models import Base
    from persistence.repository import fetch_user_account, insert_user_account
    from persistence.models import UserAccount

    os.makedirs(config.DATABASE_DIRECTORY, exist_ok=True)
    print(f"database: {config.APPLICATION_DATABASE_FILE}")
    Base.metadata.create_all(database_engine)
    print("tables: " + ", ".join(Base.metadata.tables))

    created = already = 0
    session = session_factory()
    try:
        for account in config.SEED_USER_ACCOUNTS:
            username = account["username"]
            if fetch_user_account(session, UserAccount.username == username) is not None:
                already += 1
                print(f"  account {username}: already present, left as it is")
                continue
            salt = secrets.token_hex(config.PASSWORD_SALT_BYTES)
            insert_user_account(session, {
                "username": username,
                "display_name": account["display_name"],
                "role": account["role"],
                "password_hash": hash_password(account["password"], salt),
                "password_salt": salt,
                "session_token": None,
            })
            created += 1
            print(f"  account {username}: created ({account['role']})")
    finally:
        session.close()
    print(f"accounts created: {created}, already present: {already}")
    return created


if __name__ == "__main__":
    main()
