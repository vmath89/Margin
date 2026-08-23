"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import BackgroundTasks, FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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
    if file.content_type != "application/pdf":
        raise ApiError(
            status_code=415,
            code="unsupported_upload",
            message="Upload the supported PDF file.",
            retryable=False,
        )
    source = await file.read()
    document = create_processing_document(
        request.app.state.session_factory, request.app.state.settings.data_root, source
    )
    background_tasks.add_task(process_document, request.app.state.session_factory, document.id)
    return document_response(document)


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def document_status(request: Request, document_id: str) -> DocumentResponse:
    return document_response(get_document(request.app.state.session_factory, document_id))


@app.post("/api/documents/{document_id}/retry", response_model=DocumentResponse, status_code=202)
async def retry_document_upload(
    request: Request, document_id: str, background_tasks: BackgroundTasks
) -> DocumentResponse:
    document = retry_document(request.app.state.session_factory, document_id)
    background_tasks.add_task(process_document, request.app.state.session_factory, document.id)
    return document_response(document)
