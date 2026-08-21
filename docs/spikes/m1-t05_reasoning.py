#!/usr/bin/env python3
"""Reproduce the M1-T05 reasoning/context spike.

This is disposable ticket-scoped code, not Margin's production context builder or
OpenRouter integration. Generated prompts and answers belong under ignored ``var/``.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tiktoken


ROOT = Path(__file__).resolve().parents[2]
EXTRACTION_SCRIPT = ROOT / "docs/spikes/m1-t02_extract.py"
DEFAULT_PDF = ROOT / "var/spikes/m1-t02/constitution.pdf"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-5.6-sol"
ENCODING = "o200k_base"
MODEL_CONTEXT_LIMIT = 128_000
OVER_LIMIT_PROFILE = 16_000
RESERVED_ANSWER_TOKENS = 4_096
SAFETY_MARGIN = 2_048
CONSERVATIVE_CHARACTERS_PER_TOKEN = 3.0
MAX_QUESTION_CHARACTERS = 2_000
EXPECTED_SECTION_COUNT = 37
EXPECTED_PARAGRAPH_COUNT = 154
EXPECTED_CANONICAL_CHARACTERS = 53_125

SYSTEM = """You are Margin, an expert reading companion. Answer from the explicitly supplied package.
The uploaded source text is authoritative. Orientation, a section synopsis, and prior dialogue are
supporting context, not evidence for new claims about the source. Clearly label interpretation,
general background knowledge, and invented examples. Never claim that text appears elsewhere unless
the supplied source proves it. Full-document claims require the canonical full source. In LIMITED
DOCUMENT-WIDE scope, begin by naming every supplied layer: orientation, section synopsis, local
passage window, and complete active-session dialogue (say explicitly when the dialogue is empty),
then say that you did not examine the complete document; do not imply search, retrieval, or verified
locations elsewhere. Be useful and clear, and answer at the depth requested."""


QUESTIONS = {
    "B1": "Can you explain the Preamble in everyday language? What is it trying to say the Constitution is for?",
    "B2": "What constitutional design does this passage appear to be aiming for by requiring both houses and then involving the President?",
    "B3": "Give me a simple made-up example of how a bill could become law after the President objects to it.",
    "B4": "What is a reasonable criticism someone might make of this presidential-selection process, and how is that criticism different from what the text itself says?",
    "B5": "Looking at Article I as a whole, what powers does it give Congress, and what steps or limits does it place on how Congress uses those powers?",
    "B6": "Across the Constitution, where do the text's structural checks on federal power appear? Compare Article I's lawmaking process with Article II's presidential powers and the Amendment XIV limits on state action.",
    "B7": "Where else in this document are there checks on federal power?",
}

FOLLOW_UPS = {
    "S1": "Which parts of your explanation describe goals, and which parts would you need later constitutional text to turn into a specific rule?",
    "S2": "How does the bill process you just described connect to the broader idea that legislative power belongs to Congress?",
    "S3": "Earlier you explained that the Preamble mostly states goals rather than specific rules. Is this Article I passage an example of a concrete rule, and how does it connect to those goals?",
}

ARTICLE_I_SYNOPSIS = (
    "Article I establishes a bicameral Congress, describes elections and internal procedures, "
    "sets the process for legislation, enumerates congressional powers, and states limits on "
    "Congress and the states. This generated synopsis is orientation only, not source evidence."
)


@dataclass(frozen=True)
class Turn:
    question: str
    answer: str
    episode: int
    turn: int


def load_extraction_module() -> Any:
    spec = importlib.util.spec_from_file_location("m1_t02_extract", EXTRACTION_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load M1-T02 extraction module")
    module = importlib.util.module_from_spec(spec)
    # Dataclasses consult sys.modules while applying their decorator.
    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def extract(pdf: Path) -> tuple[list[Any], list[Any]]:
    module = load_extraction_module()
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if digest != module.EXPECTED_SHA256:
        raise ValueError(f"unexpected PDF checksum: {digest}")
    lines, _ = module.extract_lines(pdf)
    sections = module.reconstruct(lines)
    paragraphs = [paragraph for section in sections for paragraph in section.paragraphs]
    if len(sections) != EXPECTED_SECTION_COUNT:
        raise AssertionError(
            f"expected {EXPECTED_SECTION_COUNT} sections, found {len(sections)}"
        )
    if len(paragraphs) != EXPECTED_PARAGRAPH_COUNT:
        raise AssertionError(
            f"expected {EXPECTED_PARAGRAPH_COUNT} paragraphs, found {len(paragraphs)}"
        )
    return sections, paragraphs


def find_paragraph(paragraphs: list[Any], needle: str) -> Any:
    matches = [paragraph for paragraph in paragraphs if needle in paragraph.text]
    if len(matches) != 1:
        raise AssertionError(f"expected one paragraph for {needle!r}, found {len(matches)}")
    return matches[0]


def canonical_source(sections: list[Any]) -> str:
    return "\n\n".join(
        f"[SECTION {section.order} | {section.title}]\n"
        + "\n\n".join(
            f"[PARAGRAPH {paragraph.order} | PAGES {paragraph.start_page}-{paragraph.end_page}]\n"
            f"{paragraph.text}"
            for paragraph in section.paragraphs
        )
        for section in sections
    )


def orientation(sections: list[Any]) -> str:
    section_map = "\n".join(
        f"- [SECTION {section.order}] {section.title}" for section in sections
    )
    return (
        "Title: The Constitution of the United States of America — Literal Print\n"
        "Author: United States\nDocument type: Constitution\n"
        "Ordered document map (orientation only):\n" + section_map
    )


def marked_paragraph(paragraph: Any, *, anchor: bool = False) -> str:
    label = "ANCHOR" if anchor else "PARAGRAPH"
    return (
        f"[{label} {paragraph.order} | PAGES {paragraph.start_page}-{paragraph.end_page}]\n"
        f"{paragraph.text}"
    )


def local_window(paragraphs: list[Any], anchor: Any) -> str:
    index = paragraphs.index(anchor)
    selected = paragraphs[max(0, index - 2) : index + 2]
    return "\n\n".join(marked_paragraph(p, anchor=p is anchor) for p in selected)


def dialogue(turns: list[Turn]) -> str:
    if not turns:
        return "(none — fresh reading session)"
    return "\n\n".join(
        f"[EPISODE {turn.episode} | TURN {turn.turn} | USER]\n{turn.question}\n"
        f"[EPISODE {turn.episode} | TURN {turn.turn} | ASSISTANT]\n{turn.answer}"
        for turn in turns
    )


def prompt(
    *,
    scope: str,
    orientation_text: str,
    source: str,
    turns: list[Turn],
    question: str,
) -> str:
    if len(question) > MAX_QUESTION_CHARACTERS:
        raise ValueError("question exceeds the configured complete-transcript limit")
    return (
        f"CONTEXT SCOPE: {scope}\n\n"
        f"DOCUMENT ORIENTATION\n{orientation_text}\n\n"
        f"SUPPLIED SOURCE CONTEXT\n{source}\n\n"
        f"COMPLETE ACTIVE READING-SESSION DIALOGUE\n{dialogue(turns)}\n\n"
        f"CURRENT USER QUESTION\n{question}\n\n"
        "Answer the current question. Treat dialogue as conversational memory, not source evidence."
    )


def exact_candidate(user_prompt: str) -> str:
    # These explicit role labels are part of the deterministic application estimate.
    return f"[SYSTEM]\n{SYSTEM}\n\n[USER]\n{user_prompt}"


def measure(user_prompt: str, context_limit: int) -> dict[str, Any]:
    candidate = exact_candidate(user_prompt)
    token_count = len(tiktoken.get_encoding(ENCODING).encode(candidate))
    characters = len(candidate)
    token_allowance = context_limit - RESERVED_ANSWER_TOKENS - SAFETY_MARGIN
    character_allowance = int(token_allowance * CONSERVATIVE_CHARACTERS_PER_TOKEN)
    return {
        "normalized_characters": characters,
        "estimated_input_tokens": token_count,
        "token_estimator": ENCODING,
        "context_limit_tokens": context_limit,
        "reserved_answer_tokens": RESERVED_ANSWER_TOKENS,
        "safety_margin_tokens": SAFETY_MARGIN,
        "input_allowance_tokens": token_allowance,
        "conservative_characters_per_token": CONSERVATIVE_CHARACTERS_PER_TOKEN,
        "character_allowance": character_allowance,
        "fits_token_estimator": token_count <= token_allowance,
        "fits_character_budget": characters <= character_allowance,
    }


def package_data(pdf: Path) -> dict[str, Any]:
    sections, paragraphs = extract(pdf)
    canonical = canonical_source(sections)
    if len(canonical) != EXPECTED_CANONICAL_CHARACTERS:
        raise AssertionError(
            "expected "
            f"{EXPECTED_CANONICAL_CHARACTERS} canonical characters, found {len(canonical)}"
        )
    p1 = find_paragraph(paragraphs, "We the People of the United States, in Order")
    p2 = find_paragraph(
        paragraphs, "Every Bill which shall have passed the House of Representatives"
    )
    p3 = find_paragraph(
        paragraphs, "The executive Power shall be vested in a President of the United States"
    )
    article_i = next(section for section in sections if section.title == "Article I")
    full_article_i = (
        "[CURRENT SECTION | Article I | COMPLETE BOUNDED SECTION]\n"
        + "\n\n".join(marked_paragraph(p) for p in article_i.paragraphs)
    )
    local_sources = {
        "P1": (
            f"[CURRENT SECTION TITLE] Preamble\n[GENERATED SECTION SYNOPSIS — ORIENTATION ONLY]\n"
            "The Preamble introduces the Constitution through stated collective aims.\n\n"
            f"[LOCAL PASSAGE WINDOW]\n{local_window(paragraphs, p1)}"
        ),
        "P2": (
            f"[CURRENT SECTION TITLE] Article I\n[GENERATED SECTION SYNOPSIS — ORIENTATION ONLY]\n"
            f"{ARTICLE_I_SYNOPSIS}\n\n[LOCAL PASSAGE WINDOW]\n{local_window(paragraphs, p2)}"
        ),
        "P3": (
            f"[CURRENT SECTION TITLE] Article II\n[GENERATED SECTION SYNOPSIS — ORIENTATION ONLY]\n"
            "Article II establishes the executive branch and describes presidential selection, powers, and duties. "
            "This generated synopsis is orientation only, not source evidence.\n\n"
            f"[LOCAL PASSAGE WINDOW]\n{local_window(paragraphs, p3)}"
        ),
    }
    limited = (
        "[LIMITED DOCUMENT-WIDE CONTEXT — NO RETRIEVAL OR COMPLETE-DOCUMENT ANALYSIS]\n"
        "Supplied layers: document orientation above, Article I synopsis below, and P2 local passage window.\n"
        f"[GENERATED ARTICLE I SYNOPSIS — ORIENTATION ONLY]\n{ARTICLE_I_SYNOPSIS}\n\n"
        f"[P2 LOCAL PASSAGE WINDOW]\n{local_window(paragraphs, p2)}"
    )
    return {
        "sections": sections,
        "paragraphs": paragraphs,
        "orientation": orientation(sections),
        "canonical": canonical,
        "local": local_sources,
        "section": full_article_i,
        "limited": limited,
    }


def initial_prompts(data: dict[str, Any]) -> dict[str, str]:
    orientation_text = data["orientation"]
    return {
        "B1": prompt(scope="LOCAL PASSAGE", orientation_text=orientation_text, source=data["local"]["P1"], turns=[], question=QUESTIONS["B1"]),
        "B2": prompt(scope="LOCAL PASSAGE", orientation_text=orientation_text, source=data["local"]["P2"], turns=[], question=QUESTIONS["B2"]),
        "B3": prompt(scope="LOCAL PASSAGE", orientation_text=orientation_text, source=data["local"]["P2"], turns=[], question=QUESTIONS["B3"]),
        "B4": prompt(scope="LOCAL PASSAGE", orientation_text=orientation_text, source=data["local"]["P3"], turns=[], question=QUESTIONS["B4"]),
        "B5": prompt(scope="CURRENT SECTION", orientation_text=orientation_text, source=data["section"], turns=[], question=QUESTIONS["B5"]),
        "B6": prompt(scope="FULL DOCUMENT", orientation_text=orientation_text, source=data["canonical"], turns=[], question=QUESTIONS["B6"]),
        "B7_full_candidate": prompt(scope="FULL DOCUMENT", orientation_text=orientation_text, source=data["canonical"], turns=[], question=QUESTIONS["B7"]),
        "B7": prompt(scope="LIMITED DOCUMENT-WIDE", orientation_text=orientation_text, source=data["limited"], turns=[], question=QUESTIONS["B7"]),
    }


def request_model(user_prompt: str, api_key: str) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": RESERVED_ANSWER_TOKENS,
        }
    ).encode()
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://margin.local",
            "X-Title": "Margin M1-T05 reasoning spike",
        },
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read())
            generation_id = response.headers.get("X-Generation-Id")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter returned HTTP {error.code}: {detail}") from error
    elapsed = time.monotonic() - started
    answer = payload["choices"][0]["message"]["content"]
    usage = payload.get("usage", {})
    return {
        "answer": answer,
        "latency_seconds": round(elapsed, 3),
        "generation_id": generation_id or payload.get("id"),
        "provider": payload.get("provider"),
        "usage": usage,
    }


def self_test(pdf: Path) -> dict[str, Any]:
    data = package_data(pdf)
    prompts = initial_prompts(data)
    measurements = {
        "B6_fitting_profile": measure(prompts["B6"], MODEL_CONTEXT_LIMIT),
        "B7_full_over_limit_profile": measure(prompts["B7_full_candidate"], OVER_LIMIT_PROFILE),
        "B7_selected_limited_profile": measure(prompts["B7"], OVER_LIMIT_PROFILE),
    }
    assert measurements["B6_fitting_profile"]["fits_token_estimator"]
    assert measurements["B6_fitting_profile"]["fits_character_budget"]
    assert not measurements["B7_full_over_limit_profile"]["fits_token_estimator"]
    assert not measurements["B7_full_over_limit_profile"]["fits_character_budget"]
    assert measurements["B7_selected_limited_profile"]["fits_token_estimator"]
    assert measurements["B7_selected_limited_profile"]["fits_character_budget"]
    assert data["canonical"].count("[PARAGRAPH ") == EXPECTED_PARAGRAPH_COUNT
    assert data["canonical"].count("[SECTION ") == EXPECTED_SECTION_COUNT
    assert "GENERATED SECTION SYNOPSIS" not in prompts["B5"]
    assert "LOCAL PASSAGE WINDOW" not in prompts["B5"]
    assert "LOCAL PASSAGE WINDOW" not in prompts["B6"]
    return {
        "model": MODEL,
        "source": {
            "sections": len(data["sections"]),
            "paragraphs": len(data["paragraphs"]),
            "canonical_characters": len(data["canonical"]),
        },
        "measurements": measurements,
        "checks": "passed",
    }


def live(pdf: Path, output: Path) -> dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is required")
    data = package_data(pdf)
    prompts = initial_prompts(data)
    results: dict[str, Any] = {}
    for case in ("B1", "B2", "B3", "B4", "B5", "B6", "B7"):
        profile = OVER_LIMIT_PROFILE if case == "B7" else MODEL_CONTEXT_LIMIT
        result = request_model(prompts[case], api_key)
        result["prompt_measurement"] = measure(prompts[case], profile)
        results[case] = result
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"model": MODEL, "results": results}, indent=2))

    sequences = {
        "S1": ("P1", "LOCAL PASSAGE", data["local"]["P1"], "B1", 1),
        "S2": ("P2", "CURRENT SECTION", data["section"], "B5", 1),
        "S3": ("P2", "LOCAL PASSAGE", data["local"]["P2"], "B1", 2),
    }
    for sequence, (_, scope, source, prior_case, episode) in sequences.items():
        prior = Turn(
            question=QUESTIONS[prior_case],
            answer=results[prior_case]["answer"],
            episode=1,
            turn=1,
        )
        sequence_prompt = prompt(
            scope=scope,
            orientation_text=data["orientation"],
            source=source,
            turns=[prior],
            question=FOLLOW_UPS[sequence],
        )
        result = request_model(sequence_prompt, api_key)
        result["prompt_measurement"] = measure(sequence_prompt, MODEL_CONTEXT_LIMIT)
        result["episode"] = episode
        result["prior_complete_turns"] = 1
        results[sequence] = result
        output.write_text(json.dumps({"model": MODEL, "results": results}, indent=2))
    return {"model": MODEL, "results": results}


def live_b7(pdf: Path, output: Path) -> dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is required")
    data = package_data(pdf)
    user_prompt = initial_prompts(data)["B7"]
    result = request_model(user_prompt, api_key)
    result["prompt_measurement"] = measure(user_prompt, OVER_LIMIT_PROFILE)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"model": MODEL, "results": {"B7": result}}, indent=2))
    return {"model": MODEL, "results": {"B7": result}}


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("self-test", "measure"):
        command = subparsers.add_parser(name)
        command.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    live_parser = subparsers.add_parser("live")
    live_parser.add_argument("output", type=Path)
    live_parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    b7_parser = subparsers.add_parser("live-b7")
    b7_parser.add_argument("output", type=Path)
    b7_parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    args = parser.parse_args()
    if args.command in {"self-test", "measure"}:
        print(json.dumps(self_test(args.pdf), indent=2))
    elif args.command == "live":
        print(json.dumps(live(args.pdf, args.output), indent=2))
    else:
        print(json.dumps(live_b7(args.pdf, args.output), indent=2))


if __name__ == "__main__":
    main()
