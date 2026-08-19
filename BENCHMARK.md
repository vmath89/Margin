# Initial development document and benchmark — M0-T04

## Selected document

The initial development and evaluation document is *The Constitution of the United States of
America — Literal Print*, published by the U.S. Government Publishing Office and made available
by Congress.gov.

- **Canonical source:** <https://constitution.congress.gov/static/files/Literal_Print_of_Constitution_MCT_1.9.26.pdf>
- **Source page:** <https://constitution.congress.gov/>
- **Development download:** 2026-08-19
- **Downloaded SHA-256:** `4d85f1cbfcb9789f10bf306e379e97ff150ea235249190a188b0c05923fd6f19`
- **Use permission:** The Constitution is a public-domain U.S. government primary source. The PDF states that its text, spelling, and punctuation follow the National Archives' high-resolution founding-document downloads. Retain the source attribution when presenting it.

The PDF is intentionally not committed: it is a 220 KB public source artifact, and the canonical
URL plus checksum identify the exact development input.

### Why this is representative

This is approachable general-interest nonfiction about everyday civic life: how laws are made,
how the federal branches work, and basic individual rights. Its language rewards explanation but
does not require a reader to have specialist knowledge beforehand. The 20-page PDF has an
immediately recognizable structure—Preamble, seven Articles, and Amendments—so it remains a
useful test of section detection, paragraph anchoring, current-section explanation, and
conversational follow-ups. It is also short enough for repeatable early development runs.

This selection does not expand V0 support: it is an ordinary, unencrypted, text-based PDF; it is
not a representative sample of image-only, encrypted, malformed, or general arbitrary PDFs.

### Text-extraction inspection

On 2026-08-19, the official PDF was inspected with `pypdf`'s native text extraction only—no OCR
was invoked. The 20-page PDF yielded 58,237 characters and correctly exposed the Preamble,
Articles, numbered sections, and Amendments in source order. The selected passages below were
manually inspected in the extract:

| Passage | Locator in PDF | Manual inspection result | Difficulty |
| --- | --- | --- | --- |
| P1 — Preamble | PDF p. 2 | The extract preserves the Preamble's stated aims, including union, justice, tranquility, common defense, general welfare, and liberty. | Introductory civic concepts |
| P2 — Making a law | PDF p. 4, Article I, §7 | The extract preserves the House/Senate passage, presidential approval or objections, and two-thirds reconsideration. | Intermediate institutional reasoning |
| P3 — Executive branch | PDF p. 7, Article II, §1 | The extract preserves the four-year presidential term, Electoral College process, eligibility requirements, and succession text. | Intermediate constitutional structure |
| P4 — Individual rights | PDF p. 14, Amendments I–V | The extract preserves the First Amendment's speech, press, assembly, and petition protections and the Fourth Amendment's search-and-warrant language. | Familiar wording with legal nuance |
| P5 — Equal protection | PDF p. 16, Amendment XIV, §1 | The extract preserves citizenship, privileges or immunities, due process, and equal-protection language. | Advanced civic/legal reasoning |

This is a manual suitability check, not the M1 extraction spike. M1-T02 must still validate
`pypdf` metadata/outline handling and `pdfplumber` layout extraction, paragraph reconstruction,
and ordering against this same file.

## Benchmark protocol

For every primary question, begin a new conversational episode at the stated anchor. Supply
only the RFC-selected context scope, then evaluate the answer with the notes below. A follow-up
keeps the anchor unchanged and supplies only bounded complete turns from that same episode.
The Constitution's text is authoritative; the document map and a generated section synopsis are
orientation aids, not evidence for a precise claim.

| ID | Anchor and scope | Question | Expected source evidence / evaluation notes |
| --- | --- | --- | --- |
| B1 — explanation | P1; local passage | “Can you explain the Preamble in everyday language? What is it trying to say the Constitution is for?” | Explain the listed aims from P1, distinguishing the text's stated purposes from claims about specific later legal effects. Make the language accessible without flattening its ideas. |
| B2 — authorial intent | P2; local passage | “What constitutional design does this passage appear to be aiming for by requiring both houses and then involving the President?” | Treat intent as an interpretation of P2's procedure, not a claim about the private motives of the framers. Identify the textual sequence and clearly label any inference about checks or deliberation. |
| B3 — illustrative example | P2; local passage | “Give me a simple made-up example of how a bill could become law after the President objects to it.” | Use P2's House, Senate, presidential-objection, and two-thirds requirements as evidence. Label the scenario and names as an illustration, not an event described by the Constitution. |
| B4 — counterargument | P3; local passage | “What is a reasonable criticism someone might make of this presidential-selection process, and how is that criticism different from what the text itself says?” | Ground the process description in P3. Clearly separate a reasoned critique from the source text; do not attribute the critique to the Constitution. |
| B5 — current-section synthesis | P2; **current section** (Article I) | “Looking at Article I as a whole, what powers does it give Congress, and what steps or limits does it place on how Congress uses those powers?” | This is the required section-context benchmark. It needs the whole bounded Article I, including legislative vesting, bicameral structure, bill process, enumerated powers, and limits—not only P2's anchored paragraph. Do not make claims about later court interpretations unless they are labeled background. |

### Follow-up sequence S1 — explanation continuity

Start at P1.

1. Ask B1.
2. While still paused in the same episode, ask: “Which parts of your explanation describe goals, and which parts would you need later constitutional text to turn into a specific rule?”

Use the unchanged P1 anchor and B1's complete answer as bounded recent dialogue. The answer should
clarify the distinction between the Preamble's stated aims and a specific operative provision,
without inventing a legal rule or claiming support from an unsupplied Article or Amendment.

### Follow-up sequence S2 — institutional connection

Start at P2.

1. Ask B5.
2. While still paused in the same episode, ask: “How does the bill process you just described connect to the broader idea that legislative power belongs to Congress?”

Retain P2 as the reading-position anchor and use only B5's complete turn as recent dialogue. The
answer should connect Article I's vesting of legislative power and its prescribed bill process;
it must not pull in claims from a different Article without supplied evidence.

## Evaluation rubric

Evaluate each response qualitatively; this ticket does not create automated grading or prescribe
model wording.

| Dimension | What to look for |
| --- | --- |
| Grounding | Precise claims about the Constitution are supported by the selected supplied text. The answer does not turn document orientation, a synopsis, or unsupplied text into evidence. |
| Usefulness | The response directly addresses the reader's question, defines necessary terms, and translates unfamiliar phrasing into clear everyday language. |
| Depth | Detail matches the request: it explains the reasoning and relevant trade-offs while distinguishing the text, interpretation, background, and illustrative examples. |
| Conversational continuity | In S1 and S2, the follow-up uses the same anchor and relevant prior answer naturally, does not repeat needlessly, and does not draw on another episode. |

For a question that asks where else an idea appears in the document, evaluate the V0 limitation
instead: the answer must say that full-document retrieval is unavailable and cannot verify other
locations. It may discuss only the supplied orientation, section, local passage, and same-episode
dialogue as clearly limited context.

## V0 success-criteria review

The benchmark exercises the core V0 validation path in `ROADMAP.md`: a supported text-based
PDF can be narrated in order; the reader can pause at P1–P5, ask a spoken version of each
question, hear a grounded answer, ask one of the two follow-ups, and continue from the original
paragraph. It deliberately tests local context (B1–B4), full current-section context (B5), and
same-episode dialogue (S1–S2), without requiring full-document retrieval.
