from __future__ import annotations

from pathlib import Path

import pytest

from margin_api.pdf_processing import (
    DOCUMENT_MAP_MAX_ENTRIES,
    LayoutLine,
    PdfProcessingError,
    ProcessedParagraph,
    _DraftSection,
    apply_section_policy,
    canonical_paragraphs,
    join_lines,
    process_selected_pdf,
    reconstruct_selected_pdf,
)


def line(source_id: str, text: str, *, page: int = 1, top: float = 100.0) -> LayoutLine:
    return LayoutLine(source_id, page, top, top + 8, 30.0, text, 10.0, "Roman")


def test_reconstruction_preserves_selected_heading_and_line_order() -> None:
    lines = [
        line("p1:1", "Cover text", top=50),
        line("p1:2", "Article. I.", top=75),
        line("p1:3", "Section 1. The legislative Power shall be vested.", top=100),
        line("p1:4", "Section 2. The House shall choose their Speaker.", top=125),
    ]

    sections = reconstruct_selected_pdf(lines)

    assert [section.title for section in sections] == ["Front matter", "Article I"]
    assert sections[1].source_line_ids == ("p1:2",)
    assert [paragraph.text for paragraph in sections[1].paragraphs] == [
        "Section 1. The legislative Power shall be vested.",
        "Section 2. The House shall choose their Speaker.",
    ]
    consumed: list[str] = []
    for section in sections:
        consumed.extend(section.source_line_ids)
        for paragraph in section.paragraphs:
            consumed.extend(paragraph.source_line_ids)
    assert consumed == ["p1:1", "p1:2", "p1:3", "p1:4"]


def test_section_policy_keeps_small_named_sections_and_splits_only_at_paragraphs() -> None:
    paragraphs = [
        ProcessedParagraph(0, "one" * 4, 1, 1, ("one",)),
        ProcessedParagraph(0, "two" * 4, 1, 1, ("two",)),
        ProcessedParagraph(0, "three" * 4, 1, 1, ("three",)),
    ]
    drafts = [
        _DraftSection("Amendment I", "heading", ("heading",), [paragraphs[0]]),
        _DraftSection("Article I", "heading", ("article",), paragraphs[1:]),
    ]

    sections = apply_section_policy(drafts, max_section_chars=20)

    assert [section.title for section in sections] == [
        "Amendment I",
        "Article I (Part 1)",
        "Article I (Part 2)",
    ]
    assert [paragraph.text for section in sections for paragraph in section.paragraphs] == [
        paragraph.text for paragraph in paragraphs
    ]
    assert sections[2].source_line_ids == ()


def test_document_map_marks_omitted_sections() -> None:
    fixture = Path("var/spikes/m1-t02/constitution.pdf")
    if not fixture.exists():
        pytest.skip("selected PDF fixture is not available")

    document = process_selected_pdf(fixture)

    assert len(document.document_map) == DOCUMENT_MAP_MAX_ENTRIES + 1
    assert document.document_map[-1].omitted_sections == (
        len(document.sections) - DOCUMENT_MAP_MAX_ENTRIES
    )
    assert document.document_map[-1].title.endswith("section titles omitted]")


def test_selected_pdf_is_lossless_ordered_and_signature_safe() -> None:
    fixture = Path("var/spikes/m1-t02/constitution.pdf")
    if not fixture.exists():
        pytest.skip("selected PDF fixture is not available")

    document = process_selected_pdf(fixture)
    paragraphs = canonical_paragraphs(document)
    text = "\n\n".join(paragraph.text for paragraph in paragraphs)

    assert document.source_sha256 == (
        "4d85f1cbfcb9789f10bf306e379e97ff150ea235249190a188b0c05923fd6f19"
    )
    assert len(document.sections) == 37
    # The spike's 154 raw reconstructed paragraphs become 155 after the
    # architecture's 2,000-character, sentence-aware paragraph limit.
    assert len(paragraphs) == 155
    assert [paragraph.order for paragraph in paragraphs] == list(range(1, len(paragraphs) + 1))
    assert [section.first_paragraph_order for section in document.sections] == [
        section.paragraphs[0].order for section in document.sections
    ]
    assert text.index("done in Convention") < text.index("The Word, “the,” being interlined")
    assert (
        text.index("The Word, “the,” being interlined")
        < text.index("DELAWARE")
        < text.index("NEW HAMPSHIRE")
    )
    assert "interlined between in Convention" not in text
    assert "Sep-Page" not in text


def test_unsupported_checksum_fails_clearly(tmp_path: Path) -> None:
    candidate = tmp_path / "other.pdf"
    candidate.write_bytes(b"not the selected pdf")

    with pytest.raises(PdfProcessingError, match="checksum"):
        process_selected_pdf(candidate)


def test_hyphen_normalization_preserves_lexical_hyphens() -> None:
    assert join_lines(["Govern-", "ment"]) == "Government"
    assert join_lines(["Vice- President"]) == "Vice- President"
    assert join_lines(["https://example.org/a-", "path"]) == "https://example.org/a-path"
