"""Entry point 1: create the database, its tables and the sign-in accounts. Safe to re-run."""

from access.password_security import create_password_hash, create_password_salt
from config import config
from persistence.database import (
    create_all_tables,
    create_database_directory,
    engine,
    open_database_session,
)
from persistence.repository import insert_user_account

if __name__ == "__main__":
    directory = create_database_directory(str(config.DATABASE_DIRECTORY))
    print("Database directory ready: " + directory)
    print("Database file: " + config.APPLICATION_DATABASE_FILE)

    table_names = create_all_tables(engine)
    print("Tables available: " + str(sorted(table_names)))
    print("Table count: " + str(len(table_names)))

    session = open_database_session()
    try:
        for seed_account in config.SEED_USER_ACCOUNTS:
            if seed_account["role"] not in config.ROLE_OPTIONS:
                raise ValueError(
                    "Account " + seed_account["username"] + " has role " + repr(seed_account["role"])
                    + ", which is not one of " + str(config.ROLE_OPTIONS)
                )
            # Each account gets its own salt. An account that already exists is left
            # untouched by insert_user_account, so a second run signs nobody out.
            password_salt = create_password_salt()
            insert_user_account(session, {
                "username": seed_account["username"],
                "display_name": seed_account["display_name"],
                "role": seed_account["role"],
                "password_hash": create_password_hash(seed_account["password"], password_salt),
                "password_salt": password_salt,
            })
    finally:
        session.close()

    print("Accounts you can sign in with:")
    for seed_account in config.SEED_USER_ACCOUNTS:
        print("   " + seed_account["username"].ljust(10) + seed_account["role"].ljust(13)
              + "password: " + seed_account["password"])
