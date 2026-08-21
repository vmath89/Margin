#!/usr/bin/env python3
"""Reproduce the M1-T04 OpenRouter text-to-speech quality spike.

This is ticket-scoped spike code, not the production OpenRouter integration. Live
requests use only the Python standard library, read OPENROUTER_API_KEY from the
environment, and write generated audio and measurements below ignored ``var/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Optional


ENDPOINT = "https://openrouter.ai/api/v1/audio/speech"
DEFAULT_MODEL = "microsoft/mai-voice-2"
DEFAULT_VOICES = (
    "en-US-Harper:MAI-Voice-2",
    "en-US-Ethan:MAI-Voice-2",
    "en-US-Olivia:MAI-Voice-2",
)
SELECTED_VOICE = "en-US-Harper:MAI-Voice-2"
RESPONSE_FORMAT = "mp3"
SPEED = 1.0
STYLE: Optional[str] = None
STYLE_DEGREE: Optional[float] = None
TIMEOUT_SECONDS = 120.0
TRANSIENT_STATUSES = frozenset({429, 500, 502, 503, 524, 529})

COMPARISON_TEXT = (
    "The Constitution creates a bicameral legislature and requires a bill to pass "
    "both houses before it reaches the President. If the President returns it with "
    "objections, Article One, Section Seven allows each house to reconsider it; a "
    "two-thirds vote in both houses can still make it law. This deliberate sequence "
    "tests pacing, pauses, pronunciation, and the difference between tranquility, "
    "enumeration, and interpretation."
)

PASSAGE_TEXT = (
    "Every Bill which shall have passed the House of Representatives and the Senate, "
    "shall, before it become a Law, be presented to the President of the United States; "
    "If he approve he shall sign it, but if not he shall return it, with his Objections "
    "to that House in which it shall have originated, who shall enter the Objections at "
    "large on their Journal, and proceed to reconsider it. If after such Reconsideration "
    "two thirds of that House shall agree to pass the Bill, it shall be sent, together "
    "with the Objections, to the other House, by which it shall likewise be reconsidered, "
    "and if approved by two thirds of that House, it shall become a Law."
)

ANSWER_TEXT = (
    "This passage describes a sequence for turning a bill into law, and the sequence is "
    "the important part. First, the same proposal must pass both the House of "
    "Representatives and the Senate. That means one chamber cannot legislate for the "
    "whole country by itself. The two chambers have different memberships and electoral "
    "structures, so agreement between them is an initial check within Congress.\n\n"
    "Second, the bill goes to the President. Approval is expressed by signing it. If the "
    "President objects, the bill is returned to the chamber where it began, together with "
    "the objections. Notice that the text requires reasons to come back with the bill and "
    "requires those objections to be entered in the chamber's journal. The disagreement "
    "therefore becomes part of a visible constitutional process rather than simply ending "
    "the proposal.\n\n"
    "Third, a presidential objection is powerful but not final. The originating chamber "
    "may reconsider the bill. If two thirds agree to pass it again, the bill and the "
    "President's objections move to the other chamber. The other chamber must also "
    "reconsider it and reach the same two-thirds threshold. Only then can the bill become "
    "law despite the President's refusal to sign it. In everyday terms, the President can "
    "force Congress to pause, confront the objections, and demonstrate unusually broad "
    "support, but cannot permanently block a bill that commands that level of support in "
    "both chambers.\n\n"
    "The broader design can reasonably be interpreted as a system of checks and renewed "
    "deliberation. That is an interpretation of the procedure supplied here, not a claim "
    "about the private motives of every framer. The text itself establishes the actors, "
    "the order of decisions, the written objections, and the two-thirds votes. The idea "
    "that these steps encourage caution and broad agreement explains why the procedure "
    "matters, but it should remain clearly distinguished from the literal wording.\n\n"
    "For a simple illustration, imagine that both chambers pass a transportation bill. "
    "The President returns it because of one disputed provision. The House reviews those "
    "reasons and passes the same bill again by two thirds. The Senate then does the same. "
    "Under the process described in this passage, the bill becomes law. The transportation "
    "bill is invented for explanation; it is not an event described by the Constitution."
)


@dataclass(frozen=True)
class AudioMeasurement:
    name: str
    model: str
    voice: str
    input_characters: int
    response_format: str
    speed: float
    style: Optional[str]
    style_degree: Optional[float]
    cache_config_version: str
    attempts: int
    status: int
    content_type: str
    generation_id: Optional[str]
    latency_seconds: float
    bytes: int
    sha256: str
    codec: str
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    bit_rate_bps: int
    path: str


class SpeechRequestError(RuntimeError):
    def __init__(self, status: Optional[int], message: str) -> None:
        super().__init__(message)
        self.status = status

    @property
    def retryable(self) -> bool:
        return self.status is None or self.status in TRANSIENT_STATUSES


def cache_config_version(model: str, voice: str) -> str:
    """Hash every synthesis setting that can change generated audio bytes."""
    settings = {
        "contract": "openrouter-audio-speech-v1",
        "model": model,
        "voice": voice,
        "response_format": RESPONSE_FORMAT,
        "speed": SPEED,
        "provider": {"azure": {"style": STYLE, "styledegree": STYLE_DEGREE}},
    }
    canonical = json.dumps(settings, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def request_payload(text: str, model: str, voice: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": RESPONSE_FORMAT,
        "speed": SPEED,
    }
    if STYLE is not None:
        azure: dict[str, Any] = {"style": STYLE}
        if STYLE_DEGREE is not None:
            azure["styledegree"] = STYLE_DEGREE
        payload["provider"] = {"options": {"azure": azure}}
    return payload


def with_bounded_retry(
    operation: Callable[[], dict[str, Any]],
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[dict[str, Any], int]:
    """Run once, retrying exactly once only for the documented transient class."""
    attempts = 0
    while True:
        attempts += 1
        try:
            return operation(), attempts
        except SpeechRequestError as error:
            if attempts >= 2 or not error.retryable:
                raise
            sleep(1.0)


def post_speech(text: str, model: str, voice: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    body = json.dumps(request_payload(text, model, voice)).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Margin-M1-T04-Spike/1",
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            audio = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            generation_id = response.headers.get("X-Generation-Id")
    except urllib.error.HTTPError as error:
        safe_body = error.read().decode("utf-8", errors="replace")[:1000]
        raise SpeechRequestError(
            error.code, f"OpenRouter HTTP {error.code}: {safe_body}"
        ) from error
    except (TimeoutError, urllib.error.URLError) as error:
        raise SpeechRequestError(None, f"OpenRouter network error: {error}") from error
    latency = time.perf_counter() - started
    if status != 200:
        raise SpeechRequestError(status, f"unexpected OpenRouter HTTP {status}")
    if not content_type.lower().startswith("audio/mpeg"):
        raise SpeechRequestError(
            status, f"expected audio/mpeg, received {content_type!r}"
        )
    if not audio:
        raise SpeechRequestError(status, "OpenRouter returned empty audio")
    return {
        "audio": audio,
        "status": status,
        "content_type": content_type,
        "generation_id": generation_id,
        "latency_seconds": latency,
    }


def probe(path: Path) -> dict[str, Any]:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("missing required command: ffprobe")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate,channels,bit_rate:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return {
        "codec": stream["codec_name"],
        "duration_seconds": round(float(data["format"]["duration"]), 3),
        "sample_rate_hz": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "bit_rate_bps": int(stream["bit_rate"]),
    }


def synthesize_one(
    output_dir: Path, name: str, text: str, model: str, voice: str
) -> AudioMeasurement:
    response, attempts = with_bounded_retry(lambda: post_speech(text, model, voice))
    safe_voice = voice.replace(":", "_")
    path = output_dir / f"{name}--{safe_voice}.mp3"
    audio = response["audio"]
    path.write_bytes(audio)
    metadata = probe(path)
    if metadata["codec"] != "mp3":
        raise RuntimeError(f"{path} codec is {metadata['codec']!r}, expected mp3")
    return AudioMeasurement(
        name=name,
        model=model,
        voice=voice,
        input_characters=len(text),
        response_format=RESPONSE_FORMAT,
        speed=SPEED,
        style=STYLE,
        style_degree=STYLE_DEGREE,
        cache_config_version=cache_config_version(model, voice),
        attempts=attempts,
        status=response["status"],
        content_type=response["content_type"],
        generation_id=response["generation_id"],
        latency_seconds=round(response["latency_seconds"], 3),
        bytes=len(audio),
        sha256=hashlib.sha256(audio).hexdigest(),
        path=str(path),
        **metadata,
    )


def synthesize(output_dir: Path, model: str, voices: tuple[str, ...]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    measurements: list[AudioMeasurement] = []
    for voice in voices:
        measurements.append(
            synthesize_one(output_dir, "comparison", COMPARISON_TEXT, model, voice)
        )
    measurements.append(
        synthesize_one(output_dir, "source-passage", PASSAGE_TEXT, model, SELECTED_VOICE)
    )
    measurements.append(
        synthesize_one(output_dir, "detailed-answer", ANSWER_TEXT, model, SELECTED_VOICE)
    )
    result = {
        "endpoint": ENDPOINT,
        "selected_voice": SELECTED_VOICE,
        "texts": {
            "comparison_characters": len(COMPARISON_TEXT),
            "source_passage_characters": len(PASSAGE_TEXT),
            "detailed_answer_characters": len(ANSWER_TEXT),
        },
        "measurements": [asdict(item) for item in measurements],
    }
    (output_dir / "live-results.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def self_test() -> dict[str, Any]:
    assert len(ANSWER_TEXT) >= 2_000
    assert len(PASSAGE_TEXT) >= 500
    assert request_payload("hello", DEFAULT_MODEL, SELECTED_VOICE) == {
        "model": DEFAULT_MODEL,
        "input": "hello",
        "voice": SELECTED_VOICE,
        "response_format": "mp3",
        "speed": 1.0,
    }
    assert cache_config_version(DEFAULT_MODEL, SELECTED_VOICE) != cache_config_version(
        DEFAULT_MODEL, DEFAULT_VOICES[1]
    )

    transient_attempts: dict[int, int] = {}
    for status in sorted(TRANSIENT_STATUSES):
        transient_attempts[status] = 0

        def transient_then_success(status: int = status) -> dict[str, Any]:
            transient_attempts[status] += 1
            if transient_attempts[status] == 1:
                raise SpeechRequestError(status, "transient failure")
            return {"ok": True}

        value, attempts = with_bounded_retry(
            transient_then_success, sleep=lambda _: None
        )
        assert value == {"ok": True}
        assert attempts == 2 and transient_attempts[status] == 2

    permanent_calls = 0

    def permanent_failure() -> dict[str, Any]:
        nonlocal permanent_calls
        permanent_calls += 1
        raise SpeechRequestError(400, "invalid request")

    try:
        with_bounded_retry(permanent_failure, sleep=lambda _: None)
    except SpeechRequestError as error:
        assert error.status == 400 and permanent_calls == 1
    else:
        raise AssertionError("permanent failure was unexpectedly retried")
    return {
        "status": "ok",
        "transient_attempts": transient_attempts,
        "permanent_attempts": permanent_calls,
        "answer_characters": len(ANSWER_TEXT),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("self-test")
    live = subparsers.add_parser("synthesize")
    live.add_argument("output_dir", type=Path)
    live.add_argument("--model", default=DEFAULT_MODEL)
    live.add_argument("--voices", nargs="+", default=list(DEFAULT_VOICES))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "self-test":
        result = self_test()
    else:
        result = synthesize(args.output_dir, args.model, tuple(args.voices))
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
