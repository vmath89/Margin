"""Application-owned errors and their stable public representation."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Stable JSON error body returned by the API."""

    code: str
    message: str
    retryable: bool


class ApiError(Exception):
    """An expected failure that can be represented safely to an API client."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        retryable: bool,
        status_code: int,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code


class ConfigurationError(ApiError):
    """A required backend-only setting is unavailable for an invoked feature."""

    def __init__(self, setting_name: str) -> None:
        super().__init__(
            code="configuration_error",
            message=f"The server is missing required configuration: {setting_name}.",
            retryable=False,
            status_code=503,
        )
