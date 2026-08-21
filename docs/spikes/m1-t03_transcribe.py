#!/usr/bin/env python3
"""Reproduce the M1-T03 browser-compatible WebM transcription spike.

This is ticket-scoped spike code, not the production OpenRouter integration. It uses
only the Python standard library plus the host's ``say``, ``ffmpeg``, and ``ffprobe``
commands. Live requests read OPENROUTER_API_KEY from the environment and never accept
the credential as a command-line argument.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ENDPOINT = "https://openrouter.ai/api/v1/audio/transcriptions"
DEFAULT_MODEL = "openai/gpt-4o-transcribe"
MIME_TYPE = "audio/webm"
FORMAT = "webm"
MAX_RECORDING_SECONDS = 120.0
MAX_ACCEPTABLE_WER = 0.10
MAX_CAPTURE_BYTES = 10 * 1024 * 1024
BROWSER_CAPTURE_PAGE = Path(__file__).with_name("m1-t03_browser_capture.html")

QUESTIONS = {
    "local-passage": (
        "Can you explain the Preamble in everyday language? What is it trying to say "
        "the Constitution is for?"
    ),
    "current-section": (
        "Looking at Article One as a whole, what powers does it give Congress, and what "
        "steps or limits does it place on how Congress uses those powers?"
    ),
    "document-wide": (
        "Across the Constitution, where do the text's structural checks on federal power "
        "appear?"
    ),
    "same-episode-follow-up": (
        "How does the bill process you just described connect to the broader idea that "
        "legislative power belongs to Congress?"
    ),
    "later-episode-continuity": (
        "Earlier you explained that the Preamble mostly states goals rather than specific "
        "rules. Is this Article One passage an example of a concrete rule, and how does it "
        "connect to those goals?"
    ),
}


@dataclass(frozen=True)
class Recording:
    question_type: str
    expected: str
    path: str
    mime_type: str
    format: str
    codec: str
    container_formats: tuple[str, ...]
    sample_rate_hz: int
    channels: int
    duration_seconds: float
    bytes: int
    sha256: str


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def require_commands(*names: str) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        raise RuntimeError(f"missing required command(s): {', '.join(missing)}")


def probe(path: Path) -> dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate,channels:format=format_name,duration",
            "-of",
            "json",
            str(path),
        ]
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    container_formats = tuple(data["format"]["format_name"].split(","))
    raw_duration = data["format"].get("duration")
    if raw_duration is None:
        packet_result = run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "packet=pts_time,duration_time",
                "-of",
                "csv=p=0",
                str(path),
            ]
        )
        packet_ends = []
        for line in packet_result.stdout.splitlines():
            values = line.split(",")
            if len(values) == 2 and all(value not in {"", "N/A"} for value in values):
                packet_ends.append(float(values[0]) + float(values[1]))
        if not packet_ends:
            raise ValueError(f"could not determine audio duration for {path}")
        duration_seconds = max(packet_ends)
    else:
        duration_seconds = float(raw_duration)
    return {
        "codec": stream["codec_name"],
        "container_formats": container_formats,
        "sample_rate_hz": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "duration_seconds": round(duration_seconds, 3),
    }


def recording_from_file(question_type: str, path: Path) -> Recording:
    metadata = probe(path)
    if "webm" not in metadata["container_formats"]:
        raise ValueError(
            f"{path} uses {metadata['container_formats']!r}, expected a WebM container"
        )
    if metadata["codec"] != "opus":
        raise ValueError(f"{path} uses {metadata['codec']!r}, expected Opus")
    if metadata["duration_seconds"] > MAX_RECORDING_SECONDS:
        raise ValueError(
            f"{path} is {metadata['duration_seconds']}s; V0 maximum is "
            f"{MAX_RECORDING_SECONDS:.0f}s"
        )
    content = path.read_bytes()
    if not content:
        raise ValueError(f"{path} is empty")
    return Recording(
        question_type=question_type,
        expected=QUESTIONS[question_type],
        path=str(path),
        mime_type=MIME_TYPE,
        format=FORMAT,
        bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        **metadata,
    )


def prepare(output_dir: Path) -> dict[str, Any]:
    require_commands("say", "ffmpeg", "ffprobe")
    output_dir.mkdir(parents=True, exist_ok=True)
    recordings: list[Recording] = []
    with tempfile.TemporaryDirectory(prefix="margin-m1-t03-") as temporary:
        temporary_dir = Path(temporary)
        for question_type, expected in QUESTIONS.items():
            aiff_path = temporary_dir / f"{question_type}.aiff"
            webm_path = output_dir / f"{question_type}.webm"
            run(["say", "-v", "Samantha", "-r", "185", "-o", str(aiff_path), expected])
            run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(aiff_path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "48000",
                    "-c:a",
                    "libopus",
                    "-b:a",
                    "48k",
                    str(webm_path),
                ]
            )
            recordings.append(recording_from_file(question_type, webm_path))
    manifest = {
        "fixture_method": "macOS say voice converted by ffmpeg to WebM/Opus",
        "recordings": [asdict(recording) for recording in recordings],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def prepare_duration_probe(
    input_dir: Path, duration_seconds: float
) -> dict[str, Any]:
    require_commands("ffmpeg", "ffprobe")
    if duration_seconds <= 0 or duration_seconds > MAX_RECORDING_SECONDS:
        raise ValueError(
            f"duration must be greater than zero and at most {MAX_RECORDING_SECONDS:.0f}s"
        )
    source_path = input_dir / "local-passage.webm"
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    output_path = input_dir / "duration-boundary.webm"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source_path),
            "-af",
            f"apad=whole_dur={duration_seconds}",
            "-t",
            str(duration_seconds),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "48000",
            "-c:a",
            "libopus",
            "-b:a",
            "48k",
            str(output_path),
        ]
    )
    recording = recording_from_file("local-passage", output_path)
    result = {
        "fixture_method": (
            "local-passage speech followed by encoded silence to exercise the configured "
            "recording-duration boundary"
        ),
        "recording": asdict(recording),
    }
    (input_dir / "duration-boundary-manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


class CaptureHandler(http.server.BaseHTTPRequestHandler):
    fixture_path: Path
    output_path: Path
    completed: threading.Event

    def do_GET(self) -> None:
        if self.path == "/":
            self._send_file(BROWSER_CAPTURE_PAGE, "text/html; charset=utf-8")
        elif self.path == "/fixture.webm":
            self._send_file(self.fixture_path, MIME_TYPE)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/capture":
            self.send_error(404)
            return
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", "0"))
        if not content_type.startswith(MIME_TYPE):
            self.send_error(415, "expected audio/webm")
            return
        if content_length <= 0 or content_length > MAX_CAPTURE_BYTES:
            self.send_error(413, "invalid capture size")
            return
        content = self.rfile.read(content_length)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_bytes(content)
        recording = recording_from_file("local-passage", self.output_path)
        manifest = {
            "capture_method": "browser MediaRecorder over a Web Audio MediaStream",
            "reported_mime_type": content_type,
            "user_agent": self.headers.get("X-Browser-User-Agent"),
            "recording": asdict(recording),
        }
        manifest_path = self.output_path.with_name("browser-capture-manifest.json")
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        response = json.dumps(manifest).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)
        self.completed.set()

    def _send_file(self, path: Path, content_type: str) -> None:
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"capture server: {format % args}", file=sys.stderr)


def serve_browser_capture(
    input_dir: Path, host: str, port: int
) -> dict[str, Any]:
    require_commands("ffprobe")
    if not BROWSER_CAPTURE_PAGE.is_file():
        raise FileNotFoundError(BROWSER_CAPTURE_PAGE)
    fixture_path = input_dir / "local-passage.webm"
    if not fixture_path.is_file():
        raise FileNotFoundError(fixture_path)
    output_path = input_dir / "browser-local-passage.webm"
    completed = threading.Event()
    handler = type(
        "ConfiguredCaptureHandler",
        (CaptureHandler,),
        {
            "fixture_path": fixture_path,
            "output_path": output_path,
            "completed": completed,
        },
    )
    server = http.server.ThreadingHTTPServer((host, port), handler)
    server.timeout = 0.5
    print(f"capture server listening at http://{host}:{port}", file=sys.stderr)
    try:
        while not completed.is_set():
            server.handle_request()
    finally:
        server.server_close()
    manifest_path = output_path.with_name("browser-capture-manifest.json")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def normalized_words(text: str) -> list[str]:
    normalized = text.casefold().replace("’", "'")
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", normalized)


def word_error_rate(expected: str, actual: str) -> float:
    reference = normalized_words(expected)
    hypothesis = normalized_words(actual)
    if not reference:
        return 0.0 if not hypothesis else 1.0
    previous = list(range(len(hypothesis) + 1))
    for reference_word in reference:
        current = [previous[0] + 1]
        for index, hypothesis_word in enumerate(hypothesis, 1):
            substitution = previous[index - 1] + (reference_word != hypothesis_word)
            insertion = current[index - 1] + 1
            deletion = previous[index] + 1
            current.append(min(substitution, insertion, deletion))
        previous = current
    return previous[-1] / len(reference)


def request_transcription(
    recording: Recording, model: str, timeout_seconds: float
) -> dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    audio = Path(recording.path).read_bytes()
    body = json.dumps(
        {
            "model": model,
            "input_audio": {
                "data": base64.b64encode(audio).decode("ascii"),
                "format": recording.format,
            },
            "language": "en",
            "temperature": 0,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Margin-M1-T03-Spike/1",
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_body = json.load(response)
            status = response.status
            generation_id = response.headers.get("X-Generation-Id")
    except urllib.error.HTTPError as error:
        safe_body = error.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"OpenRouter HTTP {error.code}: {safe_body}") from error
    elapsed = time.perf_counter() - started
    transcript = response_body.get("text")
    if status != 200 or not isinstance(transcript, str) or not transcript.strip():
        raise RuntimeError(f"unexpected transcription response (HTTP {status})")
    wer = word_error_rate(recording.expected, transcript)
    return {
        "question_type": recording.question_type,
        "expected": recording.expected,
        "transcript": transcript,
        "word_error_rate": round(wer, 4),
        "acceptable": wer <= MAX_ACCEPTABLE_WER,
        "latency_seconds": round(elapsed, 3),
        "http_status": status,
        "generation_id": generation_id,
        "usage": response_body.get("usage"),
    }


def load_recordings(input_dir: Path) -> list[Recording]:
    recordings = []
    for question_type in QUESTIONS:
        path = input_dir / f"{question_type}.webm"
        if not path.is_file():
            raise FileNotFoundError(path)
        recordings.append(recording_from_file(question_type, path))
    return recordings


def transcribe(input_dir: Path, model: str, timeout_seconds: float) -> dict[str, Any]:
    recordings = load_recordings(input_dir)
    results = [
        request_transcription(recording, model, timeout_seconds)
        for recording in recordings
    ]
    latencies = [result["latency_seconds"] for result in results]
    return {
        "endpoint": ENDPOINT,
        "model": model,
        "request_encoding": "JSON with base64 input_audio data",
        "mime_type": MIME_TYPE,
        "format": FORMAT,
        "configured_max_recording_seconds": MAX_RECORDING_SECONDS,
        "timeout_seconds": timeout_seconds,
        "attempts_per_recording": 1,
        "results": results,
        "summary": {
            "all_acceptable": all(result["acceptable"] for result in results),
            "maximum_word_error_rate": max(
                result["word_error_rate"] for result in results
            ),
            "median_latency_seconds": round(statistics.median(latencies), 3),
            "maximum_latency_seconds": round(max(latencies), 3),
        },
    }


def transcribe_one(
    path: Path, question_type: str, model: str, timeout_seconds: float
) -> dict[str, Any]:
    recording = recording_from_file(question_type, path)
    return {
        "endpoint": ENDPOINT,
        "model": model,
        "recording": asdict(recording),
        "result": request_transcription(recording, model, timeout_seconds),
        "timeout_seconds": timeout_seconds,
    }


def accuracy_passed(command: str, result: dict[str, Any]) -> bool:
    if command == "transcribe":
        return bool(result["summary"]["all_acceptable"])
    if command == "transcribe-one":
        return bool(result["result"]["acceptable"])
    return True


def self_test() -> dict[str, Any]:
    cases = [
        ("Hello, world!", "hello world", 0.0),
        ("one two three", "one four three", 1 / 3),
        ("one two", "one two three", 0.5),
        ("one two three", "one three", 1 / 3),
    ]
    for expected, actual, wanted in cases:
        actual_wer = word_error_rate(expected, actual)
        if abs(actual_wer - wanted) > 1e-9:
            raise AssertionError((expected, actual, wanted, actual_wer))
    if set(QUESTIONS) != {
        "local-passage",
        "current-section",
        "document-wide",
        "same-episode-follow-up",
        "later-episode-continuity",
    }:
        raise AssertionError("representative question set changed unexpectedly")
    accuracy_cases = [
        ("transcribe", {"summary": {"all_acceptable": True}}, True),
        ("transcribe", {"summary": {"all_acceptable": False}}, False),
        ("transcribe-one", {"result": {"acceptable": True}}, True),
        ("transcribe-one", {"result": {"acceptable": False}}, False),
    ]
    for command, result, wanted in accuracy_cases:
        if accuracy_passed(command, result) is not wanted:
            raise AssertionError((command, result, wanted))
    return {
        "status": "ok",
        "wer_cases": len(cases),
        "accuracy_gate_cases": len(accuracy_cases),
        "question_types": list(QUESTIONS),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("output_dir", type=Path)
    transcribe_parser = subparsers.add_parser("transcribe")
    transcribe_parser.add_argument("input_dir", type=Path)
    transcribe_parser.add_argument("--model", default=DEFAULT_MODEL)
    transcribe_parser.add_argument("--timeout-seconds", type=float, default=60.0)
    duration_parser = subparsers.add_parser("prepare-duration-probe")
    duration_parser.add_argument("input_dir", type=Path)
    duration_parser.add_argument(
        "--duration-seconds", type=float, default=MAX_RECORDING_SECONDS - 1
    )
    capture_parser = subparsers.add_parser("serve-browser-capture")
    capture_parser.add_argument("input_dir", type=Path)
    capture_parser.add_argument("--host", default="127.0.0.1")
    capture_parser.add_argument("--port", type=int, default=8765)
    one_parser = subparsers.add_parser("transcribe-one")
    one_parser.add_argument("path", type=Path)
    one_parser.add_argument("--question-type", choices=QUESTIONS, required=True)
    one_parser.add_argument("--model", default=DEFAULT_MODEL)
    one_parser.add_argument("--timeout-seconds", type=float, default=60.0)
    subparsers.add_parser("self-test")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.output_dir)
        elif args.command == "transcribe":
            result = transcribe(args.input_dir, args.model, args.timeout_seconds)
        elif args.command == "prepare-duration-probe":
            result = prepare_duration_probe(args.input_dir, args.duration_seconds)
        elif args.command == "serve-browser-capture":
            result = serve_browser_capture(args.input_dir, args.host, args.port)
        elif args.command == "transcribe-one":
            result = transcribe_one(
                args.path, args.question_type, args.model, args.timeout_seconds
            )
        else:
            result = self_test()
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    if not accuracy_passed(args.command, result):
        print("error: one or more transcripts exceeded the WER threshold", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
