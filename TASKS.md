# Margin Engineering Backlog

## How to use this backlog

This file is the source of truth for planned work until an external issue tracker is introduced.

Allowed statuses:

- `Backlog` — understood but not ready to begin.
- `Ready` — sufficiently defined and all dependencies are complete.
- `In Progress` — the single ticket currently being implemented.
- `Blocked` — cannot proceed; the blocking condition must be recorded.
- `Done` — all acceptance criteria and verification requirements pass.

Working rules:

1. Keep at most one implementation ticket `In Progress` unless the work is explicitly independent.
2. Complete dependencies before changing a ticket to `Ready`.
3. Do not mark a ticket `Done` based only on code being written.
4. Record newly discovered work as a separate ticket instead of silently expanding scope.
5. Update this file in the same change that completes a ticket.

## Project-wide definition of done

An implementation ticket is done only when:

- Every acceptance criterion is satisfied.
- Relevant automated tests pass.
- User-visible behavior is manually verified when applicable.
- Errors and edge cases named in the ticket are handled.
- No unrelated files or behavior are changed.
- Documentation is updated when commands, configuration, behavior, or architectural decisions change.
- No unresolved placeholder is hiding work required by the ticket.
- The verification performed is recorded in the completion summary.

A documentation or research ticket is done when its stated artifact exists, inconsistencies are resolved, and its review criteria are satisfied.

---

# M0 — Product and architecture alignment

## M0-T01 — Revise the RFC around conversational episodes

**Status:** Done
**Depends on:** None

### Outcome

The V0 RFC tests conversational reading rather than only a one-shot passage explanation.

### Scope

- Define the paragraph as the reading-position anchor rather than the complete semantic context.
- Add sequential follow-up questions while reading remains paused.
- Define when a conversational episode begins and ends.
- Add recent dialogue to the reasoning-context description.
- Update the V0 definition of done and core-loop language.

### Out of scope

- Interruption while an AI answer is playing.
- Wake words, voice activity detection, or streaming speech-to-speech.
- Long-term conversation or learner memory.
- Application implementation.

### Acceptance criteria

- The RFC explicitly supports `Ask → Answer → Follow-up → Answer → Continue`.
- The original passage remains the stable anchor throughout the episode.
- The RFC states that conversation history is bounded and temporary for context construction, while textual interactions may be persisted.
- All conflicting one-turn-only language is removed or qualified.
- The definition of done includes at least one follow-up question.

### Verification

- Review all RFC references to questions, context, conversation, answers, and continue behavior.
- Compare the revised core loop with the Founding Thesis.

## M0-T02 — Define the V0 document-context contract

**Status:** Done
**Depends on:** M0-T01

### Outcome

The RFC states exactly what source and dialogue context the model receives, what each layer is for, and which claims the model may safely make.

### Scope

- Define document orientation, current-section context, local passage context, recent dialogue, and the current question.
- Decide whether V0 stores a generated document synopsis, a document map, or both.
- Define bounded dialogue-history behavior.
- Define the limitation for precise book-wide questions.
- Define source-authority and prior-knowledge guardrails.

### Out of scope

- Embeddings, vector databases, or semantic retrieval.
- Cross-document context.
- Personalized learner context.
- Prompt tuning beyond the context contract.

### Acceptance criteria

- Every context layer has a stated purpose and bound.
- The contract supports local questions and conversational follow-ups.
- The model is prohibited from claiming that unsupported material appears elsewhere in the uploaded document.
- Book-wide limitations are expressed clearly to the user.
- The contract can be implemented as deterministic application logic.

### Verification

- Walk the five benchmark question types through the context contract.
- Confirm that no retrieval infrastructure is implicitly required.

## M0-T03 — Align the architecture with the revised RFC

**Status:** Done
**Depends on:** M0-T01, M0-T02

### Outcome

`ARCHITECTURE.md` implements the same conversational V0 described by the RFC.

### Scope

- Add the conversational-episode lifecycle to the end-to-end flow.
- Update persisted domain objects as needed to associate interactions with an episode.
- Update context-builder responsibilities and invariants.
- Resolve the current RFC/architecture disagreement about whole-document orientation.
- Update routes only if the revised behavior requires a contract change.
- Keep answer interruption and real-time transport out of scope.

### Out of scope

- Writing application code or migrations.
- Designing V1 retrieval.
- Production infrastructure.

### Acceptance criteria

- No architecture invariant excludes required recent conversation history.
- The data model can order interactions within a conversational episode.
- Continue behavior clearly ends or deactivates the current episode.
- The architecture and RFC describe the same document-context layers.
- Existing simplicity constraints remain unless the revised RFC requires a change.

### Verification

- Perform a terminology and behavior comparison across the thesis, RFC, and architecture.
- Trace upload, listen, ask, follow-up, answer, and continue through the architecture.

## M0-T04 — Select the initial development document and benchmark set

**Status:** Done
**Depends on:** M0-T02

### Outcome

Development and early evaluation use one representative, legally usable, text-based PDF and a written benchmark question set.

### Scope

- Select a difficult nonfiction PDF with extractable text and identifiable structure.
- Record why it is representative of the initial wedge.
- Identify at least three passages of varying difficulty.
- Write benchmark questions covering explanation, author intent, example, follow-up connection, and counterargument.
- Record expected source evidence or evaluation notes without prescribing exact model wording.

### Out of scope

- Building a large evaluation dataset.
- Supporting image-only, encrypted, or malformed PDFs.
- Automated model grading.

### Acceptance criteria

- The selected PDF has a documented provenance and may be used for development.
- Its text can be extracted without OCR.
- At least five primary questions and two follow-up sequences are documented.
- At least one benchmark requires chapter context beyond the anchored paragraph.
- Evaluation notes distinguish grounding, usefulness, depth, and conversational continuity.

### Verification

- Manually inspect extracted text from the selected passages.
- Review the benchmark against the V0 success criteria in `ROADMAP.md`.

## M0-T05 — Approve the V0 baseline

**Status:** Done
**Depends on:** M0-T03, M0-T04

### Outcome

The product and engineering baseline is internally consistent and ready for implementation.

### Scope

- Review the Founding Thesis, RFC, architecture, roadmap, and backlog together.
- Resolve remaining contradictory requirements.
- Confirm the M1 scope and explicit V0 exclusions.
- Record any new decisions as ticket updates or architecture text.

### Out of scope

- Application implementation.
- Expanding the product beyond V0.

### Acceptance criteria

- The core loop is expressed consistently across all planning documents.
- M1 tickets do not depend on an unresolved product decision.
- The V0 exclusions are explicit.
- M0 exit criteria in `ROADMAP.md` are met.
- M1-T01 is moved to `Ready`.

### Verification

- Complete a final cross-document review.
- Trace one benchmark follow-up sequence from product requirement to architectural support.

### Completion review

- The Founding Thesis now explicitly distinguishes its long-term EPUB, article, learner-model,
  and natural-interruption aspirations from V0's text-based-PDF, explicit-control loop.
- The RFC now matches the architecture's V0 decisions: SQLite and one backend-only OpenRouter
  gateway rather than interchangeable providers or PostgreSQL.
- The core loop is consistently `Listen → Pause → Ask → Answer → Follow-up → Answer → Continue`:
  a paragraph anchors the episode; the context builder supplies bounded same-episode dialogue;
  Continue ends the episode and resumes at that anchor.
- The explicit exclusions remain no retrieval, embeddings/vector storage, learner memory,
  agents, real-time speech-to-speech, answer interruption, OCR, authentication, or
  production-scale infrastructure.
- Benchmark sequence S2 in `BENCHMARK.md` traces from the RFC episode contract to the
  architecture's `ConversationEpisode`, ordered `Interaction` turns, bounded recent dialogue,
  and Continue route.

The same-episode-only dialogue boundary recorded above was the approved baseline at the time of
M0-T05 and is superseded by M0-T06.

## M0-T06 — Carry conversation across a reading session

**Status:** Done
**Depends on:** M0-T05

### Outcome

V0 preserves conversational continuity across multiple pause-and-discuss episodes within the
same reading session.

### Scope

- Define a reading session that spans narration and multiple conversational episodes.
- Include every complete prior interaction from the active reading session in each reasoning
  request, including interactions from ended episodes.
- Keep a distinct immutable paragraph anchor for each conversational episode.
- Define explicit context-limit behavior without silently dropping or summarizing session turns.
- Align the RFC, architecture, roadmap, benchmark, backlog, and engineering instructions.

### Out of scope

- Carrying dialogue from an ended reading session into a new session.
- Summarizing or retrieving older conversations.
- Cross-document context or a persistent learner model.
- Application implementation.

### Acceptance criteria

- Continue ends only the active conversational episode; it does not erase or exclude earlier
  dialogue from the current reading session.
- A later Ask in the same reading session receives all complete earlier session interactions in
  chronological order plus the current episode's turns.
- V0 never silently truncates or summarizes session dialogue; it rejects a question that would
  exceed the configured session-context limit and asks the user to begin a new session.
- The persisted model distinguishes reading sessions, conversational episodes, and interactions.
- The benchmark contains a cross-episode continuity sequence.
- Long-term and cross-session memory remain explicitly deferred.

### Verification

- Search all planning documents for conflicting same-episode-only language.
- Trace a session through Ask, follow-up, Continue, more reading, a new Ask, and a reference to an
  earlier answer.

### Completion review

- The RFC now defines a `ReadingSession` that survives Continue and contains multiple independently
  anchored conversational episodes.
- The architecture persists `ReadingSession → ConversationEpisode → Interaction`, supplies every
  complete earlier session turn in deterministic order, and exposes explicit session lifecycle
  operations.
- Session dialogue is conversational memory but not source evidence; new claims about the document
  still require source text supplied for the current request.
- V0 fails clearly rather than dropping or summarizing session turns when the complete prompt would
  exceed its configured model-input limit.
- Benchmark sequence S3 covers Ask, Continue, more reading, a new anchor, and a reference to an
  earlier answer from an ended episode in the same session.
- The roadmap keeps cross-session recall, automatic compaction, and learner memory in the post-V0/V2
  idea stash.

## M0-T07 — Add bounded full-document question scope

**Status:** Done
**Depends on:** M0-T06

### Outcome

V0 answers document-wide questions from the complete normalized document when the document and
required active-session context fit safely within the configured reasoning-model input budget.
Oversized documents use an explicitly limited context mode rather than a categorical V0 denial or
an unsupported claim of whole-document analysis.

### Scope

- Add a full-document context scope for explicit document-wide questions when the complete prompt
  fits.
- Define eligibility from the configured model-context limit, reserved answer tokens, system and
  prompt instructions, the complete active reading-session dialogue, the current question, and a
  safety margin.
- Use normalized token or conservative extracted-character size for enforcement rather than PDF
  page count; page and word counts may be informational only.
- Assemble every section and paragraph exactly once in canonical source order, retaining section,
  paragraph, and page markers where available.
- Preserve the requirement that every complete earlier interaction from the active reading session
  remains in context.
- Retain a clearly labeled limited document-wide scope when the full document does not fit.
- Align the RFC, architecture, roadmap, benchmark, backlog dependencies, and engineering
  instructions.
- Add benchmark coverage for a fitting document-wide question and an over-limit document.

### Out of scope

- Embeddings, vector databases, semantic retrieval, or full-document RAG.
- Silently truncating, sampling, or summarizing source text to make a document fit.
- Silently dropping or summarizing active-session dialogue.
- Precise document-wide claims when the complete document was not supplied.
- Choosing a permanent page-count threshold before capability and latency measurements.
- Application implementation.

### Acceptance criteria

- An explicit document-wide question selects full-document scope when the complete required prompt
  fits the configured input budget.
- Full-document scope supplies the normalized source exactly once, without gaps, overlap,
  reordering, or silent truncation.
- Complete active-session dialogue remains included when determining whether full-document scope
  fits.
- The budget calculation reserves configured answer capacity and a safety margin and is
  deterministic and testable without a model call.
- When the full prompt does not fit, the product states what context it did and did not examine and
  does not imply that it searched or analyzed the complete document.
- Questions such as “Where else does this appear?” may identify locations only when the supplied
  full-document source supports them.
- The benchmark includes one answer requiring evidence from multiple sections of a fitting
  document and one over-limit case that verifies honest fallback behavior.
- Retrieval infrastructure remains explicitly deferred.

### Verification

- Trace an under-budget document-wide question through scope selection, canonical prompt assembly,
  answer generation, and source-authority rules.
- Trace an over-budget document-wide question and confirm that neither source text nor session
  dialogue is silently omitted.
- Search the planning documents for categorical V0 denials that conflict with the new conditional
  capability.
- Confirm that the revised contract introduces no embeddings, vector storage, or hidden retrieval.

### Completion review

- The RFC now selects full-document scope for an explicit document-wide question only when the
  exact canonical-source candidate, instructions, complete reading-session dialogue, and current
  question fit a deterministic budget after reserved answer capacity and safety margin.
- The canonical package serializes every normalized section and paragraph exactly once in source
  order with available section, paragraph, and page markers. It replaces rather than duplicates
  local or section source context.
- An over-budget request selects clearly labeled limited document-wide context. It states the
  supplied layers and that it did not examine the complete document; it neither searches nor
  claims verified document-wide locations. An over-limit limited package still fails explicitly
  rather than omitting session dialogue.
- Architecture invariants and tests now require model-call-free budget calculation, lossless
  canonical serialization, preserved complete session dialogue, and source-authority guardrails.
- Benchmark B6 exercises a fitting multi-section question; B7 verifies honest fallback under an
  over-limit capability profile. Full-document retrieval/RAG, embeddings, vector storage, and
  hidden retrieval remain deferred.

## M0-T08 — Add section-based reading start and navigation

**Status:** Done
**Depends on:** M0-T07

### Outcome

V0 lets the user begin or resume a reading session from a meaningful place in the document rather
than forcing every session to start at the first paragraph.

### Scope

- Add three start choices: resume the saved position, start at the document beginning, or choose an
  ordered chapter/section.
- Use detected sections and deterministic fallback sections through the same navigation contract.
- Define each selectable section by stable identity, title, order, and first paragraph ID.
- Define session-start behavior when the user selects a section or the beginning.
- Define navigation during an active reading session: pause narration, update the saved reading
  position, retain active-session dialogue, and anchor the next conversational episode at the new
  location.
- Preserve an active conversational episode's immutable paragraph anchor by requiring that episode
  to end before document navigation changes the reading position.
- Validate that every selected section and paragraph belongs to the current document.
- Align the RFC, architecture, roadmap, later milestone expectations, backlog dependencies, and
  engineering instructions.
- Record deferred advanced navigation ideas in `FUTURE_IDEAS.md`.

### Out of scope

- Semantic navigation such as “take me to the discussion of monetary policy.”
- Full-text search, arbitrary phrase lookup, or arbitrary sentence-level positioning.
- Bookmarks, highlights, annotations, or saved named locations.
- Page thumbnails or a sophisticated nested table of contents.
- Voice-controlled navigation.
- Automatically choosing the best place for the user to begin.
- Application implementation.

### Acceptance criteria

- Before narration begins, the user can select resume, document beginning, or any ordered section.
- Selecting a section resolves deterministically to that section's first paragraph and persists it
  as the document's current reading position.
- Documents without reliable chapter headings remain navigable through their fallback sections.
- Navigating within an active reading session preserves every earlier interaction from that session.
- Navigation cannot mutate the immutable anchor of an active conversational episode.
- Invalid or cross-document section and paragraph selections fail clearly.
- The reader and session API contracts contain enough information to implement the behavior without
  introducing semantic search or a new retrieval system.
- Advanced navigation concepts remain explicitly deferred.

### Verification

- Trace start-from-beginning, resume, and start-from-section through the RFC and architecture.
- Trace a mid-session section change followed by a new Ask and confirm that session dialogue is
  preserved while the new episode receives the new paragraph anchor.
- Trace a document with fallback sections and confirm every section is selectable.
- Search the planning documents for language that still implies narration must begin at the first
  document paragraph.

### Completion review

- The RFC now offers Resume, Start at beginning, and an ordered section picker before narration;
  each detected or fallback section has an ID, title, order, and deterministic first paragraph ID.
- The architecture validates document ownership for all position choices, persists the resolved
  paragraph, and exposes the required document, reader, session, and position-route contracts.
- Mid-session navigation pauses playback and preserves the reading session's complete dialogue.
  It is rejected until an active episode ends, so navigation cannot mutate that episode's immutable
  anchor; the next Ask creates a newly anchored episode at the selected location.
- `FUTURE_IDEAS.md` records the V0 flat-section limit and retains semantic search, full-text search,
  voice navigation, rich navigation, bookmarks, and sentence-level positioning as deferred work.
- The RFC/architecture traces cover beginning, resume, detected section, fallback section, and the
  active-session navigation sequence. A planning-document search found no remaining requirement
  that narration always begin at the first document paragraph.

---

# M1 — Application foundation and capability validation

## M1 sequencing

M1 begins after M0-T08. Capability spikes should resolve external uncertainty before the related
integrations are used by the application. Scaffolding tickets may then establish the web/API
boundary and persistence foundation. Fake capability operations provide deterministic development
and testing seams; real provider integration belongs to later milestones unless a spike explicitly
requires a live call.

Recommended execution order with a work-in-progress limit of one:

1. Complete M1-T01 so every later ticket uses the same repository and command conventions.
2. Run the four risk spikes M1-T02 through M1-T05 and record measured constraints; their code may
   remain disposable.
3. Scaffold the API and web applications through M1-T06 and M1-T07.
4. Establish the cross-application, persistence, and fake-capability foundations through M1-T08,
   M1-T09, and M1-T11.
5. Add the approved persisted domain schema in M1-T10.
6. Run M1-T12 as the milestone integration gate and decompose M2 from the evidence collected.

M1 validates external capabilities but does not add real provider calls to the product or implement
upload, reader, navigation UI, narration, or Ask behavior.

## M1-T01 — Define the repository layout and local developer workflow

**Status:** Done
**Depends on:** M0-T08

### Outcome

The repository has an agreed structure and one documented procedure for setting up, starting, and verifying the future applications.

### Scope

- Define the locations of the Next.js app, FastAPI app, tests, local data, and developer documentation.
- Choose package-management and runtime-version conventions.
- Define environment-file handling without committing secrets.
- Document expected local processes and ports.
- Update `AGENTS.md` with concrete commands once they exist.

### Out of scope

- Building product features.
- Containerized production deployment.
- CI/CD.

### Acceptance criteria

- The directory layout is documented and does not conflict with the architecture.
- Required runtime versions and package managers are explicit.
- Secret and local-data paths are excluded from version control when version control is initialized.
- A new contributor can identify how the web and API applications will be run and tested.

### Verification

- Review the proposed layout against all M1 tickets.
- Confirm commands and paths are consistent across project documentation.

## M1-T02 — Spike extraction against the selected PDF

**Status:** Done
**Depends on:** M0-T04, M1-T01

### Outcome

The chosen PDF libraries can extract usable metadata, outline information, layout lines, and ordered text from the selected development document.

### Scope

- Exercise `pypdf` metadata and outline extraction.
- Exercise `pdfplumber` layout-aware text extraction.
- Inspect page ordering, headings, paragraph reconstruction signals, and hyphenation.
- Record the normalized extracted character count and enough structure to evaluate the configured
  full-document budget profiles used by B6 and B7.
- Confirm that detected or fallback sections can partition the normalized paragraphs exactly once
  and that each section has a deterministic first paragraph for later navigation.
- Confirm that section, paragraph, and available page markers can be retained for canonical source
  serialization without creating a second text order.
- Record observed failure modes and representative extracted samples.
- Keep spike code disposable unless it already meets production-quality boundaries.

### Out of scope

- A complete upload pipeline.
- Generalized support for arbitrary PDFs.
- Database persistence.
- OCR.

### Acceptance criteria

- The selected PDF produces ordered, readable text without OCR.
- Outline or heading signals are characterized.
- All benchmark passages P1–P5 can be located in extracted output with their available page and
  structural markers.
- The normalized corpus size used by document-wide budget tests is recorded reproducibly.
- Extracted paragraphs can be assigned to ordered detected or fallback sections without gaps,
  overlap, duplication, or reordering.
- Every resulting section resolves to one deterministic first paragraph suitable for the flat
  section-navigation contract.
- Known extraction limitations are documented as constraints or follow-up tickets.

### Verification

- Compare extracted benchmark passages with the source PDF manually.
- Confirm that extraction neither silently omits nor materially reorders those passages.
- Check the ordered section/paragraph walk and first-paragraph resolution against the selected PDF.

## M1-T03 — Spike browser recording and transcription compatibility

**Status:** Done
**Depends on:** M0-T05, M1-T01

### Outcome

A short browser-compatible recording can be accepted by the selected transcription endpoint with usable accuracy and measured latency.

### Scope

- Produce or capture a representative `audio/webm` recording.
- Verify the selected STT endpoint and model accept the format.
- Record transcript quality, request behavior, latency, and relevant limits.
- Identify any required conversion or browser constraints.

### Out of scope

- The final recording UI.
- Long recordings, streaming transcription, or voice activity detection.
- Persisting question audio.

### Acceptance criteria

- A representative recording is transcribed successfully.
- The result is accurate enough for representative local, current-section, document-wide,
  same-episode follow-up, and later-episode session-continuity questions from `BENCHMARK.md`.
- Required MIME type, duration limit, configuration, and error behavior are documented.
- Any required format conversion becomes an explicit ticket rather than hidden scope.

### Verification

- Compare the returned transcript with the spoken question.
- Record the observed end-to-end request latency, accepted MIME type, maximum V0 recording duration,
  and any browser or conversion constraint that must become configuration or backlog work.

## M1-T04 — Spike narration and answer TTS quality

**Status:** Done
**Depends on:** M0-T05, M1-T01

### Outcome

The selected TTS endpoint can produce acceptable MP3 narration for both source passages and explanatory answers.

### Scope

- Synthesize one source passage and one detailed explanatory answer.
- Include at least one answer long enough to expose pacing or long-form stability problems relevant
  to a substantive spoken explanation.
- Compare a small set of supported voices if necessary.
- Check pronunciation, pacing, long-form stability, output format, latency, and retry behavior.
- Select an initial voice and record the configuration rationale.

### Out of scope

- Full-book audio generation.
- Voice cloning or advanced prosody controls.
- Application audio caching.

### Acceptance criteria

- The endpoint returns browser-playable MP3 audio.
- One initial voice is selected for V0.
- Passage and answer audio are intelligible and acceptable for continued listening.
- Relevant limits, latency, configuration, and cache-version inputs are documented, including the
  selected voice and every model/voice setting that must invalidate cached audio.

### Verification

- Perform and record a short listening comparison.
- Play generated files in a target browser.

## M1-T05 — Spike reasoning quality with the context contract

**Status:** Done
**Depends on:** M0-T02, M0-T04, M0-T06, M0-T07, M0-T08, M1-T01

### Outcome

The selected reasoning model can answer benchmark questions usefully and remain grounded when given the V0 context contract.

### Scope

- Construct representative local, section, fitting full-document, limited document-wide, and dialogue context packages.
- Run benchmark cases B1–B7 and sequences S1–S3 using the RFC-selected scopes and source-authority
  rules.
- Exercise both deterministic token-estimator and conservative normalized-character budgeting when
  both are viable; otherwise record why one mode is selected for V0.
- Measure the exact fitting and over-budget candidate prompts, including instructions, labels,
  markers, complete active-session dialogue, question, answer reserve, and safety margin.
- Observe answer quality, grounding, depth, latency, input/output size, and estimated cost behavior.
- Recommend initial values or derivation rules for model context limit, reserved answer tokens,
  safety margin, conservative characters per token when applicable, maximum transcribed question,
  and active-session prompt failure behavior.
- Record the prompt shape, guardrails, configuration, and risks required for implementation.

### Out of scope

- Automated evaluation infrastructure.
- Full-document retrieval.
- Production prompt-version persistence.
- Implementing the context builder or real reasoning integration in the application.

### Acceptance criteria

- Local explanations correctly use the anchored passage and section context.
- Current-section answers use the complete bounded section without relying on an unused synopsis or
  duplicate local source context.
- Follow-up and later-episode answers make coherent use of every earlier turn from the active reading session.
- The model distinguishes supplied text from general background knowledge.
- B6 document-wide claims are grounded in the canonical full-document source and its markers.
- B7 clearly identifies its supplied limited layers and does not imply retrieval, search, or
  complete-document analysis.
- Fitting and over-budget decisions are reproducible without a model call and never remove source or
  active-session turns to force a fit.
- Initial context-budget and answer-reserve configuration recommendations are documented with the
  measurements that justify them.
- Material quality, cost, latency, or context-limit risks are documented before M3 implementation.

### Verification

- Manually evaluate B1–B7 and S1–S3 using `BENCHMARK.md`.
- Record representative successes, failures, prompt measurements, observed latency, and estimated
  cost.
- Recalculate at least one fitting and one over-budget decision independently from the recorded
  inputs.

### Completion review

- `docs/spikes/m1-t05_reasoning.py` reproducibly assembles local, complete current-section,
  canonical full-document, limited document-wide, and complete session-dialogue packages from the
  checksum-pinned Constitution extraction.
- Live B1–B7 and S1–S3 evaluation with `openai/gpt-5.6-sol` passed the benchmark grounding,
  usefulness, depth, and continuity expectations. An initial B7 disclosure omitted an explicit
  empty-dialogue statement; the refined guardrail and rerun name all four limited layers and the
  complete-document limitation.
- B6's final exact candidate is 55,680 characters and 12,845 `o200k_base` tokens. It fits the
  128,000-token capability profile after a 4,096-token answer reserve and 2,048-token safety margin.
  The same estimators reproducibly reject B7's 55,533-character full candidate under the 16,000-token
  over-limit profile and accept its complete 5,190-character limited package without trimming.
- The spike report records the prompt contract, initial configuration, independent fit arithmetic,
  manual evaluations, actual token/cost/latency measurements, the representative B7 refinement, and
  M3 risks. Generated prompts and answers remain ignored under `var/`.

## M1-T06 — Scaffold the FastAPI application

**Status:** Done
**Depends on:** M1-T01

### Outcome

A minimal FastAPI application starts locally, loads validated configuration, and exposes a tested health endpoint.

### Scope

- Create the API package and application entry point.
- Add environment-based configuration with clear validation errors.
- Establish typed configuration locations for local paths, database behavior, model identifiers,
  recording limits, context-budget inputs, and audio-cache versioning without making live provider
  calls.
- Add `GET /api/health`.
- Establish the initial error-response shape.
- Add a focused automated test.

### Out of scope

- Document routes.
- Database models.
- OpenRouter calls.
- Background processing.

### Acceptance criteria

- The documented command starts the API.
- `GET /api/health` returns HTTP 200 and a stable response.
- Missing required configuration fails clearly when the relevant feature is invoked or at startup, according to the chosen policy.
- Backend-only provider and context configuration cannot be exposed through a public API response.
- The health-endpoint test passes.

### Verification

- Run the API test suite.
- Start the API and request the health endpoint manually.

## M1-T07 — Scaffold the Next.js application

**Status:** Done
**Depends on:** M1-T01

### Outcome

A minimal Next.js application starts locally and renders a stable V0 shell suitable for subsequent vertical slices.

### Scope

- Create the web application with TypeScript.
- Add a minimal page shell and loading/error boundary conventions.
- Establish frontend test and lint commands.
- Avoid implementing reader features.

### Out of scope

- PDF upload.
- Audio playback or recording.
- Final visual design.
- State-management frameworks without a present need.

### Acceptance criteria

- The documented command starts the web application.
- The root page renders without console errors.
- The initial automated frontend test passes.
- Linting and type checking can be run locally.

### Verification

- Run frontend tests, linting, and type checking.
- Load the root page in a browser.

## M1-T08 — Establish same-origin web-to-API communication

**Status:** Done
**Depends on:** M1-T06, M1-T07

### Outcome

The browser can reach FastAPI under `/api` without receiving backend secrets or requiring development CORS configuration.

### Scope

- Configure the Next.js development rewrite or equivalent same-origin routing.
- Add a minimal frontend health check against `/api/health`.
- Document local process and port expectations.
- Handle an unavailable API with a clear development-visible error.

### Out of scope

- Production hosting.
- Authentication.
- Product API routes.

### Acceptance criteria

- A browser request to `/api/health` reaches FastAPI.
- No OpenRouter credential or backend-only configuration is exposed to the browser.
- The frontend communicates successfully without a permissive CORS workaround.
- The unavailable-backend state is observable and understandable.

### Verification

- Start both applications and exercise the health request in a browser.
- Inspect the browser bundle/environment for backend secrets.

## M1-T09 — Configure SQLite, SQLAlchemy, and Alembic

**Status:** Done
**Depends on:** M1-T06

### Outcome

The API has a tested local persistence foundation with repeatable schema migrations.

### Scope

- Add SQLAlchemy engine and session configuration.
- Configure SQLite foreign keys and WAL mode where appropriate.
- Configure Alembic.
- Define database-path handling for development and tests.
- Add a minimal connectivity or migration test.

### Out of scope

- Product domain tables.
- Repository classes or a separate domain hierarchy.
- Multi-process write support.

### Acceptance criteria

- A new local database can be created through migrations.
- Tests use an isolated temporary database.
- Foreign-key enforcement is active.
- The single-writer constraint is documented.
- Slow external calls are not coupled to database transactions.

### Verification

- Apply migrations to a fresh temporary database.
- Run the database configuration tests.

## M1-T10 — Add the initial persisted domain schema

**Status:** Ready
**Depends on:** M0-T03, M0-T06, M0-T07, M0-T08, M1-T09

### Outcome

The database represents the minimum V0 document, reading-session, conversational-episode, and interaction state agreed in the architecture.

### Scope

- Add `Document`, `Section`, `Paragraph`, `ReadingSession`, `ConversationEpisode`, and `Interaction`
  tables with the fields approved in `ARCHITECTURE.md`.
- Add ordering, ownership, status, timestamps, and reading-position fields required by V0.
- Add foreign keys and uniqueness constraints that enforce stable ordering and ownership.
- Create the migration and focused persistence tests.

### Out of scope

- User accounts.
- Embeddings or vector data.
- Generated-audio database rows.
- Long-term learner memory.

### Acceptance criteria

- The schema supports ordered sections and paragraphs without duplicated ownership fields.
- Document status, bounded document map, source path, processing failure information, and current
  paragraph state are represented.
- Section boundary source, cached-synopsis metadata, order, and available page range are represented;
  its navigation first paragraph remains derived from ordered member paragraphs rather than stored
  as a competing source of truth.
- Reading sessions and their conversational episodes have deterministic order.
- An interaction can be ordered within an episode, included in chronological session context, and anchored through its episode to a paragraph.
- At most one reading session per document and one episode per session can be active.
- A document can store one current reading position.
- Database constraints are used where SQLite can express the invariant; cross-table ownership rules
  that require application validation are documented and covered by focused query/service tests at
  the appropriate later ticket.
- Processing states and retry-related failure fields match the architecture.
- The migration applies cleanly to a fresh database and tests cover key constraints.

### Verification

- Apply and roll back the migration against a temporary database when supported.
- Run persistence tests for relationships, ordering, and invalid foreign keys.

## M1-T11 — Add deterministic fake capability operations

**Status:** Backlog  
**Depends on:** M1-T06

### Outcome

Application services and future end-to-end tests can exercise reasoning, transcription, and speech behavior without network calls or model variability.

### Scope

- Define the three application-owned operations required by the architecture: generate text, transcribe recording, and synthesize speech.
- Add deterministic fake implementations with configurable success and failure responses.
- Make the text fake able to return scope-specific answers and the speech fake return stable
  browser-playable fixture bytes or an equally deterministic application-owned audio value.
- Keep the seam small and avoid a generic provider registry.
- Add focused tests for fake behavior and error mapping.

### Out of scope

- Real OpenRouter HTTP integration.
- Runtime provider routing.
- Provider SDK abstractions.

### Acceptance criteria

- Each fake operation returns deterministic application-owned values.
- Tests can simulate transient and permanent failures.
- Tests can distinguish local, section, fitting full-document, limited document-wide, transcription,
  and synthesis paths without inspecting or changing provider-specific code.
- No network access is required.
- The interface remains limited to current V0 operations.

### Verification

- Run the capability-operation unit tests.
- Review the seam against the OpenRouter boundary in `ARCHITECTURE.md`.

## M1-T12 — Establish the integrated verification baseline

**Status:** Backlog  
**Depends on:** M1-T02, M1-T03, M1-T04, M1-T05, M1-T08, M1-T09, M1-T10, M1-T11

### Outcome

The application foundation has a documented, repeatable verification procedure and satisfies the M1 milestone exit criteria.

### Scope

- Document setup, migration, start, test, lint, and type-check procedures.
- Provide one convenient verification command or a short ordered command sequence.
- Verify the web/API boundary, database migration, domain schema, and fake capabilities together.
- Review all four capability-spike reports and consolidate their accepted V0 configuration values,
  constraints, and unresolved risks into authoritative developer documentation and example
  environment configuration without committing secrets.
- Update `AGENTS.md` with the final commands and conventions.
- Reconcile M1 completion against every exit criterion in `ROADMAP.md`.
- Decompose M2 into implementation-ready tickets using the completed M1 evidence, and move only the
  first dependency-satisfied M2 ticket to `Ready`.

### Out of scope

- PDF upload or reader features.
- Real model integrations beyond completed spikes.
- Deployment automation.
- Implementing any M2 upload, reader, navigation, or narration behavior.

### Acceptance criteria

- A clean local environment can follow the documented setup.
- Backend tests, frontend tests, linting, and type checking pass.
- A fresh database can be migrated.
- The browser reaches the API health endpoint.
- PDF extraction, STT, TTS, and reasoning spike reports contain the measurements and decisions
  required by their tickets.
- Authoritative configuration documents the initial recording, context-budget, answer-reserve,
  safety-margin, model/voice, and audio-cache inputs established by the spikes.
- M1 exit criteria in `ROADMAP.md` are satisfied.
- M2 has an ordered, dependency-aware backlog based on evidence rather than speculative
  implementation detail.

### Verification

- Execute the complete documented procedure from a clean local state.
- Audit M1-T01 through M1-T11 and the four spike artifacts against their acceptance criteria.
- Review M1 completion against `ROADMAP.md` and this backlog.

---

# Later milestones

M2 through M5 are intentionally not decomposed yet. Their outcomes and exit criteria live in `ROADMAP.md`. Create their implementation-ready tickets near the end of the preceding milestone, using evidence from completed work and keeping the same ticket template.
