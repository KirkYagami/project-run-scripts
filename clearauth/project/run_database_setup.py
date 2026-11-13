from pathlib import Path
import secrets
from sqlalchemy import inspect
from config import config as c
from persistence.database import database_engine, session_factory
from persistence.models import Base, UserAccount
from persistence.repository import fetch_user_account, insert_user_account
from access.password_security import hash_password


def main():
    Path(c.DATABASE_DIRECTORY).mkdir(parents=True, exist_ok=True)
    inspector = inspect(database_engine)
    for name, table in Base.metadata.tables.items():
        if inspector.has_table(name):
            missing = set(table.columns.keys()) - {
                col["name"] for col in inspector.get_columns(name)
            }
            if missing:
                raise ValueError(
                    f"{name}: missing columns {sorted(missing)}; delete {c.APPLICATION_DATABASE_FILE} and {c.CHECKPOINT_DATABASE_FILE}"
                )
    Base.metadata.create_all(database_engine)
    created = 0
    with session_factory.begin() as session:
        for account in c.SEED_USER_ACCOUNTS:
            if fetch_user_account(session, UserAccount.username == account["username"]):
                continue
            salt = secrets.token_hex(c.PASSWORD_SALT_BYTES)
            insert_user_account(
                session,
                {k: v for k, v in account.items() if k != "password"}
                | dict(
                    password_hash=hash_password(account["password"], salt),
                    password_salt=salt,
                ),
            )
            created += 1
            print(
                "account created",
                account["username"],
                account["display_name"],
                account["role"],
            )
    print(
        "database:",
        c.APPLICATION_DATABASE_FILE,
        "tables:",
        ", ".join(Base.metadata.tables),
    )
    print(
        "accounts created:",
        created,
        "already present:",
        len(c.SEED_USER_ACCOUNTS) - created,
    )


if __name__ == "__main__":
    main()
