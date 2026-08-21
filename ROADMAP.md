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
4. Receive a useful answer grounded in local, section, and document-wide context when the complete
   normalized source safely fits; otherwise receive an honest limited-context answer.
5. Ask at least one natural follow-up question while remaining anchored to the passage.
6. Continue narration, pause later, and ask a question that naturally uses an earlier discussion from the same reading session.
7. Hear the answers and continue narration from the correct reading position.
8. Use the product on a real difficult document and prefer the integrated loop to manually switching between a reader and a general-purpose assistant.

## Milestones

### M0 — Product and architecture alignment

**Status:** Complete (`M0-T01` through `M0-T08` are Done.)

**Outcome:** The thesis, RFC, and architecture describe the same V0 product and define a testable conversational experience.

**Exit criteria:**

- The RFC distinguishes the reading anchor from the context boundary.
- Sequential follow-up questions are explicitly part of V0.
- The document, section, local, and whole-reading-session conversation context layers are defined.
- Conditional full-document context and its over-budget limited-context disclosure are stated
  without implying false document knowledge or retrieval.
- One initial PDF and a benchmark question set are selected for development and evaluation.
- Architecture invariants and the definition of done agree with the revised RFC.
- A reader can deterministically resume, start at the beginning, or start at any ordered detected
  or fallback section without compromising session dialogue or episode anchors.

**Baseline approval:** M0-T05 confirms these criteria against the approved PDF and benchmark
in `BENCHMARK.md`. V0 is a single-user, text-based-PDF product with explicit controls and a
persisted reading-session conversation spanning multiple pause episodes. M0-T06 supersedes the
original same-episode-only context boundary; cross-session learner memory remains deferred.
M0-T07 adds a bounded canonical full-document scope for explicit document-wide questions and
retains a clearly disclosed limited mode when the complete candidate prompt does not fit.
M0-T08 adds deterministic start and flat section navigation; richer navigation remains deferred.

### M1 — Application foundation and capability validation

**Status:** In progress (`M1-T01` is Done; `M1-T02` is Ready.)

**Outcome:** The web and API applications run locally, persist basic domain data, communicate through a stable boundary, and have verified seams for PDF extraction and model capabilities.

**Exit criteria:**

- Next.js and FastAPI start using documented local commands.
- The browser reaches FastAPI through same-origin `/api` routing.
- SQLite, SQLAlchemy, and Alembic are configured.
- The initial document, section, paragraph, reading-session, conversational-episode, and interaction schema exists.
- Application services can use deterministic fake reasoning, transcription, and speech operations.
- Focused spikes verify the selected PDF, STT input format, TTS output, and reasoning context outside the product flow.
- The reasoning spike exercises local, current-section, fitting full-document, and over-budget
  limited document-wide contexts, including same-session dialogue and deterministic prompt-budget
  behavior.
- Initial context-budget, answer-reserve, safety-margin, recording, and audio-cache configuration
  requirements are documented from measured capability behavior rather than page-count guesses.
- Automated checks run through a documented verification command or procedure.

### M2 — PDF reader and narration

**Status:** Not started; decompose near M1 completion.

**Outcome:** A user can upload the selected supported PDF, choose where to begin, listen paragraph by paragraph, pause, navigate by section or backward, and resume from a persisted anchor.

**Exit criteria:**

- Upload and processing states are visible.
- Extracted sections and paragraphs remain ordered and lossless.
- Before narration, the user can resume the saved paragraph, start at the beginning, or select any
  ordered detected or fallback section.
- Every selectable section exposes a stable ID, title, order, and first paragraph ID; invalid or
  cross-document selections fail clearly.
- The active paragraph is displayed and highlighted.
- Paragraph audio is generated on demand and the next paragraph is prefetched.
- Pause, previous paragraph, playback speed, section navigation, and resume work.
- Selecting a new section pauses narration and persists that section's first paragraph as the new
  reading position without creating a second source order or navigation model.
- Reading position survives a page reload.

### M3 — Grounded question and answer

**Status:** Not started; decompose near M2 completion.

**Outcome:** A user can pause narration, ask one spoken question at local, section, or document-wide scope, see and hear a grounded answer, and continue reading.

**Exit criteria:**

- Browser audio is recorded and transcribed.
- Scope selection is explicit, deterministic, and testable without a classifier or retrieval call.
- Local questions receive document orientation, current-section synopsis, the canonical local
  passage window, complete earlier active-session dialogue, and the current question.
- Current-section questions receive the complete bounded current section rather than an unused
  synopsis or duplicated local source context.
- Explicit document-wide questions receive the complete canonical document exactly once when the
  exact prompt fits the configured budget; otherwise they receive clearly disclosed limited
  document-wide context that does not imply complete-document analysis.
- Source and session dialogue are never silently truncated, sampled, duplicated, overlapped, or
  reordered to make a prompt fit.
- The uploaded source remains authoritative; prior model answers, section synopses, document maps,
  and general knowledge do not become unsupported source evidence.
- The textual interaction is stored exactly once.
- Answer audio is generated separately and can be retried.
- Continue resumes from the recorded paragraph.

### M4 — Session-continuous conversational reading

**Status:** Not started; decompose near M3 completion.

**Outcome:** The user can converse while paused, continue reading, and later begin a new anchored conversation that remembers every earlier discussion from the same reading session.

**Exit criteria:**

- Follow-ups remain associated with one conversational episode.
- A reading session contains multiple ordered conversational episodes.
- The context builder includes every complete earlier turn from the active reading session.
- A context-limit failure is explicit and never silently drops or summarizes an earlier session turn.
- The user can ask, hear an answer, ask again, and then continue.
- Continuing closes the active conversational episode without ending the reading session.
- After Continue, backward movement, or section navigation, the next Ask creates a new episode with
  the newly selected immutable paragraph anchor while retaining every earlier interaction from the
  active reading session.
- Navigation cannot mutate the anchor of an active conversational episode; that episode must end
  before the reading position changes.
- The benchmark same-episode and cross-episode questions produce coherent, grounded responses.

### M5 — V0 hardening and dogfooding

**Status:** Not started; decompose near M4 completion.

**Outcome:** The complete V0 loop is reliable enough for repeated use on a real difficult document and produces evidence for V1 prioritization.

**Exit criteria:**

- The end-to-end browser test using fake model operations covers upload, start-location selection,
  narration, pause, Ask, answer playback, same-episode follow-up, Continue, navigation to a new
  anchor, a later session-aware Ask, and resume.
- Deterministic tests cover local, section, fitting full-document, and over-budget limited
  document-wide scope behavior, including exact source ordering and context-limit failures.
- Important processing, network, and model failures have clear retry behavior.
- Logs and diagnostics avoid storing full sensitive passages or audio.
- Benchmark cases B1–B7 and S1–S3 are exercised against the implemented context contract, with live
  provider checks remaining explicit and opt-in.
- The product is used in several real reading sessions.
- Observed failures, latency, cost, answer quality, navigation friction, context-limit frequency,
  and desired capabilities are recorded.
- V1 work is selected from evidence rather than assumed in advance.

## Future idea stash — post-V0/V2 candidates

`FUTURE_IDEAS.md` is the source of truth for deferred concepts and their evidence-based revisit
conditions. Entries there are not roadmap commitments and cannot be implemented until an explicit
decision promotes them into this roadmap and creates actionable work in `TASKS.md`.

## Planning horizon

Only M0 and M1 are decomposed into implementation-ready tickets in `TASKS.md`. Later milestones remain outcome-level plans until discoveries from the preceding milestone make responsible decomposition possible.
