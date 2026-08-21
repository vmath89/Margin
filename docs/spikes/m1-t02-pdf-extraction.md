# M1-T02 PDF extraction spike

## Decision

`pypdf` and `pdfplumber` are sufficient for the selected Constitution PDF without OCR.
Use `pypdf` for metadata and outline inspection, but do not trust this file's outline as semantic
structure. Use `pdfplumber` layout lines, typography, spacing, and numbered-heading text to build
the ordered paragraph stream and detected sections. The selected PDF's signature page requires an
explicit four-region reading order; the spike applies and regression-checks that order. Retain the
original PDF because decorative titles, line-end hyphenation, and generalized multi-column layout
still require explicit normalization rules and regression fixtures in the production processor.

This report evaluates only the selected development PDF. It does not establish generalized support
for arbitrary PDFs or implement the upload pipeline.

## Reproduction

Input: the public-domain PDF and SHA-256 pinned in `BENCHMARK.md`.

```sh
mkdir -p var/spikes/m1-t02
curl --fail --location \
  https://constitution.congress.gov/static/files/Literal_Print_of_Constitution_MCT_1.9.26.pdf \
  --output var/spikes/m1-t02/constitution.pdf
shasum -a 256 var/spikes/m1-t02/constitution.pdf
uv run --python 3.12 \
  --with pypdf==6.1.1 \
  --with pdfplumber==0.11.7 \
  python docs/spikes/m1-t02_extract.py var/spikes/m1-t02/constitution.pdf --json
```

The original run used CPython 3.12.11 and `uv` 0.8.13. The corrected measurements were verified
again with CPython 3.12.13, `pypdf` 6.1.1, and `pdfplumber` 0.11.7. The script rejects any input
whose checksum differs from
`4d85f1cbfcb9789f10bf306e379e97ff150ea235249190a188b0c05923fd6f19`.

## Measurements

| Measurement | Result |
| --- | ---: |
| PDF pages | 20 |
| `pypdf` plain extracted characters | 48,438 |
| `pypdf` layout extracted characters | 58,267 |
| Retained `pdfplumber` layout lines | 737 |
| Median body font size | 10 pt |
| Normalized paragraph characters | 47,727 |
| Normalized paragraphs | 154 |
| Ordered sections | 37 |
| Canonical serialization characters before prompt instructions | 53,125 |

The normalized-corpus number is reproducibly defined as every normalized paragraph joined in
global paragraph order with two newline characters between paragraphs. It excludes repeated running
headers, printed page-number furniture, and section-heading text represented by section markers.
The canonical serialization measurement adds one section marker and one paragraph/page marker per
record. It includes each section and paragraph once and does not also append a second local or
page-ordered text stream.

The earlier 58,237-character note in `BENCHMARK.md` was neither the normalized corpus nor
reproducible with the pinned input and library version. The current `pypdf` layout-mode raw count is
58,267; the budget-relevant normalized source is 47,727 characters. `BENCHMARK.md` now uses the
measured normalized value. The 53,125-character marked source is the base input for B6/B7 budget
work; M1-T05 must still measure the exact assembled prompt with instructions, orientation, complete
session dialogue, question, answer reserve, and safety margin. A fitting B6 configuration needs an
allowance at least as large as that complete candidate, while B7 deliberately configures a lower
allowance. Page count is not used in either decision.

## Metadata and outline

`pypdf` reports author `U.S. GOVERNMENT PUBLISHING OFFICE`, creator `GPO`, producer
`PDFlib+PDI 9.2.0 (Win64)`, creation/modification date `2026-02-09`, and an empty title. The title
therefore has to come from visible source text or an application fallback; metadata alone cannot
provide document orientation.

The outline has 24 flat entries. Twenty resolve to PDF pages and four have null destinations. Every
title is an internal production label such as `For Print FINAL_CONAN_2025_suppl 13`, not a Preamble,
Article, or Amendment title. The outline preserves a mostly physical-page sequence but is unusable
for the flat semantic navigation contract. Heading detection or fallback sectioning is required for
this PDF.

## Layout, paragraphs, headings, and hyphenation

The body is predominantly 10 pt `NewCenturySchlbk-Roman`. Article and Amendment headings form a
consistent centered, bold 11 pt series, and the Preamble has a distinctive 14 pt opening. The spike
uses those textual heading series to create a front-matter fallback, Preamble, Articles I–VII, an
Amendments front-matter section, and Amendments I–XXVII. This produces 37 ordered sections.

Paragraph reconstruction uses layout order plus these selected-document signals:

- a vertical gap of at least 10 points;
- an explicit `Section 1.` / `Section. 1.` start;
- a completed paragraph at a page boundary;
- an Article or Amendment heading boundary;
- continuation across a page when the preceding line is not complete.

PDF p. 11 is the selected file's one complex-layout exception. The spike extracts its constitutional
closing statement, marginal attestation, left signer column, and right signer column as four
non-overlapping regions in that reading order. Regression assertions require those blocks to remain
ordered and reject the earlier cross-column artifacts `interlined between in Convention` and
`Sep-Page`.

Repeated running headers and printed footer page numbers are identified as page furniture and
removed. Line-end words such as `Govern-` / `ment` and inline extraction artifacts such as
`Represent- atives` are joined. A line-broken URL retains its real hyphen, and uppercase compounds
such as `Vice-President` retain theirs. Production code needs focused fixtures because typography
alone cannot prove whether every hyphen is lexical or layout-introduced.

Every retained layout line has a stable run-local source ID. The ordered-walk assertions compare
those IDs with the section-marker and paragraph walk, proving that each retained line is consumed
exactly once in the same canonical order. Separate assertions verify contiguous global paragraph
order, unique paragraph ownership, and one deterministic first paragraph for every section. The
semantic sections range from the short Amendment VIII (111 source characters) to Article I
(13,133). Consequently the production processor must apply the architecture's minimum/maximum
section policy deliberately:
small genuine headings may need deterministic consolidation, and oversized detected sections must
be split only at paragraph boundaries. Whatever policy is selected must retain this single ordered
paragraph stream.

## Benchmark locations and manual comparison

| Passage | Extracted marker | Source comparison |
| --- | --- | --- |
| P1 | Preamble, `paragraph_0004`, PDF p. 2 | Stated aims and their order match the visible Preamble. |
| P2 | Article I, `paragraph_0027`, PDF p. 4 | House, Senate, President, objections, reconsideration, and two-thirds sequence match. |
| P3 | Article II, `paragraph_0058`, `paragraph_0062`, and `paragraph_0063`, PDF p. 7 | Executive vesting, four-year term, election text, eligibility requirements, and succession remain in source order. |
| P4 | Amendment I, `paragraph_0101`, and Amendment IV, `paragraph_0104`, PDF p. 14 | Speech/press/assembly/petition and search/warrant language match their visible amendments. |
| P5 | Amendment XIV, `paragraph_0115`, PDF p. 16 | Citizenship, privileges or immunities, due process, and equal protection match Section 1. |

PDF pages 2, 4, 7, 14, and 16 were rendered and compared manually with the extracted samples. No
benchmark phrase was omitted, duplicated, or materially reordered. Page and section markers agree
with the source. P3 intentionally resolves to three paragraphs because the benchmark spans the
election, eligibility, and succession provisions. P4 resolves to two paragraphs because the
benchmark names rights in both Amendment I and Amendment IV.

## Representative extracted samples

Preamble (`P1`):

> We the People of the United States, in Order to form a more perfect Union, establish Justice,
> insure domestic Tranquility, provide for the common defence, promote the general Welfare, and
> secure the Blessings of Liberty to ourselves and our Posterity, do ordain and establish this
> Constitution for the United States of America.

Article I bill process (`P2`, excerpt):

> Every Bill which shall have passed the House of Representatives and the Senate, shall, before it
> become a Law, be presented to the President of the United States; If he approve he shall sign it,
> but if not he shall return it, with his Objections to that House in which it shall have originated
> ...

Amendment XIV (`P5`, excerpt):

> Section 1. All persons born or naturalized in the United States, and subject to the jurisdiction
> thereof, are citizens of the United States and of the State wherein they reside. No State shall
> make or enforce any law which shall abridge the privileges or immunities of citizens of the
> United States ...

## Constraints and follow-up implications

- Decorative small-caps cover titles are emitted as fragmented glyph runs (`T HE C ...`) by
  layout-line extraction. The legal prose is readable, but production title normalization needs an
  explicit fixture and must not silently rewrite body text.
- PDF p. 11 contains a multi-column attestation and signature block. Default line extraction merges
  its columns, so the selected-file spike uses checksum-pinned region coordinates to retain readable
  block order without omission. Production code must not generalize those coordinates: it needs
  column/block detection or a clear supported-PDF rejection rule. Generalized multi-column support
  remains outside this spike.
- The file's outline cannot supply semantic sections, and its empty title cannot supply document
  orientation. Both require visible-layout signals or deterministic fallbacks.
- Many genuine Amendment sections are shorter than the architecture's initial
  `MIN_SECTION_CHARS`. The production parsing ticket must define deterministic consolidation while
  retaining headings as markers and preserving flat navigation; the spike does not change the
  approved configuration.
- Page markers are physical PDF pages. The printed footer numbers are offset and are not a second
  page-order model.

These are implementation constraints for the later document-processing work, not reasons to add
OCR, arbitrary-PDF support, retrieval, persistence, or upload behavior to M1-T02.
