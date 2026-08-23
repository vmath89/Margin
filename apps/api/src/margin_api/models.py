"""Persisted V0 domain objects and database-enforced local invariants."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from margin_api.database import Base

DocumentStatus = Literal["processing", "ready", "failed"]
SessionStatus = Literal["active", "ended"]
EpisodeStatus = Literal["active", "ended"]
BoundarySource = Literal["outline", "heading", "fallback"]


def _new_id() -> str:
    """Create application-owned stable identifiers without database-specific UUID support."""

    return str(uuid4())


class Document(Base):
    """One uploaded source PDF and its authoritative normalized reading state."""

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("status IN ('processing', 'ready', 'failed')", name="document_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    title: Mapped[str | None] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(500))
    document_type: Mapped[str | None] = mapped_column(String(100))
    document_map: Mapped[list[object]] = mapped_column(JSON, nullable=False, default=list)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(String(20), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_message: Mapped[str | None] = mapped_column(Text)
    current_paragraph_id: Mapped[str | None] = mapped_column(
        ForeignKey("paragraphs.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    sections: Mapped[list[Section]] = relationship(back_populates="document")
    reading_sessions: Mapped[list[ReadingSession]] = relationship(back_populates="document")


class Section(Base):
    """An ordered, flat section boundary within a document."""

    __tablename__ = "sections"
    __table_args__ = (
        CheckConstraint(
            "boundary_source IN ('outline', 'heading', 'fallback')", name="section_boundary_source"
        ),
        CheckConstraint(
            "end_page IS NULL OR start_page IS NULL OR end_page >= start_page",
            name="section_page_range",
        ),
        Index("uq_sections_document_order", "document_id", "order", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    boundary_source: Mapped[BoundarySource] = mapped_column(String(20), nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text)
    synopsis_prompt_version: Mapped[str | None] = mapped_column(String(100))
    synopsis_model_id: Mapped[str | None] = mapped_column(String(200))
    start_page: Mapped[int | None] = mapped_column(Integer)
    end_page: Mapped[int | None] = mapped_column(Integer)

    document: Mapped[Document] = relationship(back_populates="sections")
    paragraphs: Mapped[list[Paragraph]] = relationship(back_populates="section")


class Paragraph(Base):
    """A stable, ordered reading-position anchor within one section."""

    __tablename__ = "paragraphs"
    __table_args__ = (
        CheckConstraint(
            "end_page IS NULL OR start_page IS NULL OR end_page >= start_page",
            name="paragraph_page_range",
        ),
        Index("uq_paragraphs_section_order", "section_id", "order", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    section_id: Mapped[str] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_page: Mapped[int | None] = mapped_column(Integer)
    end_page: Mapped[int | None] = mapped_column(Integer)

    section: Mapped[Section] = relationship(back_populates="paragraphs")


class ReadingSession(Base):
    """A document's active or ended sequence of reading and conversations."""

    __tablename__ = "reading_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'ended')", name="reading_session_status"),
        Index(
            "uq_active_reading_session_per_document",
            "document_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[SessionStatus] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    document: Mapped[Document] = relationship(back_populates="reading_sessions")
    episodes: Mapped[list[ConversationEpisode]] = relationship(back_populates="reading_session")


class ConversationEpisode(Base):
    """An immutable paragraph anchor and ordered exchange sequence for one pause."""

    __tablename__ = "conversation_episodes"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'ended')", name="conversation_episode_status"),
        Index("uq_episodes_session_order", "reading_session_id", "session_order", unique=True),
        Index(
            "uq_active_episode_per_session",
            "reading_session_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    reading_session_id: Mapped[str] = mapped_column(
        ForeignKey("reading_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_order: Mapped[int] = mapped_column(Integer, nullable=False)
    anchored_paragraph_id: Mapped[str] = mapped_column(
        ForeignKey("paragraphs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[EpisodeStatus] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reading_session: Mapped[ReadingSession] = relationship(back_populates="episodes")
    interactions: Mapped[list[Interaction]] = relationship(back_populates="episode")


class Interaction(Base):
    """One transcript-answer turn in a conversational episode."""

    __tablename__ = "interactions"
    __table_args__ = (
        Index("uq_interactions_episode_turn", "episode_id", "turn_order", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    episode_id: Mapped[str] = mapped_column(
        ForeignKey("conversation_episodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    turn_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    context_scope: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)
    openrouter_model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    episode: Mapped[ConversationEpisode] = relationship(back_populates="interactions")
