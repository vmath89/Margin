"""Focused coverage for deterministic model-capability fakes."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from margin_api.capabilities import (
    FAKE_MP3_BYTES,
    CapabilityError,
    FailureResponse,
    FakeCapabilities,
    SpeechSynthesisRequest,
    TextGenerationRequest,
    TextScope,
    TranscriptionRequest,
)
from margin_api.main import app


@pytest.mark.parametrize(
    ("scope", "expected"),
    [
        (TextScope.LOCAL, "Fake local-passage answer."),
        (TextScope.SECTION, "Fake current-section answer."),
        (TextScope.FULL_DOCUMENT, "Fake fitting full-document answer."),
        (TextScope.LIMITED_DOCUMENT_WIDE, "Fake limited document-wide answer."),
    ],
)
def test_text_fake_returns_a_deterministic_answer_for_each_application_scope(
    scope: TextScope, expected: str
) -> None:
    fake = FakeCapabilities()

    answer = fake.generate_text(TextGenerationRequest(prompt="assembled prompt", scope=scope))

    assert answer == expected
    assert fake.requests["generate_text"] == [
        TextGenerationRequest(prompt="assembled prompt", scope=scope)
    ]


def test_transcription_and_speech_fakes_return_application_owned_values() -> None:
    fake = FakeCapabilities(transcription="Explain the opening argument.")
    transcription_request = TranscriptionRequest(recording=b"webm", media_type="audio/webm")
    speech_request = SpeechSynthesisRequest(text="An explanation.")

    assert fake.transcribe(transcription_request) == "Explain the opening argument."
    assert fake.synthesize(speech_request) == FAKE_MP3_BYTES
    assert fake.requests["transcribe"] == [transcription_request]
    assert fake.requests["synthesize"] == [speech_request]


def test_fake_speech_fixture_is_a_decodable_mp3(tmp_path: Path) -> None:
    """Keep the fake audio usable by browsers, rather than checking only an MP3 header."""

    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        pytest.skip("ffprobe is required to verify the MP3 fixture")

    fixture = tmp_path / "fake-speech.mp3"
    fixture.write_bytes(FAKE_MP3_BYTES)
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=format_name,duration:stream=codec_name,codec_type",
            "-of",
            "json",
            str(fixture),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(result.stdout)

    assert metadata["format"]["format_name"] == "mp3"
    assert float(metadata["format"]["duration"]) > 0
    assert metadata["streams"] == [{"codec_name": "mp3", "codec_type": "audio"}]


def test_fake_can_model_a_retryable_failure_followed_by_success() -> None:
    fake = FakeCapabilities(
        transcription_failures=(
            FailureResponse(
                code="capability_unavailable",
                message="Transcription is temporarily unavailable.",
                retryable=True,
            ),
        )
    )
    request = TranscriptionRequest(recording=b"webm", media_type="audio/webm")

    with pytest.raises(CapabilityError) as raised:
        fake.transcribe(request)

    assert raised.value.code == "capability_unavailable"
    assert raised.value.retryable is True
    assert fake.transcribe(request) == "What does this passage mean?"


def test_fake_can_model_a_permanent_failure_for_each_operation() -> None:
    failure = FailureResponse(
        code="capability_rejected",
        message="The configured operation rejected this input.",
        retryable=False,
    )
    fake = FakeCapabilities(
        text_failures=(failure,),
        transcription_failures=(failure,),
        speech_failures=(failure,),
    )

    for invoke in (
        lambda: fake.generate_text(
            TextGenerationRequest(prompt="assembled prompt", scope=TextScope.LOCAL)
        ),
        lambda: fake.transcribe(TranscriptionRequest(recording=b"webm", media_type="audio/webm")),
        lambda: fake.synthesize(SpeechSynthesisRequest(text="An explanation.")),
    ):
        with pytest.raises(CapabilityError) as raised:
            invoke()
        assert (raised.value.code, raised.value.retryable) == ("capability_rejected", False)


def test_text_fake_allows_scope_specific_response_overrides() -> None:
    fake = FakeCapabilities(text_by_scope={TextScope.SECTION: "Configured section answer."})

    assert (
        fake.generate_text(TextGenerationRequest(prompt="section prompt", scope=TextScope.SECTION))
        == "Configured section answer."
    )


def test_capability_error_uses_the_stable_api_error_mapping() -> None:
    @app.get("/api/test-capability-error")
    async def raise_capability_error() -> None:
        raise CapabilityError(
            code="capability_rejected",
            message="The configured operation rejected this input.",
            retryable=False,
        )

    with TestClient(app) as client:
        response = client.get("/api/test-capability-error")

    assert response.status_code == 502
    assert response.json() == {
        "code": "capability_rejected",
        "message": "The configured operation rejected this input.",
        "retryable": False,
    }
