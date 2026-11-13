"""The single connection to the application database, its sessions, and table creation."""

import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, sessionmaker

from config import config

DATABASE_URL = config.APPLICATION_DATABASE_URL

# The API serves requests on several threads, so SQLite must allow a connection
# to be used from a thread other than the one that opened it.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def get_database_session():
    """Lend one session to one web request and always close it afterwards."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def open_database_session():
    """A session for scripts and workflow nodes; the caller closes it."""
    return SessionLocal()


def create_database_directory(directory_path):
    """Create the database folder (and parents) if missing; return the path."""
    os.makedirs(directory_path, exist_ok=True)
    return directory_path


def create_all_tables(database_engine):
    """Create every table in persistence/models.py on database_engine and list what exists."""
    # Imported here, not at the top, because models.py imports Base from this module.
    from persistence import models  # noqa: F401

    Base.metadata.create_all(database_engine)
    return inspect(database_engine).get_table_names()
