#!/usr/bin/env python3
"""Reproduce the M1-T02 extraction measurements for Margin's selected PDF.

This is ticket-scoped spike code, not the production document processor. Run it with
the pinned versions recorded in ``m1-t02-pdf-extraction.md``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pdfplumber
from pypdf import PdfReader


EXPECTED_SHA256 = "4d85f1cbfcb9789f10bf306e379e97ff150ea235249190a188b0c05923fd6f19"
RUNNING_HEADERS = {
    "The Constitution of the United States of America—Literal Print",
    "Amendments to the Constitution of the United States of America—Literal Print",
}
ARTICLE_HEADING = re.compile(r"^Article\. [IVX]+\.$")
AMENDMENT_HEADING = re.compile(r"^Amendment [IVX]+\.$")
SECTION_START = re.compile(r"^Section\.? \d+\.")
SIGNATURE_PAGE = 11
SIGNATURE_PAGE_REGIONS = (
    ("closing_statement", (210.0, 50.0, 495.006, 195.0)),
    ("attestation_note", (0.0, 50.0, 210.0, 195.0)),
    ("left_signers", (0.0, 195.0, 260.0, 500.0)),
    ("right_signers", (260.0, 195.0, 495.006, 500.0)),
)


@dataclass
class Line:
    source_id: str
    page: int
    top: float
    bottom: float
    x0: float
    text: str
    font_size: float
    font_name: str


@dataclass
class Paragraph:
    id: str
    order: int
    text: str
    start_page: int
    end_page: int
    source_line_ids: tuple[str, ...]


@dataclass
class Section:
    id: str
    order: int
    title: str
    boundary_source: str
    source_line_ids: tuple[str, ...] = ()
    paragraphs: list[Paragraph] = field(default_factory=list)

    @property
    def first_paragraph_id(self) -> str:
        if not self.paragraphs:
            raise ValueError(f"section {self.title!r} has no paragraphs")
        return self.paragraphs[0].id


def flatten_outline(reader: PdfReader) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []

    def walk(items: list[Any], depth: int) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            title = getattr(item, "title", str(item))
            try:
                page = reader.get_destination_page_number(item) + 1
            except Exception:
                page = None
            flattened.append({"title": title, "page": page, "depth": depth})

    walk(reader.outline, 0)
    return flattened


def modal(values: list[Any], default: Any) -> Any:
    if not values:
        return default
    counts = Counter(values)
    highest_count = max(counts.values())
    return next(value for value in values if counts[value] == highest_count)


def extract_lines(pdf_path: Path) -> tuple[list[Line], float]:
    lines: list[Line] = []
    body_sizes: list[float] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            if page_number == SIGNATURE_PAGE:
                regions = (
                    (label, page.crop(bbox)) for label, bbox in SIGNATURE_PAGE_REGIONS
                )
            else:
                regions = (("page", page),)
            for region_label, region in regions:
                raw_lines = region.extract_text_lines(strip=True, return_chars=True)
                for line_number, raw in enumerate(raw_lines, 1):
                    text = re.sub(r"\s+", " ", raw["text"]).strip()
                    if not text or text in RUNNING_HEADERS:
                        continue
                    if raw["top"] > 670 and text.isdigit():
                        continue
                    sizes = [round(float(char["size"]), 1) for char in raw["chars"]]
                    fonts = [str(char["fontname"]) for char in raw["chars"]]
                    size = float(modal(sizes, 0.0))
                    font = str(modal(fonts, ""))
                    if "Roman" in font:
                        body_sizes.extend(sizes)
                    lines.append(
                        Line(
                            source_id=f"page_{page_number:02d}:{region_label}:{line_number:03d}",
                            page=page_number,
                            top=round(float(raw["top"]), 2),
                            bottom=round(float(raw["bottom"]), 2),
                            x0=round(float(raw["x0"]), 2),
                            text=text,
                            font_size=size,
                            font_name=font,
                        )
                    )
    return lines, statistics.median(body_sizes)


def join_lines(parts: list[str]) -> str:
    text = ""
    for part in parts:
        if text.endswith("-"):
            previous_token = text.rsplit(" ", 1)[-1]
            if "/" in previous_token:
                text += part
            elif part[:1].islower():
                text = text[:-1] + part
            else:
                text += part
        else:
            text = f"{text} {part}" if text else part
    # The selected PDF occasionally places both sides of a line-wrap hyphen on one
    # extracted layout line. Uppercase compounds such as "Vice- President" remain.
    return re.sub(r"(?<=\w)-\s+(?=[a-z])", "", text).strip()


def reconstruct(lines: list[Line]) -> list[Section]:
    sections: list[Section] = []
    current_section: Section | None = None
    paragraph_parts: list[str] = []
    paragraph_start_page = 0
    paragraph_end_page = 0
    paragraph_line_ids: list[str] = []
    previous_line: Line | None = None
    paragraph_order = 0

    def start_section(
        title: str, source: str, source_line_ids: tuple[str, ...] = ()
    ) -> None:
        nonlocal current_section
        flush_paragraph()
        current_section = Section(
            id=f"section_{len(sections) + 1:03d}",
            order=len(sections) + 1,
            title=title,
            boundary_source=source,
            source_line_ids=source_line_ids,
        )
        sections.append(current_section)

    def flush_paragraph() -> None:
        nonlocal paragraph_parts, paragraph_line_ids, paragraph_order
        if not paragraph_parts:
            return
        if current_section is None:
            raise AssertionError("paragraph created without a section")
        paragraph_order += 1
        current_section.paragraphs.append(
            Paragraph(
                id=f"paragraph_{paragraph_order:04d}",
                order=paragraph_order,
                text=join_lines(paragraph_parts),
                start_page=paragraph_start_page,
                end_page=paragraph_end_page,
                source_line_ids=tuple(paragraph_line_ids),
            )
        )
        paragraph_parts = []
        paragraph_line_ids = []

    start_section("Front matter", "fallback")
    for line in lines:
        if ARTICLE_HEADING.fullmatch(line.text):
            start_section(
                line.text.replace(".", "").replace("Article ", "Article "),
                "heading",
                (line.source_id,),
            )
            previous_line = line
            continue
        if AMENDMENT_HEADING.fullmatch(line.text):
            start_section(line.text[:-1], "heading", (line.source_id,))
            previous_line = line
            continue
        if line.text == "We the People":
            start_section("Preamble", "heading")
        elif (
            line.page >= 13
            and line.text == "A"
            and current_section.title == "Article VII"
        ):
            start_section("Amendments front matter", "heading")
        elif line.text == "MENDMENTS TO THE" and current_section.title != "Amendments front matter":
            start_section("Amendments front matter", "heading")

        page_break = previous_line is not None and previous_line.page != line.page
        vertical_gap = (
            previous_line is not None
            and previous_line.page == line.page
            and line.top - previous_line.bottom >= 10.0
        )
        begins_structural_paragraph = bool(SECTION_START.match(line.text))
        prior_looks_complete = bool(paragraph_parts and re.search(r"[.!?]$", paragraph_parts[-1]))
        if paragraph_parts and (
            vertical_gap or begins_structural_paragraph or (page_break and prior_looks_complete)
        ):
            flush_paragraph()
        if not paragraph_parts:
            paragraph_start_page = line.page
        paragraph_parts.append(line.text)
        paragraph_line_ids.append(line.source_id)
        paragraph_end_page = line.page
        previous_line = line

    flush_paragraph()
    return sections


BENCHMARK_NEEDLES = {
    "P1": ["We the People of the United States, in Order to form a more perfect Union"],
    "P2": ["Every Bill which shall have passed the House of Representatives and the Senate"],
    "P3": [
        "The executive Power shall be vested in a President of the United States of America",
        "No Person except a natural born Citizen",
        "In Case of the Removal of the President from Office",
    ],
    "P4": [
        "Congress shall make no law respecting an establishment of religion",
        "The right of the people to be secure in their persons, houses, papers, and effects",
    ],
    "P5": ["All persons born or naturalized in the United States"],
}


def locate_benchmarks(sections: list[Section]) -> dict[str, list[dict[str, Any]]]:
    located: dict[str, list[dict[str, Any]]] = {}
    for passage, needles in BENCHMARK_NEEDLES.items():
        matches: list[dict[str, Any]] = []
        for needle in needles:
            found = None
            for section in sections:
                for paragraph in section.paragraphs:
                    if needle in paragraph.text:
                        found = {
                            "section_id": section.id,
                            "section_title": section.title,
                            "paragraph_id": paragraph.id,
                            "paragraph_order": paragraph.order,
                            "start_page": paragraph.start_page,
                            "end_page": paragraph.end_page,
                            "sample": paragraph.text[:240],
                        }
                        break
                if found:
                    break
            if found is None:
                raise AssertionError(f"{passage} needle not found: {needle}")
            matches.append(found)
        located[passage] = matches
    return located


def build_result(pdf_path: Path) -> dict[str, Any]:
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"unexpected PDF checksum: {digest}")

    reader = PdfReader(pdf_path)
    pypdf_plain = "".join(page.extract_text() or "" for page in reader.pages)
    pypdf_layout = "".join(
        page.extract_text(extraction_mode="layout") or "" for page in reader.pages
    )
    outline = flatten_outline(reader)
    lines, body_font_size = extract_lines(pdf_path)
    sections = reconstruct(lines)
    paragraphs = [paragraph for section in sections for paragraph in section.paragraphs]
    normalized_text = "\n\n".join(paragraph.text for paragraph in paragraphs)
    canonical_text = "\n\n".join(
        f"[SECTION {section.order} | {section.title}]\n"
        + "\n\n".join(
            f"[PARAGRAPH {paragraph.order} | PAGES {paragraph.start_page}-{paragraph.end_page}]\n"
            f"{paragraph.text}"
            for paragraph in section.paragraphs
        )
        for section in sections
    )

    orders = [paragraph.order for paragraph in paragraphs]
    if orders != list(range(1, len(paragraphs) + 1)):
        raise AssertionError("paragraph ordering is not contiguous")
    if any(not section.paragraphs for section in sections):
        raise AssertionError("one or more sections has no deterministic first paragraph")
    if normalized_text.count("We the People of the United States") != 1:
        raise AssertionError("Preamble was omitted or duplicated")

    retained_line_ids = [line.source_id for line in lines]
    canonical_line_ids = [
        source_line_id
        for section in sections
        for source_line_id in (
            *section.source_line_ids,
            *(line_id for paragraph in section.paragraphs for line_id in paragraph.source_line_ids),
        )
    ]
    if len(retained_line_ids) != len(set(retained_line_ids)):
        raise AssertionError("retained layout line IDs are not unique")
    if Counter(canonical_line_ids) != Counter(retained_line_ids):
        raise AssertionError("canonical walk does not consume every retained line exactly once")
    if canonical_line_ids != retained_line_ids:
        raise AssertionError("canonical walk reorders retained layout lines")

    paragraph_ids = [paragraph.id for paragraph in paragraphs]
    if len(paragraph_ids) != len(set(paragraph_ids)):
        raise AssertionError("a paragraph is owned by more than one section")

    signature_order = (
        "done in Convention",
        "The Word, “the,” being interlined",
        "DELAWARE",
        "NEW HAMPSHIRE",
    )
    signature_positions = [normalized_text.index(phrase) for phrase in signature_order]
    if signature_positions != sorted(signature_positions):
        raise AssertionError("signature-page blocks are not in canonical reading order")
    for artifact in ("interlined between in Convention", "Sep-Page"):
        if artifact in normalized_text:
            raise AssertionError(f"signature-page column merge remains: {artifact}")

    return {
        "input": {
            "path": str(pdf_path),
            "sha256": digest,
            "pages": len(reader.pages),
        },
        "versions": {
            "pypdf": __import__("pypdf").__version__,
            "pdfplumber": pdfplumber.__version__,
        },
        "metadata": {str(key): str(value) for key, value in (reader.metadata or {}).items()},
        "outline": {
            "entries": outline,
            "entry_count": len(outline),
            "entries_with_page": sum(entry["page"] is not None for entry in outline),
        },
        "extraction": {
            "pypdf_plain_characters": len(pypdf_plain),
            "pypdf_layout_characters": len(pypdf_layout),
            "pdfplumber_layout_lines_retained": len(lines),
            "median_body_font_size": body_font_size,
            "normalized_paragraph_characters": len(normalized_text),
            "canonical_serialization_characters": len(canonical_text),
            "paragraph_count": len(paragraphs),
            "section_count": len(sections),
        },
        "sections": [
            {
                "id": section.id,
                "order": section.order,
                "title": section.title,
                "boundary_source": section.boundary_source,
                "first_paragraph_id": section.first_paragraph_id,
                "paragraph_count": len(section.paragraphs),
                "character_count": sum(len(p.text) for p in section.paragraphs),
                "start_page": section.paragraphs[0].start_page,
                "end_page": section.paragraphs[-1].end_page,
            }
            for section in sections
        ],
        "benchmarks": locate_benchmarks(sections),
        "invariants": {
            "paragraph_orders_contiguous": orders
            == list(range(1, len(paragraphs) + 1)),
            "each_paragraph_owned_by_one_section": len(paragraph_ids)
            == len(set(paragraph_ids)),
            "each_section_has_first_paragraph": all(
                section.first_paragraph_id for section in sections
            ),
            "each_retained_line_consumed_once": Counter(canonical_line_ids)
            == Counter(retained_line_ids),
            "canonical_walk_preserves_line_order": canonical_line_ids
            == retained_line_ids,
            "signature_page_blocks_readable": signature_positions
            == sorted(signature_positions),
        },
        "representative_paragraphs": [
            asdict(paragraphs[index]) for index in (0, 1, 2, len(paragraphs) - 1)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--json", action="store_true", help="emit the complete measured result")
    args = parser.parse_args()
    result = build_result(args.pdf)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    print(json.dumps({"input": result["input"], "extraction": result["extraction"]}, indent=2))
    for passage, matches in result["benchmarks"].items():
        markers = ", ".join(
            f"{match['section_title']}/{match['paragraph_id']}/p.{match['start_page']}"
            for match in matches
        )
        print(f"{passage}: {markers}")


if __name__ == "__main__":
    main()
