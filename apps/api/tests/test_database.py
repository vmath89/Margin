from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, create_engine, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from margin_api.database import create_database_engine


def test_sqlite_enforces_foreign_keys_and_uses_wal(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'margin.db'}")
    metadata = MetaData()
    parents = Table("parents", metadata, Column("id", Integer, primary_key=True))
    children = Table(
        "children",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey(parents.c.id), nullable=False),
    )

    metadata.create_all(engine)
    with engine.begin() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        assert connection.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"
        with pytest.raises(IntegrityError):
            connection.execute(children.insert().values(id=1, parent_id=999))


def test_migrations_apply_to_a_fresh_temporary_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "migrated.db"
    environment_database_path = tmp_path / "environment.db"
    monkeypatch.setenv("MARGIN_DATABASE_URL", f"sqlite:///{environment_database_path}")
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == "20260823_01"

    assert not environment_database_path.exists()


def test_migrations_use_the_api_database_setting_without_an_alembic_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "configured.db"
    monkeypatch.setenv("MARGIN_DATABASE_URL", f"sqlite:///{database_path}")
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == "20260823_01"
