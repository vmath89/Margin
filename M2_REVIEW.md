# M2 incremental human review log

## Purpose

This file records the reproducible human checkpoint for every M2 implementation ticket. Automated
verification remains required, but a ticket is not `Done` and its dependent ticket does not become
`Ready` until the reviewer accepts the increment here.

Do not record credentials, private uploaded source text, recordings, generated audio, full sensitive
prompts, or other local runtime data. Record the exact reviewed commit so the decision identifies
one reproducible repository state.

## Reviewer decisions

- `Pending` — the walkthrough has not been accepted.
- `Accepted` — the ticket's visible or inspectable increment satisfies its acceptance criteria.
- `Changes requested` — the active ticket remains open until the named defect is corrected.
- `Follow-up ticket required` — the increment is accepted, but necessary out-of-scope work must be
  added to `TASKS.md` and dependency-gated appropriately.

## Required record for each ticket

Copy this checklist into the ticket section when its review begins:

```text
Implementation status:
Reviewed commit:
Review date:
Reviewer:
Decision: Pending

Start procedure:
Happy-path walkthrough:
Failure or edge-case walkthrough:
Expected observations:
Actual observations:
Automated verification and results:
Known limitations:
Required corrections or follow-up tickets:
```

## M2-T01 — Selected-PDF processing pipeline

Implementation status: Done
Reviewed commit: Not recorded in this log
Review date: Not recorded in this log
Reviewer: Not recorded in this log
Decision: Accepted before this review log was introduced

The completion evidence remains in the ticket handoff and repository history. Do not recreate or
invent historical observations solely to populate this file.

## M2-T02 — Selected benchmark upload and persistence

Implementation status: Done
Reviewed commit: Not recorded in this log
Review date: Not recorded in this log
Reviewer: Not recorded in this log
Decision: Accepted before this review log was introduced

The completion evidence remains in the ticket handoff and repository history. Do not recreate or
invent historical observations solely to populate this file.

## M2-T02A — General text-PDF upload and prepared-source review

Implementation status: Done
Reviewed commit: 0a3355be748af0f04e6541b712362ce4b53cf9f2
Review date: 2026-08-27
Reviewer: Project owner, with Codex verification evidence
Decision: Accepted by one-time owner waiver

### Start procedure

From the repository root, install the locked backend and frontend dependencies, migrate a fresh
SQLite database, start FastAPI on port 8000, start Next.js on port 3000, and open the web origin at
`http://127.0.0.1:3000`. The exact canonical commands remain in `DEVELOPMENT.md`.

### Happy-path walkthrough

Upload the Constitution fixture and at least one different supported text-based PDF. Confirm visible
preparation states, open the prepared-source review, and compare representative map, section,
paragraph, and page-marker output with each source.

### Failure or edge-case walkthrough

Upload an image-only or malformed PDF, then select a different file and confirm the old status is
cleared before the new request.

### Expected observations

Accepted documents publish one complete canonical hierarchy; rejected documents expose no partial
authoritative data, secret, local path, or stale status.

### Actual observations

Codex uploaded the committed non-benchmark outline fixture through the real browser UI. It moved
through the visible preparation flow, became ready as `Opening`, and exposed a prepared-source
review whose document map was `Opening` then `Conclusion`; sections retained pages 1 and 2; and
five paragraphs appeared once in canonical order with their page markers. Codex then selected the
image-only fixture: selection immediately cleared the prior ready message and prepared-source
view, and preparation failed with the actionable no-extractable-text message without exposing a
path or technical detail. The committed Constitution fixture, no-outline fixture, encrypted
fixture, malformed input, pagination, stale asynchronous review response, retry, and source-order
cases were exercised by automated tests.

### Automated verification and results

- `apps/api/.venv/bin/pytest apps/api/tests` — 57 passed on 2026-08-27.
- `apps/api/.venv/bin/ruff check apps/api` — passed.
- `apps/api/.venv/bin/mypy apps/api/src` — passed with no issues in 9 source files.
- `apps/web/node_modules/.bin/vitest run` — 8 passed.
- `apps/web/node_modules/.bin/eslint .` — passed.
- `apps/web/node_modules/.bin/tsc --noEmit` — passed.
- A fresh SQLite database migrated through revisions `20260823_01` and `20260823_02`.
- Real-browser same-origin non-benchmark success, prepared-source inspection, state reset, and
  image-only failure checks passed on 2026-08-25.

### Known limitations

No narration or conversation. The broader supported-layout decision belongs to M2-T02B.

### Required corrections or follow-up tickets

No correction remains from the independent code review. The project owner explicitly waived the
remaining personal hands-on walkthrough on 2026-08-27 and accepted the ticket using the recorded
automated and Codex-operated browser evidence. This is a one-ticket waiver; it does not change the
human-review requirement for later M2 tickets. M2-T02B remains responsible for defining and
validating the broader supported-layout envelope.

## M2-T02B — Supported text-PDF compatibility gate

Implementation status: Ready
Reviewed commit:
Review date:
Reviewer:
Decision: Pending

Review the fixture-backed compatibility matrix, inspect every accepted distinct layout through the
prepared-source review, compare representative output with its source, and inspect at least one
clear unsupported-input failure. Record which complex layouts are accepted, rejected, or explicitly
unsupported and whether every accepted result is natural enough to narrate.

## M2-T03 — Linear narration

Implementation status: Backlog
Reviewed commit:
Review date:
Reviewer:
Decision: Pending

Start an accepted prepared document, play and pause midway, resume, observe several canonical
paragraph transitions, reach or simulate document end, and trigger one fake audio-generation
failure. Confirm the highlighted paragraph always matches the current audio unit and a failed audio
request never advances it.

## M2-T04 — Conversation engine and session-continuous context

Implementation status: Backlog
Reviewed commit:
Review date:
Reviewer:
Decision: Pending

Reproduce the deterministic B1 → S1 → Continue → later S3-style trace. Inspect the reading-session
ID, episode IDs and anchors, ordered interactions, separately labeled source and dialogue, selected
scope, Continue result, repeated request ID, one stable failure, context-limit rejection, and
ended-session exclusion. Use only a legal fixture and do not establish sensitive production logs.

## M2-T04A — Browser conversation and session-boundary review

Implementation status: Backlog
Reviewed commit:
Review date:
Reviewer:
Decision: Pending

Using deterministic fake capabilities, exercise Ask, follow-up, Continue, later-episode memory, End
Reading Session, Start New Session Here, context-limit recovery, double submission, and one failed
Ask. Confirm the four user actions have distinct visible meanings and the fresh session retains the
saved paragraph but none of the ended session's dialogue.

## M2-T05A — Production OpenRouter capabilities

Implementation status: Backlog
Reviewed commit:
Review date:
Reviewer:
Decision: Pending

Review mocked success and failure coverage, then explicitly opt in to each configured live
capability when credentials are available. Record latency, transcription accuracy, answer grounding,
voice quality, retry behavior, validation, and safe diagnostics without recording secret values or
sensitive payloads.

## M2-T05B — Production spoken conversational reader

Implementation status: Backlog
Reviewed commit:
Review date:
Reviewer:
Decision: Pending

With an actual microphone, perform B1, S1, Continue, and the later S3-style question. Inspect the
transcript, textual answer, answer audio, anchor restart, and earlier-session continuity. Also test
permission denial, a failed Ask, answer-audio retry, End Reading Session, and Start New Session Here.

## M2-T06 — M2 integrated acceptance

Implementation status: Backlog
Reviewed commit:
Review date:
Reviewer:
Decision: Pending

Review the complete verification commands, benchmark fake-provider flow, non-benchmark supported-PDF
flow, session reset and failure paths, roadmap checklist, and explicit opt-in live run. Record the
final decision as either acceptance of M2 for post-M2 M3 planning or named corrections that keep M2
open.
