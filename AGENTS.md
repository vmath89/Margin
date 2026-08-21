# Margin Engineering Instructions

## Project purpose

Margin is an AI reading companion for difficult nonfiction. The V0 product must let a user upload a supported PDF, listen to it, pause at a passage, ask grounded spoken questions and follow-ups, hear the answers, and continue from the correct reading position.

Read these product documents before making product or architectural changes:

1. `Founding Thesis.md` — long-term belief and product direction.
2. `MVP RFC — AI Reading Companion v0.md` — V0 product behavior and boundaries.
3. `ARCHITECTURE.md` — technical design and invariants.
4. `ROADMAP.md` — milestone outcomes and exit criteria.
5. `TASKS.md` — active backlog, ticket scope, and acceptance criteria.
6. `FUTURE_IDEAS.md` — deferred concepts that are not approved or authorized work.

If these documents disagree, do not silently choose one. Treat the thesis as product direction, the RFC as V0 product scope, and the architecture as its implementation design. Resolve material inconsistencies in the relevant planning documents before implementation.

## Current project phase

The repository currently contains planning documents only. Do not scaffold or implement the application until an implementation ticket is explicitly selected.

M0 aligns the product and architecture. M1 establishes the application foundation and validates risky external capabilities. Later milestones are deliberately not decomposed yet.

## Work selection and ticket discipline

- Use `TASKS.md` as the source of truth for planned work.
- Work on an explicitly selected ticket; do not infer permission to begin adjacent tickets.
- Before implementation, confirm that the ticket is `Ready` and all dependencies are `Done`.
- Change the selected ticket to `In Progress` when work begins.
- Keep one implementation ticket in progress unless independent parallel work is explicitly requested.
- Stay within the ticket's scope and out-of-scope boundaries.
- Add newly discovered work to the backlog instead of expanding the active ticket silently.
- Record a worthwhile out-of-scope product idea in `FUTURE_IDEAS.md`; do not implement it unless an
  explicit decision promotes it into `ROADMAP.md` and `TASKS.md`.
- Mark a ticket `Done` only after every acceptance criterion and verification step passes.
- Update ticket status in the same change that completes the ticket.
- Do not mark a milestone complete until its integrated exit criteria in `ROADMAP.md` are demonstrable.

## Product boundaries for V0

Preserve these principles unless an approved RFC change says otherwise:

- The central experience is `Listen → Pause → Ask → Discuss → Continue`.
- A paragraph is the stable reading-position and resume anchor, not the full semantic context boundary.
- Before narration, a reader may resume the saved paragraph, start at the document beginning, or
  select an ordered detected or fallback section. Navigation within an active session preserves
  its dialogue but requires any active conversational episode to end before the position changes.
- Model context is explicit, bounded, grounded, and constructed by application logic.
- Sequential follow-up questions belong to one paused-reading conversational episode.
- A reading session spans narration and multiple conversational episodes. Every complete earlier
  interaction from the active reading session is model context, including interactions from ended
  episodes.
- Never silently truncate or summarize active-session dialogue. If the complete required prompt
  exceeds the configured limit, fail clearly and require a new reading session.
- Uploaded source text is authoritative. General model knowledge must be identified as background and must not be presented as evidence from the uploaded document.
- Precise document-wide claims require supplied evidence. An explicit document-wide question may
  receive the complete normalized document only when its full required prompt fits the configured
  deterministic budget; retrieval remains deferred.
- V0 is a trusted, single-user prototype on one host.

Do not introduce these without a new approved requirement:

- Autonomous agents or multi-agent systems.
- Embeddings, vector databases, or hidden retrieval.
- Cross-session conversation recall, long-term learner memory, or cross-document knowledge graphs.
- Authentication, billing, multi-user isolation, or production-scale infrastructure.
- WebSockets, real-time speech-to-speech, wake words, or answer interruption.
- OCR or broad image-only PDF support.
- Generic repository layers, provider registries, or speculative framework abstractions.

## Architectural expectations

- The browser calls FastAPI through same-origin `/api` routes and never receives provider credentials.
- FastAPI owns document processing, context construction, model calls, reading position, and persistence.
- SQLite is the V0 database and has one backend writer.
- SQLAlchemy query functions should remain small and explicit; do not add generic repository classes.
- PDF parsing and splitting should be deterministic and testable without model calls.
- The context builder should be deterministic application logic over persisted data, the active
  reading session and episode, and the current question.
- External capability boundaries should expose only the operations V0 needs: text generation, transcription, and speech synthesis.
- Slow external calls must not run inside database transactions.
- Source text must never be silently truncated, omitted, duplicated, overlapped, or reordered.
  A fitting full-document context serializes every normalized section and paragraph exactly once
  in canonical source order; an over-budget document-wide request uses clearly labeled limited
  context without implying complete-document analysis.
- Generated audio is disposable and reproducible from authoritative stored text.
- New abstractions must solve a current ticket requirement or make an existing boundary directly testable.

## Repository and command conventions

`DEVELOPMENT.md` defines the repository layout, local environment handling, ports, and contributor
procedure. Use CPython 3.12 with `uv` for `apps/api` and Node.js 22 with Corepack-managed pnpm 10
for `apps/web`. Run commands from the repository root.

The canonical command contract is:

- backend setup: `uv sync --project apps/api --all-groups`;
- start API: `uv run --project apps/api uvicorn margin_api.main:app --reload --port 8000`;
- backend tests: `uv run --project apps/api pytest apps/api/tests`;
- backend lint: `uv run --project apps/api ruff check apps/api`;
- backend type checking: `uv run --project apps/api mypy apps/api/src`;
- frontend setup: `pnpm --dir apps/web install --frozen-lockfile`;
- start web: `pnpm --dir apps/web dev --port 3000`;
- frontend tests: `pnpm --dir apps/web test`;
- frontend lint: `pnpm --dir apps/web lint`;
- frontend type checking: `pnpm --dir apps/web typecheck`;
- apply migrations: `uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head`;
- end-to-end verification: `pnpm --dir apps/web exec playwright test ../../tests/e2e`.

Commands become executable when their owning M1 ticket creates the relevant application files;
until then, do not scaffold them outside the selected ticket. If an implementing ticket must
change a command, update both this index and `DEVELOPMENT.md` in the same change.

Local development uses Next.js at `http://127.0.0.1:3000` and one FastAPI worker at
`http://127.0.0.1:8000`. The browser uses the web origin and same-origin `/api` routing. Store all
repository-local runtime state under ignored `var/`. Keep backend secrets in ignored
`apps/api/.env`, never in frontend variables or browser-visible responses.

Never commit API keys, recordings, uploaded documents containing private material, local databases, or generated audio caches.

## Testing and verification

- Test deterministic parsing, context, state-transition, and path logic as pure functions where practical.
- Use temporary isolated databases for persistence tests.
- Use fake external capability operations for normal automated tests.
- Keep live provider smoke tests explicit and opt-in.
- Add browser-level tests only for valuable cross-boundary behavior; the V0 core loop requires one end-to-end test by M5.
- When fixing a defect, add a focused regression test when the behavior is testable.
- Report exactly which checks were run and any checks that could not be run.

## Change hygiene

- Preserve unrelated user changes.
- Keep changes focused on the selected ticket.
- Do not perform destructive Git or filesystem operations without explicit authorization.
- Prefer small, reviewable changes over large rewrites.
- Update the RFC or architecture when behavior or an invariant changes; do not let code become the only record of a product decision.
- Use architecture decision records only for consequential decisions not already captured adequately in the RFC or architecture.

## Completion handoff

When finishing a ticket, report:

1. The outcome delivered.
2. The important files changed.
3. The acceptance criteria satisfied.
4. The verification commands and results.
5. Any known limitations or newly created follow-up tickets.
6. The next ticket that is eligible to move to `Ready`.
