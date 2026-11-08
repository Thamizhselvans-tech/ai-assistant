"""Database engine, session management, and dependencies."""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings
from backend.app.database.base import Base

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Enforce foreign key constraints in SQLite
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables defined in models and apply lightweight SQLite schema migrations."""
    # Import models so Base metadata is populated
    import backend.app.models.user  # noqa: F401
    import backend.app.models.document  # noqa: F401
    import backend.app.models.chat  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Lightweight schema upgrade for SQLite
    if "sqlite" in settings.DATABASE_URL:
        with engine.connect() as conn:
            try:
                cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
                if cols and "is_admin" not in cols:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL")
                if cols and "role" not in cols:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user' NOT NULL")

                cm_cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(chat_messages)").fetchall()]
                if cm_cols and "language" not in cm_cols:
                    conn.exec_driver_sql("ALTER TABLE chat_messages ADD COLUMN language VARCHAR(20) DEFAULT NULL")
                conn.commit()
            except Exception:
                pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
