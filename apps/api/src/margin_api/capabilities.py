"""Small application-owned boundary for Margin's three model capabilities.

The production OpenRouter client will implement these operations in a later ticket.  Keeping the
requests and failures here makes service tests independent of any provider SDK or network call.
"""

from __future__ import annotations

from base64 import b64decode
from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from margin_api.errors import ApiError


class TextScope(StrEnum):
    """The explicit context selected by application logic for a reasoning request."""

    LOCAL = "local"
    SECTION = "section"
    FULL_DOCUMENT = "full_document"
    LIMITED_DOCUMENT_WIDE = "limited_document_wide"


@dataclass(frozen=True)
class TextGenerationRequest:
    """An already-constructed reasoning prompt and its application-selected scope."""

    prompt: str
    scope: TextScope


@dataclass(frozen=True)
class TranscriptionRequest:
    """A browser recording submitted for transcription."""

    recording: bytes
    media_type: str


@dataclass(frozen=True)
class SpeechSynthesisRequest:
    """Authoritative stored text that should be rendered as disposable audio."""

    text: str


class CapabilityError(ApiError):
    """An expected provider-boundary failure with stable application semantics."""

    def __init__(self, *, code: str, message: str, retryable: bool) -> None:
        super().__init__(
            code=code,
            message=message,
            retryable=retryable,
            status_code=503 if retryable else 502,
        )


@dataclass(frozen=True)
class FailureResponse:
    """A deterministic failure returned by a fake operation."""

    code: str
    message: str
    retryable: bool

    def as_error(self) -> CapabilityError:
        return CapabilityError(code=self.code, message=self.message, retryable=self.retryable)


# A short, valid MP3 rendered from a fixed sine wave. The fake owns this value; it never contacts
# a speech provider. It is encoded as base64 to keep this application-owned binary fixture legible.
FAKE_MP3_BYTES = b64decode(
    "SUQzBAAAAAAAIlRTU0UAAAAOAAADTGF2ZjYzLjEuMTAwAAAAAAAAAAAAAAD/40jAAAAAAAAAAAAASW5mbwAAAA8AAAAEAAAFoABmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmaZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzP////////////////////////////////8AAAAATGF2YzYzLjEuAAAAAAAAAAAAAAAAJAJAAAAAAAAABaDBeHlcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/40jEADli/lABWhgBQDoBy75csuWgHRXTHWOoIkIgELkFyC8CDigixFToSy2ZZMsmXHbe8nOAgiRplV5xbJ6ep+/Z9dZ2YZqRamrJ14F3C8CDimjXJZnK3/cty3/jdvTmEAAAAShwARu56AAGBv9cOBgAAiIiAAABgYt3dwMDAAAQiIEAAADAwN3cOBgYAAACIgQAAAMDAxbuHAwMAAAAQiBAAAAwMDFu7gYsAAABERAggDAxbu7uLAABERERBbu7u7uIQAAAADDw8PDwAAAAADDw8PDwAAAAADDw8PDwAAAAADDw8PDwAAUkGArgVBgWYF4YHGCTGAyAY8Rir7QF/d+YG0B2mCSAwJgSYI8YKiDJP00mAV3/40jELUdDMigJn6gAP/rzCMwwAwRAHfNAEHADFvREZMowJ4BgNAXGLDCVgJzzAbwQMzjAy7MIZAzwNbWMDsU7A5NOwMqqoDWKkA1KtiBFsc0hpaJqXd4GLDOBm41gZsPYGGSIBk0lAZNKwGDBiBjYbmR8xMWSU+/rAxsPwMCiADE4mAxSLAAAuBhwOgYcEIBoOAwqFAMJhZFbJKdHf6+oBAJAwYDQMGA0B4CAwOBgMDgYG8oGAAGBgAAhswNhgbZf/f+3cOhBuELRRPQXDBqoV0NWiUR1CCw4iNFy/r/+vq+SJwc4vpk6SiKh0mSQxxMkVFIkCIFW8dGu746NIBbAJfT09PT0+eeeGGGHP3Xp6SkpKSUQw6DSGsMHSjKAmYj/40jEI0R0bnS13EgAQWZpswADAhBSTiwig652VuW5bluW/7/u4/j+P5DkYjEYjAbFYrFYrFYrFYrFAoFAoFAoFAoJBWjRo0aNGjRkiBAgQIECBAjRo0aNGjRo0CBAgQIECBAjRo0aNGjRo0CBAgQIECBAjRo0aNGjRo0CBAgQIECBAjRo0aNGjRo0CBAgQIECBAjRo0aNGjRo0CBAgQIECBAjRo0aNGjRo0CBAgQIECBAgQI0aNGjRo0aNAgQIECBAgQI0aNGjRo0aNAgQIECBAgQI0aNGjRo0aNAgQIECBAgQI0aNGjRo0aNAgQIECBAgQI0aNGjRo0aNAgQIEMK0af5/n+f5/nacp2XJclnLOWcs5XasKsMqZMZMZFZAMXeLb/40jEJDT8XmgQ0kbpRgQwADmQKmUSnK1noXmLeG5PGPHGLDAQCWhLkoOoqpiqCqlWFYczpnTOmdNecpynKBEEQRBEEQRBEMhUVCoVCoVCoVCoVIRSKRSKUKFChRIkSJEiRIkSqFChQoQFVZmZmZmZmVVVVVVZmZmZvqqql//s3/VUvl//qsx//P/+qzf8ZlVVVVVWZmZmZlVVVVVWZmZmZlVVVVVWZmZmZlVVVVVWZmZmZlVVVVVWZmZmYMCgpMQU1FNC4wqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqo="
)


class FakeCapabilities:
    """Deterministic in-process implementations of Margin's current capability operations.

    Each sequence is consumed in call order, which lets a test model a transient failure followed
    by success or a permanent failure without a mock framework or provider-specific behavior.
    """

    def __init__(
        self,
        *,
        text_by_scope: Mapping[TextScope, str] | None = None,
        transcription: str = "What does this passage mean?",
        speech: bytes = FAKE_MP3_BYTES,
        text_failures: Sequence[FailureResponse] = (),
        transcription_failures: Sequence[FailureResponse] = (),
        speech_failures: Sequence[FailureResponse] = (),
    ) -> None:
        self._text_by_scope = {
            TextScope.LOCAL: "Fake local-passage answer.",
            TextScope.SECTION: "Fake current-section answer.",
            TextScope.FULL_DOCUMENT: "Fake fitting full-document answer.",
            TextScope.LIMITED_DOCUMENT_WIDE: "Fake limited document-wide answer.",
        }
        if text_by_scope is not None:
            self._text_by_scope.update(text_by_scope)
        self._transcription = transcription
        self._speech = speech
        self._failures = {
            "generate_text": deque(text_failures),
            "transcribe": deque(transcription_failures),
            "synthesize": deque(speech_failures),
        }
        self.requests: dict[str, list[object]] = defaultdict(list)

    def generate_text(self, request: TextGenerationRequest) -> str:
        """Return the configured deterministic answer for the application-selected scope."""

        self.requests["generate_text"].append(request)
        self._raise_next_failure("generate_text")
        return self._text_by_scope[request.scope]

    def transcribe(self, request: TranscriptionRequest) -> str:
        """Return the configured deterministic transcript."""

        self.requests["transcribe"].append(request)
        self._raise_next_failure("transcribe")
        return self._transcription

    def synthesize(self, request: SpeechSynthesisRequest) -> bytes:
        """Return deterministic application-owned MP3 fixture bytes."""

        self.requests["synthesize"].append(request)
        self._raise_next_failure("synthesize")
        return self._speech

    def _raise_next_failure(self, operation: str) -> None:
        failures = self._failures[operation]
        if failures:
            raise failures.popleft().as_error()
