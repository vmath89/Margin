"""Persistence coverage for the V0 document and conversation schema."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from margin_api.database import create_database_engine


def _migrate_database(tmp_path: Path) -> tuple[str, object]:
    database_url = f"sqlite:///{tmp_path / 'domain.db'}"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    return database_url, config


def _insert_document_hierarchy(connection: object) -> None:
    connection.execute(
        text(
            "INSERT INTO documents (id, document_map, source_path, status) "
            "VALUES ('document-1', '[]', 'uploads/document.pdf', 'ready')"
        )
    )
    connection.execute(
        text(
            'INSERT INTO sections (id, document_id, "order", title, boundary_source, '
            "start_page, end_page) "
            "VALUES ('section-1', 'document-1', 1, 'Chapter one', 'outline', 1, 4)"
        )
    )
    connection.execute(
        text(
            'INSERT INTO paragraphs (id, section_id, "order", text, start_page, end_page) '
            "VALUES ('paragraph-1', 'section-1', 1, 'First paragraph.', 1, 1)"
        )
    )
    connection.execute(
        text("UPDATE documents SET current_paragraph_id = 'paragraph-1' WHERE id = 'document-1'")
    )


def test_domain_schema_orders_members_and_anchors_state(tmp_path: Path) -> None:
    database_url, _ = _migrate_database(tmp_path)
    engine = create_database_engine(database_url)

    with engine.begin() as connection:
        _insert_document_hierarchy(connection)
        connection.execute(
            text(
                "INSERT INTO reading_sessions (id, document_id, status) "
                "VALUES ('session-1', 'document-1', 'active')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO conversation_episodes "
                "(id, reading_session_id, session_order, anchored_paragraph_id, status) "
                "VALUES ('episode-1', 'session-1', 1, 'paragraph-1', 'active')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO interactions "
                "(id, episode_id, turn_order, question_transcript, answer_text, context_scope, "
                "prompt_version, openrouter_model_id) VALUES "
                "('interaction-1', 'episode-1', 1, 'What does this mean?', 'An explanation.', "
                "'local', 'v1', 'openai/gpt-5.6-sol')"
            )
        )

        row = connection.execute(
            text(
                "SELECT d.current_paragraph_id, e.session_order, i.turn_order "
                "FROM documents d "
                "JOIN reading_sessions s ON s.document_id = d.id "
                "JOIN conversation_episodes e ON e.reading_session_id = s.id "
                "JOIN interactions i ON i.episode_id = e.id"
            )
        ).one()
        assert row == ("paragraph-1", 1, 1)


def test_domain_schema_rejects_duplicate_orders_and_active_rows(tmp_path: Path) -> None:
    database_url, _ = _migrate_database(tmp_path)
    engine = create_database_engine(database_url)

    with engine.begin() as connection:
        _insert_document_hierarchy(connection)
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    'INSERT INTO sections (id, document_id, "order", title, boundary_source) '
                    "VALUES ('section-duplicate', 'document-1', 1, 'Duplicate', 'heading')"
                )
            )

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO reading_sessions (id, document_id, status) "
                "VALUES ('session-1', 'document-1', 'active')"
            )
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO reading_sessions (id, document_id, status) "
                    "VALUES ('session-2', 'document-1', 'active')"
                )
            )

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE reading_sessions SET status = 'ended' WHERE id = 'session-1'")
        )
        connection.execute(
            text(
                "INSERT INTO reading_sessions (id, document_id, status) "
                "VALUES ('session-2', 'document-1', 'active')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO conversation_episodes "
                "(id, reading_session_id, session_order, anchored_paragraph_id, status) "
                "VALUES ('episode-1', 'session-2', 1, 'paragraph-1', 'active')"
            )
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO conversation_episodes "
                    "(id, reading_session_id, session_order, anchored_paragraph_id, status) "
                    "VALUES ('episode-2', 'session-2', 2, 'paragraph-1', 'active')"
                )
            )


def test_domain_schema_rejects_invalid_foreign_keys_and_statuses(tmp_path: Path) -> None:
    database_url, _ = _migrate_database(tmp_path)
    engine = create_database_engine(database_url)

    with engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    'INSERT INTO sections (id, document_id, "order", title, boundary_source) '
                    "VALUES ('section-1', 'missing-document', 1, 'Bad', 'outline')"
                )
            )
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO documents (id, document_map, source_path, status) "
                    "VALUES ('document-1', '[]', 'uploads/document.pdf', 'unknown')"
                )
            )


def test_domain_migration_rolls_back_to_the_initial_revision(tmp_path: Path) -> None:
    _, config = _migrate_database(tmp_path)

    command.downgrade(config, "20260823_01")

    engine = create_engine(config.get_main_option("sqlalchemy.url"))
    assert "documents" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "20260823_01"
        )
