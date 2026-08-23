"""Add Margin's initial persisted V0 domain schema.

Revision ID: 20260823_02
Revises: 20260823_01
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260823_02"
down_revision: str | Sequence[str] | None = "20260823_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create ordered document, session, episode, and interaction state."""

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("author", sa.String(length=500), nullable=True),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("document_map", sa.JSON(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("current_paragraph_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('processing', 'ready', 'failed')", name="document_status"),
        sa.ForeignKeyConstraint(["current_paragraph_id"], ["paragraphs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_current_paragraph_id", "documents", ["current_paragraph_id"])
    op.create_table(
        "sections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("boundary_source", sa.String(length=20), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("synopsis_prompt_version", sa.String(length=100), nullable=True),
        sa.Column("synopsis_model_id", sa.String(length=200), nullable=True),
        sa.Column("start_page", sa.Integer(), nullable=True),
        sa.Column("end_page", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "boundary_source IN ('outline', 'heading', 'fallback')", name="section_boundary_source"
        ),
        sa.CheckConstraint(
            "end_page IS NULL OR start_page IS NULL OR end_page >= start_page",
            name="section_page_range",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sections_document_id", "sections", ["document_id"])
    op.create_index("uq_sections_document_order", "sections", ["document_id", "order"], unique=True)
    op.create_table(
        "paragraphs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("section_id", sa.String(length=36), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_page", sa.Integer(), nullable=True),
        sa.Column("end_page", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "end_page IS NULL OR start_page IS NULL OR end_page >= start_page",
            name="paragraph_page_range",
        ),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paragraphs_section_id", "paragraphs", ["section_id"])
    op.create_index(
        "uq_paragraphs_section_order", "paragraphs", ["section_id", "order"], unique=True
    )
    op.create_table(
        "reading_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('active', 'ended')", name="reading_session_status"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reading_sessions_document_id", "reading_sessions", ["document_id"])
    op.create_index(
        "uq_active_reading_session_per_document",
        "reading_sessions",
        ["document_id"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "conversation_episodes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("reading_session_id", sa.String(length=36), nullable=False),
        sa.Column("session_order", sa.Integer(), nullable=False),
        sa.Column("anchored_paragraph_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('active', 'ended')", name="conversation_episode_status"),
        sa.ForeignKeyConstraint(["anchored_paragraph_id"], ["paragraphs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["reading_session_id"], ["reading_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_episodes_anchored_paragraph_id",
        "conversation_episodes",
        ["anchored_paragraph_id"],
    )
    op.create_index(
        "ix_conversation_episodes_reading_session_id",
        "conversation_episodes",
        ["reading_session_id"],
    )
    op.create_index(
        "uq_episodes_session_order",
        "conversation_episodes",
        ["reading_session_id", "session_order"],
        unique=True,
    )
    op.create_index(
        "uq_active_episode_per_session",
        "conversation_episodes",
        ["reading_session_id"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "interactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("episode_id", sa.String(length=36), nullable=False),
        sa.Column("turn_order", sa.Integer(), nullable=False),
        sa.Column("question_transcript", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("context_scope", sa.String(length=50), nullable=False),
        sa.Column("prompt_version", sa.String(length=100), nullable=False),
        sa.Column("openrouter_model_id", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["episode_id"], ["conversation_episodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interactions_episode_id", "interactions", ["episode_id"])
    op.create_index(
        "uq_interactions_episode_turn", "interactions", ["episode_id", "turn_order"], unique=True
    )


def downgrade() -> None:
    """Remove all domain tables while retaining Alembic's initial revision."""

    op.drop_index("uq_interactions_episode_turn", table_name="interactions")
    op.drop_index("ix_interactions_episode_id", table_name="interactions")
    op.drop_table("interactions")
    op.drop_index("uq_active_episode_per_session", table_name="conversation_episodes")
    op.drop_index("uq_episodes_session_order", table_name="conversation_episodes")
    op.drop_index("ix_conversation_episodes_reading_session_id", table_name="conversation_episodes")
    op.drop_index(
        "ix_conversation_episodes_anchored_paragraph_id", table_name="conversation_episodes"
    )
    op.drop_table("conversation_episodes")
    op.drop_index("uq_active_reading_session_per_document", table_name="reading_sessions")
    op.drop_index("ix_reading_sessions_document_id", table_name="reading_sessions")
    op.drop_table("reading_sessions")
    op.drop_index("uq_paragraphs_section_order", table_name="paragraphs")
    op.drop_index("ix_paragraphs_section_id", table_name="paragraphs")
    op.drop_table("paragraphs")
    op.drop_index("uq_sections_document_order", table_name="sections")
    op.drop_index("ix_sections_document_id", table_name="sections")
    op.drop_table("sections")
    op.drop_index("ix_documents_current_paragraph_id", table_name="documents")
    op.drop_table("documents")
