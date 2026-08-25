"""Upload and atomic persistence for Margin's single supported PDF."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from margin_api.errors import ApiError
from margin_api.models import Document, Paragraph, Section
from margin_api.pdf_processing import PdfProcessingError, ProcessedDocument, process_selected_pdf

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def create_processing_document(
    session_factory: sessionmaker[Session], data_root: Path, source: bytes
) -> Document:
    """Validate and save an upload before making its processing state observable."""

    _validate_pdf(source)
    document_id = str(uuid4())
    source_path = data_root / "documents" / document_id / "source.pdf"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = source_path.with_suffix(".uploading")
    try:
        temporary_path.write_bytes(source)
        os.replace(temporary_path, source_path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ApiError(
            status_code=500,
            code="upload_storage_failed",
            message="The PDF could not be stored. Please try again.",
            retryable=True,
        ) from error

    document = Document(id=document_id, source_path=str(source_path), status="processing")
    with session_factory.begin() as session:
        session.add(document)
    return document


def process_document(session_factory: sessionmaker[Session], document_id: str) -> None:
    """Process source text outside a transaction, then publish its hierarchy atomically."""

    with session_factory() as session:
        document = session.get(Document, document_id)
        if document is None or document.status != "processing":
            return
        source_path = Path(document.source_path)

    try:
        processed = process_selected_pdf(source_path)
    except PdfProcessingError as error:
        _mark_failed(session_factory, document_id, "pdf_processing_failed", str(error))
        return
    except Exception:
        _mark_failed(
            session_factory,
            document_id,
            "pdf_processing_failed",
            "The PDF could not be prepared. Please try again.",
        )
        return

    try:
        _publish_processed_document(session_factory, document_id, processed)
    except Exception:
        _mark_failed(
            session_factory,
            document_id,
            "document_publication_failed",
            "The prepared PDF could not be saved. Please try again.",
        )


def retry_document(session_factory: sessionmaker[Session], document_id: str) -> Document:
    """Move a failed document back to processing; the caller schedules work separately."""

    with session_factory.begin() as session:
        document = session.get(Document, document_id)
        if document is None:
            raise ApiError(
                status_code=404,
                code="document_not_found",
                message="The document was not found.",
                retryable=False,
            )
        if document.status != "failed":
            raise ApiError(
                status_code=409,
                code="document_not_retryable",
                message="Only a failed document can be retried.",
                retryable=False,
            )
        document.status = "processing"
        document.failure_code = None
        document.failure_message = None
    return document


def fail_interrupted_processing_documents(session_factory: sessionmaker[Session]) -> None:
    """Make processing interrupted by a backend restart explicitly retryable."""

    try:
        with session_factory() as session:
            document_ids = session.scalars(
                select(Document.id).where(Document.status == "processing")
            ).all()
    except OperationalError as error:
        if "no such table: documents" not in str(error).lower():
            raise
        return
    for document_id in document_ids:
        _mark_failed(
            session_factory,
            document_id,
            "processing_interrupted",
            "Document preparation was interrupted. Please try again.",
        )


def get_document(session_factory: sessionmaker[Session], document_id: str) -> Document:
    with session_factory() as session:
        document = session.get(Document, document_id)
        if document is None:
            raise ApiError(
                status_code=404,
                code="document_not_found",
                message="The document was not found.",
                retryable=False,
            )
        session.expunge(document)
        return document


def _publish_processed_document(
    session_factory: sessionmaker[Session], document_id: str, processed: ProcessedDocument
) -> None:
    """Replace all derived rows in one transaction and set the first reading position."""

    with session_factory.begin() as session:
        document = session.get(Document, document_id)
        if document is None or document.status != "processing":
            return
        document.current_paragraph_id = None
        section_ids = select(Section.id).where(Section.document_id == document_id)
        session.execute(delete(Paragraph).where(Paragraph.section_id.in_(section_ids)))
        session.execute(delete(Section).where(Section.document_id == document_id))

        document.title = processed.title
        document.author = processed.author
        document.document_type = "pdf"
        document.document_map = [
            {"order": entry.order, "title": entry.title, "omitted_sections": entry.omitted_sections}
            for entry in processed.document_map
        ]
        first_paragraph: Paragraph | None = None
        for source_section in processed.sections:
            section = Section(
                document_id=document.id,
                order=source_section.order,
                title=source_section.title,
                boundary_source=source_section.boundary_source,
                start_page=source_section.start_page,
                end_page=source_section.end_page,
            )
            session.add(section)
            session.flush()
            for source_paragraph in source_section.paragraphs:
                paragraph = Paragraph(
                    section_id=section.id,
                    order=source_paragraph.order,
                    text=source_paragraph.text,
                    start_page=source_paragraph.start_page,
                    end_page=source_paragraph.end_page,
                )
                session.add(paragraph)
                if first_paragraph is None:
                    first_paragraph = paragraph
        session.flush()
        if first_paragraph is None:
            raise RuntimeError("processed document contained no paragraphs")
        document.current_paragraph_id = first_paragraph.id
        document.status = "ready"
        document.failure_code = None
        document.failure_message = None


def _mark_failed(
    session_factory: sessionmaker[Session], document_id: str, code: str, message: str
) -> None:
    with session_factory.begin() as session:
        document = session.get(Document, document_id)
        if document is None:
            return
        document.current_paragraph_id = None
        section_ids = select(Section.id).where(Section.document_id == document_id)
        session.execute(delete(Paragraph).where(Paragraph.section_id.in_(section_ids)))
        session.execute(delete(Section).where(Section.document_id == document_id))
        document.document_map = []
        document.status = "failed"
        document.failure_code = code
        document.failure_message = message


def _validate_pdf(source: bytes) -> None:
    if not source:
        raise ApiError(
            status_code=400,
            code="empty_upload",
            message="Choose a PDF file to upload.",
            retryable=False,
        )
    if len(source) > MAX_UPLOAD_BYTES:
        raise ApiError(
            status_code=413,
            code="upload_too_large",
            message="The PDF is larger than the 50 MB limit.",
            retryable=False,
        )
    if not source.startswith(b"%PDF-"):
        raise ApiError(
            status_code=415,
            code="unsupported_upload",
            message="Upload the supported PDF file.",
            retryable=False,
        )
