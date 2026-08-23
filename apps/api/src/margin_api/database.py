"""SQLite engine and session configuration for Margin's single backend writer."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from margin_api.config import Settings


class Base(DeclarativeBase):
    """Base for the persisted domain models introduced by later tickets."""


def _sqlite_database_path(url: URL) -> Path | None:
    """Return a filesystem SQLite path, excluding in-memory and URI databases."""

    database = url.database
    if url.get_backend_name() != "sqlite" or database in {None, ":memory:"}:
        return None
    assert database is not None
    if database.startswith("file:"):
        return None
    return Path(database)


def create_database_engine(database_url: str, *, echo: bool = False) -> Engine:
    """Create a SQLite engine with foreign keys and WAL configured when applicable."""

    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        raise ValueError("Margin V0 supports SQLite databases only.")
    database_path = _sqlite_database_path(url)
    if database_path is not None:
        database_path.parent.mkdir(parents=True, exist_ok=True)

    configured_engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        echo=echo,
    )

    @event.listens_for(configured_engine, "connect")
    def configure_sqlite_connection(dbapi_connection: sqlite3.Connection, _: object) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            if database_path is not None:
                cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()

    return configured_engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Build the explicit session factory used by small application query functions."""

    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Commit one short database unit of work, rolling it back if it fails.

    Callers must complete network or other slow external operations before entering this scope.
    """

    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_session_factory_from_settings(settings: Settings) -> sessionmaker[Session]:
    """Create the configured database session factory for application startup."""

    engine = create_database_engine(settings.database_url, echo=settings.database_echo)
    return create_session_factory(engine)
