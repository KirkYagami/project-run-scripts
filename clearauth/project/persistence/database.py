from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from config import config as c

database_engine = create_engine(
    c.APPLICATION_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30}
)


@event.listens_for(database_engine, "connect")
def _setup(connection, record):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")


session_factory = sessionmaker(bind=database_engine, expire_on_commit=False)
