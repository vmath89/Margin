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

**Status:** Ready
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

**Status:** Backlog  
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

---

# M1 — Application foundation and capability validation

## M1 sequencing

M1 begins after M0-T05. Capability spikes should resolve external uncertainty before the related integrations are used by the application. Scaffolding tickets may then establish the web/API boundary and persistence foundation. Fake capability operations provide deterministic development and testing seams; real provider integration belongs to later milestones unless a spike explicitly requires a live call.

## M1-T01 — Define the repository layout and local developer workflow

**Status:** Backlog  
**Depends on:** M0-T05

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

**Status:** Backlog  
**Depends on:** M0-T04, M1-T01

### Outcome

The chosen PDF libraries can extract usable metadata, outline information, layout lines, and ordered text from the selected development document.

### Scope

- Exercise `pypdf` metadata and outline extraction.
- Exercise `pdfplumber` layout-aware text extraction.
- Inspect page ordering, headings, paragraph reconstruction signals, and hyphenation.
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
- At least three benchmark passages can be located in extracted output.
- Known extraction limitations are documented as constraints or follow-up tickets.

### Verification

- Compare extracted benchmark passages with the source PDF manually.
- Confirm that extraction neither silently omits nor materially reorders those passages.

## M1-T03 — Spike browser recording and transcription compatibility

**Status:** Backlog  
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
- The result is accurate enough for all five benchmark question styles.
- Required MIME type, duration limit, configuration, and error behavior are documented.
- Any required format conversion becomes an explicit ticket rather than hidden scope.

### Verification

- Compare the returned transcript with the spoken question.
- Record the observed end-to-end request latency.

## M1-T04 — Spike narration and answer TTS quality

**Status:** Backlog  
**Depends on:** M0-T05, M1-T01

### Outcome

The selected TTS endpoint can produce acceptable MP3 narration for both source passages and explanatory answers.

### Scope

- Synthesize one source passage and one detailed explanatory answer.
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
- Relevant limits, latency, configuration, and cache-version inputs are documented.

### Verification

- Perform and record a short listening comparison.
- Play generated files in a target browser.

## M1-T05 — Spike reasoning quality with the context contract

**Status:** Backlog  
**Depends on:** M0-T02, M0-T04, M1-T01

### Outcome

The selected reasoning model can answer benchmark questions usefully and remain grounded when given the V0 context contract.

### Scope

- Construct representative local, section, document-orientation, and dialogue context packages.
- Run the primary benchmark questions and follow-up sequences.
- Observe answer quality, grounding, depth, latency, and prompt-size behavior.
- Record prompt adjustments required for implementation.

### Out of scope

- Automated evaluation infrastructure.
- Full-document retrieval.
- Production prompt-version persistence.

### Acceptance criteria

- Local explanations correctly use the anchored passage and section context.
- Follow-up answers make coherent use of recent dialogue.
- The model distinguishes supplied text from general background knowledge.
- Unsupported book-wide claims are refused or qualified.
- Material quality or latency risks are documented before M3 implementation.

### Verification

- Manually evaluate responses using the benchmark notes from M0-T04.
- Record representative successes, failures, and observed latency.

## M1-T06 — Scaffold the FastAPI application

**Status:** Backlog  
**Depends on:** M1-T01

### Outcome

A minimal FastAPI application starts locally, loads validated configuration, and exposes a tested health endpoint.

### Scope

- Create the API package and application entry point.
- Add environment-based configuration with clear validation errors.
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
- The health-endpoint test passes.

### Verification

- Run the API test suite.
- Start the API and request the health endpoint manually.

## M1-T07 — Scaffold the Next.js application

**Status:** Backlog  
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

**Status:** Backlog  
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

**Status:** Backlog  
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

**Status:** Backlog  
**Depends on:** M0-T03, M1-T09

### Outcome

The database represents the minimum V0 document, reading, interaction, and conversational-episode state agreed in the architecture.

### Scope

- Add `Document`, `Section`, `Paragraph`, `Conversation`, and `Interaction` tables or the final M0-approved equivalents.
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
- An interaction can be ordered within a conversational episode and anchored to a paragraph.
- A document can store one current reading position.
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
- Keep the seam small and avoid a generic provider registry.
- Add focused tests for fake behavior and error mapping.

### Out of scope

- Real OpenRouter HTTP integration.
- Runtime provider routing.
- Provider SDK abstractions.

### Acceptance criteria

- Each fake operation returns deterministic application-owned values.
- Tests can simulate transient and permanent failures.
- No network access is required.
- The interface remains limited to current V0 operations.

### Verification

- Run the capability-operation unit tests.
- Review the seam against the OpenRouter boundary in `ARCHITECTURE.md`.

## M1-T12 — Establish the integrated verification baseline

**Status:** Backlog  
**Depends on:** M1-T08, M1-T09, M1-T10, M1-T11

### Outcome

The application foundation has a documented, repeatable verification procedure and satisfies the M1 milestone exit criteria.

### Scope

- Document setup, migration, start, test, lint, and type-check procedures.
- Provide one convenient verification command or a short ordered command sequence.
- Verify the web/API boundary, database migration, domain schema, and fake capabilities together.
- Update `AGENTS.md` with the final commands and conventions.
- Record any deferred work as M2 tickets rather than implementing it.

### Out of scope

- PDF upload or reader features.
- Real model integrations beyond completed spikes.
- Deployment automation.

### Acceptance criteria

- A clean local environment can follow the documented setup.
- Backend tests, frontend tests, linting, and type checking pass.
- A fresh database can be migrated.
- The browser reaches the API health endpoint.
- M1 exit criteria in `ROADMAP.md` are satisfied.

### Verification

- Execute the complete documented procedure from a clean local state.
- Review M1 completion against `ROADMAP.md` and this backlog.

---

# Later milestones

M2 through M5 are intentionally not decomposed yet. Their outcomes and exit criteria live in `ROADMAP.md`. Create their implementation-ready tickets near the end of the preceding milestone, using evidence from completed work and keeping the same ticket template.
