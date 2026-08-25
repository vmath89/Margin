from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select

from margin_api import document_uploads
from margin_api.config import get_settings
from margin_api.database import create_session_factory
from margin_api.document_uploads import create_processing_document, process_document
from margin_api.errors import ApiError
from margin_api.main import app
from margin_api.models import Document, Paragraph, Section


def test_selected_pdf_publishes_one_complete_ordered_hierarchy(tmp_path: Path) -> None:
    factory = _factory(tmp_path)
    source = (Path(__file__).parent / "fixtures" / "constitution.pdf").read_bytes()

    document = create_processing_document(factory, tmp_path / "data", source)
    process_document(factory, document.id)

    with factory() as session:
        persisted = session.get(Document, document.id)
        assert persisted is not None
        assert persisted.status == "ready"
        assert persisted.current_paragraph_id is not None
        sections = session.scalars(
            select(Section).where(Section.document_id == document.id).order_by(Section.order)
        ).all()
        paragraphs = session.scalars(
            select(Paragraph)
            .join(Section)
            .where(Section.document_id == document.id)
            .order_by(Paragraph.order)
        ).all()
        assert sections and paragraphs
        assert [paragraph.order for paragraph in paragraphs] == list(range(1, len(paragraphs) + 1))
        assert persisted.current_paragraph_id == paragraphs[0].id
        assert persisted.document_map


def test_processing_failure_leaves_no_authoritative_derived_rows(tmp_path: Path) -> None:
    factory = _factory(tmp_path)
    document = create_processing_document(factory, tmp_path / "data", b"%PDF-1.7 unsupported")

    process_document(factory, document.id)

    with factory() as session:
        persisted = session.get(Document, document.id)
        assert persisted is not None
        assert persisted.status == "failed"
        assert persisted.current_paragraph_id is None
        assert persisted.document_map == []
        assert session.scalar(select(func.count()).select_from(Section)) == 0
        assert session.scalar(select(func.count()).select_from(Paragraph)) == 0
        assert str(tmp_path) not in (persisted.failure_message or "")


def test_publication_failure_leaves_document_retryable_without_derived_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory = _factory(tmp_path)
    source = (Path(__file__).parent / "fixtures" / "constitution.pdf").read_bytes()
    document = create_processing_document(factory, tmp_path / "data", source)

    def fail_publication(*_: object) -> None:
        raise RuntimeError("database write failed")

    monkeypatch.setattr(document_uploads, "_publish_processed_document", fail_publication)
    process_document(factory, document.id)

    with factory() as session:
        persisted = session.get(Document, document.id)
        assert persisted is not None
        assert persisted.status == "failed"
        assert persisted.failure_code == "document_publication_failed"
        assert persisted.failure_message == "The prepared PDF could not be saved. Please try again."
        assert persisted.current_paragraph_id is None
        assert persisted.document_map == []
        assert session.scalar(select(func.count()).select_from(Section)) == 0
        assert session.scalar(select(func.count()).select_from(Paragraph)) == 0


def test_invalid_upload_is_rejected_before_a_document_is_created(tmp_path: Path) -> None:
    factory = _factory(tmp_path)

    with pytest.raises(ApiError, match="Upload the supported PDF"):
        create_processing_document(factory, tmp_path / "data", b"not a pdf")

    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_upload_api_returns_a_safe_processing_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "api.db"
    _factory(tmp_path, database_path)
    monkeypatch.setenv("MARGIN_DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("MARGIN_DATA_ROOT", str(tmp_path / "data"))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents",
                files={"file": ("notes.txt", b"not a pdf", "application/pdf")},
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 415
    assert response.json() == {
        "code": "unsupported_upload",
        "message": "Upload the supported PDF file.",
        "retryable": False,
    }
    assert str(tmp_path) not in response.text


def test_upload_api_accepts_the_selected_multipart_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "api.db"
    _factory(tmp_path, database_path)
    monkeypatch.setenv("MARGIN_DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("MARGIN_DATA_ROOT", str(tmp_path / "data"))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            source = (Path(__file__).parent / "fixtures" / "constitution.pdf").read_bytes()
            response = client.post(
                "/api/documents",
                files={"file": ("constitution.pdf", source, "application/pdf")},
            )
            assert response.status_code == 202
            assert response.json()["status"] == "processing"
            status_response = client.get(f"/api/documents/{response.json()['id']}")
    finally:
        get_settings.cache_clear()

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "ready"
    assert status_response.json()["current_paragraph_id"] is not None


def test_upload_api_rejects_a_non_multipart_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "api.db"
    _factory(tmp_path, database_path)
    monkeypatch.setenv("MARGIN_DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("MARGIN_DATA_ROOT", str(tmp_path / "data"))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents", content=b"%PDF-1.7", headers={"content-type": "application/pdf"}
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 415
    assert response.json() == {
        "code": "multipart_upload_required",
        "message": "Upload the PDF as a multipart form.",
        "retryable": False,
    }


def test_startup_marks_interrupted_processing_document_as_retryable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "api.db"
    factory = _factory(tmp_path, database_path)
    document = create_processing_document(factory, tmp_path / "data", b"%PDF-1.7 interrupted")
    monkeypatch.setenv("MARGIN_DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("MARGIN_DATA_ROOT", str(tmp_path / "data"))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            assert client.get("/api/health").status_code == 200
    finally:
        get_settings.cache_clear()

    with factory() as session:
        persisted = session.get(Document, document.id)
        assert persisted is not None
        assert persisted.status == "failed"
        assert persisted.failure_code == "processing_interrupted"
        assert (
            persisted.failure_message == "Document preparation was interrupted. Please try again."
        )


def _factory(tmp_path: Path, database_path: Path | None = None):
    engine = create_engine(f"sqlite:///{database_path or tmp_path / 'margin.db'}")
    from margin_api.database import Base

    Base.metadata.create_all(engine)
    return create_session_factory(engine)
