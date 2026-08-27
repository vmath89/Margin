from __future__ import annotations

from pathlib import Path

import pytest

from margin_api.pdf_processing import (
    LayoutLine,
    PdfProcessingError,
    canonical_paragraphs,
    join_lines,
    process_pdf,
    reconstruct_document,
)


def line(
    source_id: str,
    text: str,
    *,
    page: int = 1,
    top: float = 100.0,
    font_size: float = 10.0,
    font_name: str = "Roman",
) -> LayoutLine:
    return LayoutLine(source_id, page, top, top + 8, 30.0, text, font_size, font_name)


def test_fallback_sections_preserve_every_line_in_canonical_order() -> None:
    lines = [
        line("p1:1", "One complete paragraph.", top=50),
        line("p1:2", "A second complete paragraph.", top=80),
    ]

    sections = reconstruct_document(lines, [])

    assert [section.boundary_source for section in sections] == ["fallback"]
    assert [paragraph.text for paragraph in sections[0].paragraphs] == [
        "One complete paragraph.",
        "A second complete paragraph.",
    ]
    assert [
        source_id for paragraph in sections[0].paragraphs for source_id in paragraph.source_line_ids
    ] == [
        "p1:1",
        "p1:2",
    ]


def test_outline_boundaries_are_retained_without_reordering_source() -> None:
    lines = [
        line("p1:1", "First source paragraph.", page=1),
        line("p2:1", "Second source paragraph.", page=2),
    ]

    sections = reconstruct_document(lines, [("Opening", 1), ("Next", 2)])

    assert [(section.title, section.boundary_source) for section in sections] == [
        ("Opening", "outline"),
        ("Next", "outline"),
    ]
    assert [paragraph.text for section in sections for paragraph in section.paragraphs] == [
        "First source paragraph.",
        "Second source paragraph.",
    ]


def test_nested_outline_titles_sharing_a_page_are_flattened_without_loss() -> None:
    lines = [
        line("p1:1", "First source paragraph.", page=1),
        line("p2:1", "Second source paragraph.", page=2),
    ]

    sections = reconstruct_document(
        lines,
        [("Chapter one", 1), ("Scope", 1), ("Chapter two", 2)],
    )

    assert [section.title for section in sections] == [
        "Chapter one — Scope",
        "Chapter two",
    ]
    assert [paragraph.text for section in sections for paragraph in section.paragraphs] == [
        "First source paragraph.",
        "Second source paragraph.",
    ]


def test_partial_outline_falls_back_to_consistent_headings() -> None:
    body = "Readable body text. " * 60
    lines = [
        line("heading-1", "First heading", top=50, font_size=18.0),
        line("body-1", body, top=90),
        line("heading-2", "Second heading", top=200, font_size=18.0),
        line("body-2", body, top=240),
    ]

    sections = reconstruct_document(lines, [("Incidental bookmark", 1)])

    assert [section.title for section in sections] == ["First heading", "Second heading"]
    assert [section.boundary_source for section in sections] == ["heading", "heading"]


def test_committed_constitution_regression_fixture_is_processed_without_identity_policy() -> None:
    document = process_pdf(Path(__file__).parent / "fixtures" / "constitution.pdf")

    paragraphs = canonical_paragraphs(document)
    text = "\n\n".join(paragraph.text for paragraph in paragraphs)
    assert document.sections
    assert paragraphs
    assert [paragraph.order for paragraph in paragraphs] == list(range(1, len(paragraphs) + 1))
    assert document.document_map
    # The signature page has two upper text blocks followed by two signer columns.
    # Its semantic reading order is intentionally not raw y/x extraction order.
    assert text.index("done in Convention") < text.index("The Word, “the,” being interlined")
    assert text.index("The Word, “the,” being interlined") < text.index("DELAWARE")
    assert text.index("DELAWARE") < text.index("NEW HAMPSHIRE")
    assert "interlined between in Convention" not in text
    assert "Sep-Page" not in text


@pytest.mark.parametrize(
    ("name", "boundary_source"),
    [("text-with-outline.pdf", "outline"), ("text-without-outline.pdf", "fallback")],
)
def test_text_pdf_fixtures_are_lossless_and_ordered(name: str, boundary_source: str) -> None:
    document = process_pdf(Path(__file__).parent / "fixtures" / name)

    paragraphs = canonical_paragraphs(document)
    assert paragraphs
    assert any(section.boundary_source == boundary_source for section in document.sections)
    assert [paragraph.order for paragraph in paragraphs] == list(range(1, len(paragraphs) + 1))
    assert len({paragraph.text for paragraph in paragraphs}) == len(paragraphs)


def test_image_only_fixture_is_rejected_without_partial_text() -> None:
    with pytest.raises(PdfProcessingError, match="no extractable text"):
        process_pdf(Path(__file__).parent / "fixtures" / "image-only.pdf")


def test_encrypted_fixture_is_rejected_with_an_actionable_error() -> None:
    with pytest.raises(PdfProcessingError, match="encrypted"):
        process_pdf(Path(__file__).parent / "fixtures" / "encrypted-text.pdf")


def test_malformed_pdf_has_a_plain_language_failure(tmp_path: Path) -> None:
    candidate = tmp_path / "malformed.pdf"
    candidate.write_bytes(b"%PDF-1.7 malformed")

    with pytest.raises(PdfProcessingError, match="could not be opened"):
        process_pdf(candidate)


def test_extracted_document_text_over_configured_limit_is_rejected() -> None:
    candidate = Path(__file__).parent / "fixtures" / "text-without-outline.pdf"

    with pytest.raises(PdfProcessingError, match="configured limit"):
        process_pdf(candidate, max_document_characters=20)


def test_hyphen_normalization_preserves_lexical_hyphens() -> None:
    assert join_lines(["Govern-", "ment"]) == "Government"
    assert join_lines(["Vice- President"]) == "Vice- President"
    assert join_lines(["https://example.org/a-", "path"]) == "https://example.org/a-path"


def test_heading_sections_require_substantial_content_after_consistent_candidates() -> None:
    body = "Readable body text. " * 60
    lines = [
        line("heading-1", "First heading", top=50, font_size=18.0),
        line("body-1", body, top=90),
        line("heading-2", "Second heading", top=200, font_size=18.0),
        line("body-2", body, top=240),
    ]

    sections = reconstruct_document(lines, [])

    assert [section.boundary_source for section in sections] == ["heading", "heading"]
    assert [section.title for section in sections] == ["First heading", "Second heading"]


def test_short_or_running_heading_candidates_use_fallback_sections() -> None:
    lines = [
        line("heading-1", "First heading", top=50, font_size=18.0),
        line("body-1", "Short body.", top=90),
        line("heading-2", "Second heading", top=200, font_size=18.0),
        line("body-2", "Another short body.", top=240),
    ]

    sections = reconstruct_document(lines, [])

    assert [section.boundary_source for section in sections] == ["fallback"]
