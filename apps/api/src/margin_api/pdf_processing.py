"""Deterministic processing for Margin's one supported development PDF.

This module intentionally supports only the checksum-pinned Constitution PDF selected
in M0.  Upload, persistence, and arbitrary-PDF handling belong to later tickets.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pdfplumber
from pypdf import PdfReader

EXPECTED_SELECTED_PDF_SHA256 = "4d85f1cbfcb9789f10bf306e379e97ff150ea235249190a188b0c05923fd6f19"
RUNNING_HEADERS = frozenset(
    {
        "The Constitution of the United States of America—Literal Print",
        "Amendments to the Constitution of the United States of America—Literal Print",
    }
)
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

# These are the architecture's initial processing limits.  The selected-document
# policy deliberately retains short named amendments as individual sections so
# their visible headings remain navigation markers; it splits only oversized
# sections at paragraph boundaries.
MAX_PARAGRAPH_CHARS = 2_000
MAX_SECTION_CHARS = 100_000
DOCUMENT_MAP_MAX_ENTRIES = 24
DOCUMENT_MAP_MAX_CHARS = 4_000

BoundarySource = Literal["heading", "fallback"]


class PdfProcessingError(ValueError):
    """A clear failure for an input outside this narrow supported-PDF contract."""


@dataclass(frozen=True)
class LayoutLine:
    source_id: str
    page: int
    top: float
    bottom: float
    x0: float
    text: str
    font_size: float
    font_name: str


@dataclass(frozen=True)
class ProcessedParagraph:
    order: int
    text: str
    start_page: int
    end_page: int
    source_line_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProcessedSection:
    order: int
    title: str
    boundary_source: BoundarySource
    first_paragraph_order: int
    paragraphs: tuple[ProcessedParagraph, ...]
    source_line_ids: tuple[str, ...]

    @property
    def start_page(self) -> int:
        return self.paragraphs[0].start_page

    @property
    def end_page(self) -> int:
        return self.paragraphs[-1].end_page


@dataclass(frozen=True)
class DocumentMapEntry:
    order: int | None
    title: str
    omitted_sections: int = 0


@dataclass(frozen=True)
class ProcessedDocument:
    source_sha256: str
    title: str
    author: str | None
    page_count: int
    document_map: tuple[DocumentMapEntry, ...]
    sections: tuple[ProcessedSection, ...]

    @property
    def paragraphs(self) -> tuple[ProcessedParagraph, ...]:
        return tuple(paragraph for section in self.sections for paragraph in section.paragraphs)


@dataclass
class _DraftSection:
    title: str
    boundary_source: BoundarySource
    source_line_ids: tuple[str, ...]
    paragraphs: list[ProcessedParagraph]


def process_selected_pdf(pdf_path: Path) -> ProcessedDocument:
    """Return a lossless, source-ordered representation of the pinned PDF."""

    try:
        source_bytes = pdf_path.read_bytes()
    except OSError as error:
        raise PdfProcessingError("selected PDF could not be read") from error
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != EXPECTED_SELECTED_PDF_SHA256:
        raise PdfProcessingError("unsupported PDF: checksum does not match the selected document")

    try:
        reader = PdfReader(pdf_path)
        lines = extract_selected_pdf_lines(pdf_path)
    except Exception as error:
        raise PdfProcessingError("selected PDF text extraction failed") from error
    if not lines:
        raise PdfProcessingError("selected PDF contains no extractable text")

    sections = reconstruct_selected_pdf(lines)
    sections = apply_section_policy(sections)
    processed = _finalize_sections(sections)
    _assert_invariants(lines, processed)
    metadata: Any = reader.metadata or {}
    author = str(metadata.get("/Author") or "").strip() or None
    return ProcessedDocument(
        source_sha256=source_sha256,
        title="The Constitution of the United States of America — Literal Print",
        author=author,
        page_count=len(reader.pages),
        document_map=build_document_map(processed),
        sections=processed,
    )


def extract_selected_pdf_lines(pdf_path: Path) -> list[LayoutLine]:
    """Extract layout lines, applying the pinned p. 11 region ordering."""

    lines: list[LayoutLine] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            regions = (
                ((label, page.crop(bbox)) for label, bbox in SIGNATURE_PAGE_REGIONS)
                if page_number == SIGNATURE_PAGE
                else (("page", page),)
            )
            for region_label, region in regions:
                raw_lines = region.extract_text_lines(strip=True, return_chars=True)
                for line_number, raw in enumerate(raw_lines, start=1):
                    text = re.sub(r"\s+", " ", raw["text"]).strip()
                    if not text or text in RUNNING_HEADERS:
                        continue
                    if raw["top"] > 670 and text.isdigit():
                        continue
                    chars = raw["chars"]
                    if not chars:
                        continue
                    sizes = [round(float(char["size"]), 1) for char in chars]
                    fonts = [str(char["fontname"]) for char in chars]
                    lines.append(
                        LayoutLine(
                            source_id=f"page_{page_number:02d}:{region_label}:{line_number:03d}",
                            page=page_number,
                            top=round(float(raw["top"]), 2),
                            bottom=round(float(raw["bottom"]), 2),
                            x0=round(float(raw["x0"]), 2),
                            text=text,
                            font_size=float(_modal(sizes, 0.0)),
                            font_name=str(_modal(fonts, "")),
                        )
                    )
    return lines


def reconstruct_selected_pdf(lines: list[LayoutLine]) -> list[_DraftSection]:
    """Use only the selected PDF's validated heading and paragraph signals."""

    sections: list[_DraftSection] = []
    current: _DraftSection | None = None
    paragraph_parts: list[str] = []
    paragraph_line_ids: list[str] = []
    paragraph_start_page = 0
    paragraph_end_page = 0
    prior: LayoutLine | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph_parts, paragraph_line_ids
        if not paragraph_parts:
            return
        if current is None:
            raise PdfProcessingError("selected PDF paragraph lacks a section")
        text = join_lines(paragraph_parts)
        if not text:
            raise PdfProcessingError("selected PDF contains an empty reconstructed paragraph")
        current.paragraphs.extend(
            _split_paragraph(
                text,
                paragraph_start_page,
                paragraph_end_page,
                tuple(paragraph_line_ids),
            )
        )
        paragraph_parts = []
        paragraph_line_ids = []

    def start_section(title: str, source: BoundarySource, source_ids: tuple[str, ...] = ()) -> None:
        nonlocal current
        flush_paragraph()
        current = _DraftSection(title, source, source_ids, [])
        sections.append(current)

    start_section("Front matter", "fallback")
    for line in lines:
        if ARTICLE_HEADING.fullmatch(line.text):
            start_section(line.text.replace(".", ""), "heading", (line.source_id,))
            prior = line
            continue
        if AMENDMENT_HEADING.fullmatch(line.text):
            start_section(line.text[:-1], "heading", (line.source_id,))
            prior = line
            continue
        if line.text == "We the People":
            start_section("Preamble", "heading")
        elif _begins_amendments_front_matter(line, current):
            start_section("Amendments front matter", "heading")

        page_break = prior is not None and prior.page != line.page
        vertical_gap = (
            prior is not None and prior.page == line.page and line.top - prior.bottom >= 10.0
        )
        starts_structural_paragraph = bool(SECTION_START.match(line.text))
        prior_complete = bool(paragraph_parts and re.search(r"[.!?]$", paragraph_parts[-1]))
        if paragraph_parts and (
            vertical_gap or starts_structural_paragraph or (page_break and prior_complete)
        ):
            flush_paragraph()
        if not paragraph_parts:
            paragraph_start_page = line.page
        paragraph_parts.append(line.text)
        paragraph_line_ids.append(line.source_id)
        paragraph_end_page = line.page
        prior = line
    flush_paragraph()
    if any(not section.paragraphs for section in sections):
        raise PdfProcessingError("selected PDF produced an empty section")
    return sections


def apply_section_policy(
    sections: list[_DraftSection], *, max_section_chars: int = MAX_SECTION_CHARS
) -> list[_DraftSection]:
    """Retain small named sections and split oversized sections only between paragraphs."""

    if max_section_chars <= 0:
        raise ValueError("max_section_chars must be positive")
    result: list[_DraftSection] = []
    for section in sections:
        parts: list[list[ProcessedParagraph]] = [[]]
        part_size = 0
        for paragraph in section.paragraphs:
            paragraph_size = len(paragraph.text)
            if parts[-1] and part_size + paragraph_size > max_section_chars:
                parts.append([])
                part_size = 0
            parts[-1].append(paragraph)
            part_size += paragraph_size
        for part_number, paragraphs in enumerate(parts, start=1):
            title = section.title if len(parts) == 1 else f"{section.title} (Part {part_number})"
            result.append(
                _DraftSection(
                    title,
                    section.boundary_source,
                    section.source_line_ids if part_number == 1 else (),
                    paragraphs,
                )
            )
    return result


def build_document_map(sections: tuple[ProcessedSection, ...]) -> tuple[DocumentMapEntry, ...]:
    """Bound the orientation map and make omitted section titles explicit."""

    entries: list[DocumentMapEntry] = []
    used_chars = 0
    for section in sections:
        if (
            len(entries) >= DOCUMENT_MAP_MAX_ENTRIES
            or used_chars + len(section.title) > DOCUMENT_MAP_MAX_CHARS
        ):
            break
        entries.append(DocumentMapEntry(section.order, section.title))
        used_chars += len(section.title)
    omitted = len(sections) - len(entries)
    if omitted:
        entries.append(DocumentMapEntry(None, f"[{omitted} section titles omitted]", omitted))
    return tuple(entries)


def canonical_paragraphs(document: ProcessedDocument) -> tuple[ProcessedParagraph, ...]:
    """Expose the one canonical traversal used by future persistence and reader work."""

    return document.paragraphs


def join_lines(parts: list[str]) -> str:
    text = ""
    for part in parts:
        if text.endswith("-"):
            prior_token = text.rsplit(" ", 1)[-1]
            if "/" in prior_token:
                text += part
            elif part[:1].islower():
                text = text[:-1] + part
            else:
                text += part
        else:
            text = f"{text} {part}" if text else part
    return re.sub(r"(?<=\w)-\s+(?=[a-z])", "", text).strip()


def _split_paragraph(
    text: str, start_page: int, end_page: int, source_ids: tuple[str, ...]
) -> list[ProcessedParagraph]:
    if len(text) <= MAX_PARAGRAPH_CHARS:
        return [ProcessedParagraph(0, text, start_page, end_page, source_ids)]
    pieces: list[str] = []
    remaining = text
    while len(remaining) > MAX_PARAGRAPH_CHARS:
        candidates = [
            match.end()
            for match in re.finditer(r"(?<=[.!?])\s+", remaining[: MAX_PARAGRAPH_CHARS + 1])
        ]
        split_at = (
            candidates[-1]
            if candidates
            else remaining.rfind(" ", 0, MAX_PARAGRAPH_CHARS + 1)
        )
        if split_at <= 0:
            split_at = MAX_PARAGRAPH_CHARS
        pieces.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    pieces.append(remaining)
    return [
        ProcessedParagraph(0, piece, start_page, end_page, source_ids if index == 0 else ())
        for index, piece in enumerate(pieces)
    ]


def _finalize_sections(drafts: list[_DraftSection]) -> tuple[ProcessedSection, ...]:
    paragraph_order = 0
    sections: list[ProcessedSection] = []
    for section_order, draft in enumerate(drafts, start=1):
        paragraphs: list[ProcessedParagraph] = []
        for paragraph in draft.paragraphs:
            paragraph_order += 1
            paragraphs.append(
                ProcessedParagraph(
                    paragraph_order,
                    paragraph.text,
                    paragraph.start_page,
                    paragraph.end_page,
                    paragraph.source_line_ids,
                )
            )
        if not paragraphs:
            raise PdfProcessingError("selected PDF produced an empty section")
        sections.append(
            ProcessedSection(
                section_order,
                draft.title,
                draft.boundary_source,
                paragraphs[0].order,
                tuple(paragraphs),
                draft.source_line_ids,
            )
        )
    return tuple(sections)


def _assert_invariants(lines: list[LayoutLine], sections: tuple[ProcessedSection, ...]) -> None:
    paragraphs = [paragraph for section in sections for paragraph in section.paragraphs]
    if [paragraph.order for paragraph in paragraphs] != list(range(1, len(paragraphs) + 1)):
        raise PdfProcessingError("selected PDF paragraph order is not contiguous")
    retained_ids = [line.source_id for line in lines]
    canonical_ids: list[str] = []
    for section in sections:
        canonical_ids.extend(section.source_line_ids)
        for paragraph in section.paragraphs:
            canonical_ids.extend(paragraph.source_line_ids)
    if (
        len(retained_ids) != len(set(retained_ids))
        or Counter(canonical_ids) != Counter(retained_ids)
    ):
        raise PdfProcessingError("selected PDF source lines were omitted or duplicated")
    if canonical_ids != retained_ids:
        raise PdfProcessingError("selected PDF source lines were reordered")
    normalized = "\n\n".join(paragraph.text for paragraph in paragraphs)
    signature_phrases = (
        "done in Convention",
        "The Word, “the,” being interlined",
        "DELAWARE",
        "NEW HAMPSHIRE",
    )
    try:
        positions = [normalized.index(phrase) for phrase in signature_phrases]
    except ValueError as error:
        raise PdfProcessingError("selected PDF signature-page text is incomplete") from error
    if positions != sorted(positions) or any(
        artifact in normalized for artifact in ("interlined between in Convention", "Sep-Page")
    ):
        raise PdfProcessingError("selected PDF signature-page reading order is unsafe")


def _modal[T](values: Sequence[T], default: T) -> T:
    if not values:
        return default
    counts = Counter(values)
    maximum = max(counts.values())
    return next(value for value in values if counts[value] == maximum)


def _begins_amendments_front_matter(line: LayoutLine, current: _DraftSection | None) -> bool:
    return (
        line.page >= 13
        and line.text == "A"
        and current is not None
        and current.title == "Article VII"
    ) or (
        line.text == "MENDMENTS TO THE"
        and current is not None
        and current.title != "Amendments front matter"
    )
