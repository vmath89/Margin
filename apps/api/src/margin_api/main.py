"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import BackgroundTasks, FastAPI, File, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from margin_api.config import get_settings
from margin_api.database import create_session_factory_from_settings
from margin_api.document_uploads import (
    create_processing_document,
    fail_interrupted_processing_documents,
    get_document,
    process_document,
    retry_document,
)
from margin_api.errors import ApiError, ErrorResponse
from margin_api.models import Document, Paragraph, Section


class HealthResponse(BaseModel):
    status: Literal["ok"]


class DocumentResponse(BaseModel):
    id: str
    title: str | None
    author: str | None
    document_type: str | None
    document_map: list[object]
    status: Literal["processing", "ready", "failed"]
    failure_code: str | None
    failure_message: str | None
    current_paragraph_id: str | None


class ReviewParagraphResponse(BaseModel):
    id: str
    section_id: str
    order: int
    text: str
    start_page: int | None
    end_page: int | None


class ReviewSectionResponse(BaseModel):
    id: str
    order: int
    title: str
    boundary_source: Literal["outline", "heading", "fallback"]
    start_page: int | None
    end_page: int | None


class DocumentReviewResponse(BaseModel):
    id: str
    title: str | None
    document_map: list[object]
    sections: list[ReviewSectionResponse]
    paragraphs: list[ReviewParagraphResponse]
    offset: int
    limit: int
    total_paragraphs: int


def document_response(document: object) -> DocumentResponse:
    return DocumentResponse.model_validate(document, from_attributes=True)


def error_response(error: ErrorResponse, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error.model_dump())


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    application.state.settings = get_settings()
    application.state.session_factory = create_session_factory_from_settings(
        application.state.settings
    )
    fail_interrupted_processing_documents(application.state.session_factory)
    yield


app = FastAPI(title="Margin API", version="0.1.0", lifespan=lifespan)


@app.exception_handler(ApiError)
async def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
    return error_response(
        ErrorResponse(code=exc.code, message=exc.message, retryable=exc.retryable),
        exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, _exc: RequestValidationError) -> JSONResponse:
    if request.url.path == "/api/documents" and not request.headers.get(
        "content-type", ""
    ).startswith("multipart/form-data"):
        return error_response(
            ErrorResponse(
                code="multipart_upload_required",
                message="Upload the PDF as a multipart form.",
                retryable=False,
            ),
            415,
        )
    return error_response(
        ErrorResponse(
            code="request_validation_error",
            message="The request is invalid.",
            retryable=False,
        ),
        422,
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == 404 else "http_error"
    message = "The requested resource was not found." if exc.status_code == 404 else str(exc.detail)
    return error_response(
        ErrorResponse(code=code, message=message, retryable=False), exc.status_code
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
    return error_response(
        ErrorResponse(
            code="internal_server_error",
            message="The server encountered an unexpected error.",
            retryable=True,
        ),
        500,
    )


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/documents", response_model=DocumentResponse, status_code=202)
async def upload_document(
    request: Request, background_tasks: BackgroundTasks, file: Annotated[UploadFile, File()]
) -> DocumentResponse:
    source = await file.read()
    document = create_processing_document(
        request.app.state.session_factory, request.app.state.settings.data_root, source
    )
    background_tasks.add_task(
        process_document,
        request.app.state.session_factory,
        document.id,
        max_document_characters=request.app.state.settings.max_extracted_document_characters,
    )
    return document_response(document)


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def document_status(request: Request, document_id: str) -> DocumentResponse:
    return document_response(get_document(request.app.state.session_factory, document_id))


@app.get("/api/documents/{document_id}/review", response_model=DocumentReviewResponse)
async def review_document(
    request: Request,
    document_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=250),
) -> DocumentReviewResponse:
    with request.app.state.session_factory() as session:
        document = session.get(Document, document_id)
        if document is None:
            raise ApiError(
                code="document_not_found",
                message="The document was not found.",
                retryable=False,
                status_code=404,
            )
        if document.status != "ready":
            raise ApiError(
                code="document_not_ready",
                message="The document is still being prepared and cannot be reviewed yet.",
                retryable=document.status == "processing",
                status_code=409,
            )
        sections = session.scalars(
            select(Section).where(Section.document_id == document_id).order_by(Section.order)
        ).all()
        paragraph_query = (
            select(Paragraph)
            .join(Section)
            .where(Section.document_id == document_id)
            .order_by(Paragraph.order)
        )
        total = session.scalar(
            select(func.count())
            .select_from(Paragraph)
            .join(Section)
            .where(Section.document_id == document_id)
        )
        paragraphs = session.scalars(paragraph_query.offset(offset).limit(limit)).all()
        return DocumentReviewResponse(
            id=document.id,
            title=document.title,
            document_map=document.document_map,
            sections=[
                ReviewSectionResponse.model_validate(section, from_attributes=True)
                for section in sections
            ],
            paragraphs=[
                ReviewParagraphResponse.model_validate(paragraph, from_attributes=True)
                for paragraph in paragraphs
            ],
            offset=offset,
            limit=limit,
            total_paragraphs=total,
        )


@app.post("/api/documents/{document_id}/retry", response_model=DocumentResponse, status_code=202)
async def retry_document_upload(
    request: Request, document_id: str, background_tasks: BackgroundTasks
) -> DocumentResponse:
    document = retry_document(request.app.state.session_factory, document_id)
    background_tasks.add_task(
        process_document,
        request.app.state.session_factory,
        document.id,
        max_document_characters=request.app.state.settings.max_extracted_document_characters,
    )
    return document_response(document)
