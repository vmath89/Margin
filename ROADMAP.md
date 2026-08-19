# Margin Product Roadmap

## Purpose

Margin is an AI reading companion for difficult nonfiction. Its V0 must prove that a reader can listen to a document, pause at a difficult passage, have a grounded spoken conversation about it, and continue reading without losing their place.

The roadmap translates the product thesis and V0 RFC into measurable engineering milestones. It is intentionally limited to the smallest product that can test the core experience.

## Working principles

- Build vertical slices that can be demonstrated end to end.
- Treat the current paragraph as the reading-position anchor, not as the limit of model context.
- Validate the conversational experience before broadening document support.
- Keep context explicit, bounded, inspectable, and grounded in the uploaded document.
- Add infrastructure only when it solves a current V0 requirement.
- Use one active implementation ticket at a time unless work is demonstrably independent.
- A milestone is complete only when its integrated outcome can be demonstrated.

## V0 success criteria

V0 succeeds when a user can:

1. Upload a supported text-based PDF.
2. Listen to ordered document narration.
3. Pause at a passage and ask a spoken question.
4. Receive a useful answer grounded in local, section, and lightweight document context.
5. Ask at least one natural follow-up question while remaining anchored to the passage.
6. Hear the answers and continue narration from the correct reading position.
7. Use the product on a real difficult document and prefer the integrated loop to manually switching between a reader and a general-purpose assistant.

## Milestones

### M0 — Product and architecture alignment

**Outcome:** The thesis, RFC, and architecture describe the same V0 product and define a testable conversational experience.

**Exit criteria:**

- The RFC distinguishes the reading anchor from the context boundary.
- Sequential follow-up questions are explicitly part of V0.
- The document, section, local, and conversation context layers are defined.
- Book-wide retrieval limitations are stated without implying false document knowledge.
- One initial PDF and a benchmark question set are selected for development and evaluation.
- Architecture invariants and the definition of done agree with the revised RFC.

**Baseline approval:** M0-T05 confirms these criteria against the approved PDF and benchmark
in `BENCHMARK.md`. V0 is a single-user, text-based-PDF product with explicit controls and a
bounded same-episode conversation; its broader thesis aspirations remain deferred.

### M1 — Application foundation and capability validation

**Outcome:** The web and API applications run locally, persist basic domain data, communicate through a stable boundary, and have verified seams for PDF extraction and model capabilities.

**Exit criteria:**

- Next.js and FastAPI start using documented local commands.
- The browser reaches FastAPI through same-origin `/api` routing.
- SQLite, SQLAlchemy, and Alembic are configured.
- The initial document, section, paragraph, interaction, and conversation schema exists.
- Application services can use deterministic fake reasoning, transcription, and speech operations.
- Focused spikes verify the selected PDF, STT input format, TTS output, and reasoning context outside the product flow.
- Automated checks run through a documented verification command or procedure.

### M2 — PDF reader and narration

**Outcome:** A user can upload the selected supported PDF, listen paragraph by paragraph, pause, navigate backward, and resume from a persisted anchor.

**Exit criteria:**

- Upload and processing states are visible.
- Extracted sections and paragraphs remain ordered and lossless.
- The active paragraph is displayed and highlighted.
- Paragraph audio is generated on demand and the next paragraph is prefetched.
- Pause, previous paragraph, playback speed, and resume work.
- Reading position survives a page reload.

### M3 — Grounded question and answer

**Outcome:** A user can pause narration, ask one spoken question about the anchored passage, see and hear a grounded answer, and continue reading.

**Exit criteria:**

- Browser audio is recorded and transcribed.
- Context includes document orientation, current-section context, a local passage window, and the question.
- The textual interaction is stored exactly once.
- Answer audio is generated separately and can be retried.
- Continue resumes from the recorded paragraph.

### M4 — Multi-turn conversational reading

**Outcome:** While narration is paused, the user can ask sequential follow-up questions that retain the passage anchor and relevant recent dialogue.

**Exit criteria:**

- Follow-ups remain associated with one conversational episode.
- The context builder includes a bounded recent dialogue history.
- The user can ask, hear an answer, ask again, and then continue.
- Continuing closes the active conversational episode without losing stored interactions.
- The benchmark follow-up questions produce coherent, grounded responses.

### M5 — V0 hardening and dogfooding

**Outcome:** The complete V0 loop is reliable enough for repeated use on a real difficult document and produces evidence for V1 prioritization.

**Exit criteria:**

- The end-to-end happy path is covered by a browser test using fake model operations.
- Important processing, network, and model failures have clear retry behavior.
- Logs and diagnostics avoid storing full sensitive passages or audio.
- The product is used in several real reading sessions.
- Observed failures, latency, answer quality, and desired capabilities are recorded.
- V1 work is selected from evidence rather than assumed in advance.

## Explicitly deferred until evidence supports them

- Full-document retrieval and vector search.
- Cross-document connections and learner memory.
- Autonomous or multi-agent orchestration.
- Real-time speech-to-speech interaction.
- Interrupting an answer while it is playing.
- Sentence-level audio alignment and resume.
- OCR and broad support for malformed or image-only PDFs.
- Authentication, multi-user isolation, billing, and production-scale infrastructure.
- Native mobile, EPUB, Kindle, and publisher integrations.

## Planning horizon

Only M0 and M1 are decomposed into implementation-ready tickets in `TASKS.md`. Later milestones remain outcome-level plans until discoveries from the preceding milestone make responsible decomposition possible.
