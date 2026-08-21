"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from margin_api.config import get_settings
from margin_api.errors import ApiError, ErrorResponse


class HealthResponse(BaseModel):
    status: Literal["ok"]


def error_response(error: ErrorResponse, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error.model_dump())


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    application.state.settings = get_settings()
    yield


app = FastAPI(title="Margin API", version="0.1.0", lifespan=lifespan)


@app.exception_handler(ApiError)
async def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
    return error_response(
        ErrorResponse(code=exc.code, message=exc.message, retryable=exc.retryable),
        exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, _exc: RequestValidationError) -> JSONResponse:
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
