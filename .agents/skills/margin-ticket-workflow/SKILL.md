---
name: margin-ticket-workflow
description: Run the Margin repository's single-ticket workflow. Use only in the Margin project when asked to implement, review, fix, or finalize one ticket from TASKS.md, including status checks, scope enforcement, verification, read-only review, and a focused Git commit. Do not use outside Margin or for multi-ticket or milestone-wide implementation.
---

# Margin Ticket Workflow

Operate on exactly one Margin ticket in one explicit mode: `implement`, `review`, `fix`, or
`finalize`. Treat `AGENTS.md`, `TASKS.md`, and the repository's product documents as the current
sources of truth; do not copy their requirements into this skill.

## Resolve the request

1. Require one mode and one ticket ID such as `M1-T06`. Ask for the missing value when either is
   ambiguous.
2. Locate the Margin repository root. Require `AGENTS.md`, `TASKS.md`, `ROADMAP.md`, and
   `MVP RFC — AI Reading Companion v0.md`; stop if they are absent.
3. Read `AGENTS.md` completely, then read the complete target ticket and every project document it
   requires for the requested work.
4. Inspect the worktree before acting. Preserve unrelated user changes and never silently absorb
   them into the ticket.
5. Never begin or partially implement another ticket.

## Implement mode

1. Confirm that the ticket is `Ready` and every listed dependency is `Done`. Stop and report the
   exact unmet condition otherwise.
2. Mark only the target ticket `In Progress` before changing implementation files.
3. Implement only the ticket's scope. Treat its out-of-scope list as a hard boundary.
4. Add or update the tests and documentation required by its acceptance criteria.
5. Record newly discovered required work as a separate ticket. Record worthwhile non-V0 concepts in
   `FUTURE_IDEAS.md`. Do not implement either during this invocation.
6. Run every ticket verification step plus the smallest relevant regression suite.
7. Mark the ticket `Done` only when every acceptance criterion passes. Leave it `In Progress` and
   report the blocker or failing criterion otherwise.
8. Mark a newly unblocked ticket `Ready` only when all of its dependencies are `Done` and its scope
   is sufficiently defined.
9. Do not commit and do not begin the next ticket.

## Review mode

Remain strictly read-only: do not edit files, update ticket status, fix findings, stage changes, or
commit. Reconstruct the requirements from repository artifacts rather than relying on an
implementer's explanation.

Review the target ticket against:

- every acceptance criterion and verification step;
- `AGENTS.md`, the RFC, architecture, roadmap, and relevant benchmark requirements;
- correctness, edge cases, state transitions, error handling, and retry behavior;
- security, secret handling, data ownership, and destructive-action risk;
- test quality and missing regression coverage;
- unnecessary abstractions, scope expansion, and work belonging to another ticket.

Report actionable findings first, ordered by severity, with precise file and line references. State
explicitly when there are no material findings. Identify unverified acceptance criteria and residual
risks separately. Do not praise or summarize before reporting findings.

## Fix mode

1. Require concrete review findings in the request or conversation.
2. Read the original ticket and validate each finding against its scope.
3. Reopen a `Done` ticket to `In Progress` before making material corrections.
4. Fix in-scope findings and add focused regression tests where practical.
5. Put adjacent required work in `TASKS.md` and deferred concepts in `FUTURE_IDEAS.md`; do not expand
   the active ticket silently.
6. Run the complete original verification plus checks covering the fixes.
7. Mark the ticket `Done` only when all original criteria and accepted findings pass.
8. Do not commit and do not begin the next ticket.

## Finalize mode

Treat an explicit `finalize` invocation as authorization to create one focused Git commit for the
ticket, but not to begin subsequent work.

1. Require the ticket to be `Done`.
2. Inspect the final diff and confirm it contains only the ticket and its required status or
   documentation updates. Stop if unrelated changes cannot be safely excluded.
3. Confirm the recorded verification is current; rerun checks when the diff changed after the last
   successful verification.
4. Stage only the target ticket's files. Never stage unrelated changes with a broad command.
5. Commit with `<ticket-id>: <concise imperative outcome>`.
6. Report the commit identifier, files committed, verification results, residual limitations, and
   the next eligible `Ready` ticket. Do not start it.

## Handoff format

For implement, fix, and finalize modes, report:

1. Outcome delivered.
2. Important files changed.
3. Acceptance criteria satisfied or still unmet.
4. Verification commands and results.
5. Known limitations and follow-up tickets or future ideas created.
6. Next ticket eligible to become or remain `Ready`.

For review mode, use the review-specific findings format above.

## Invocation examples

- `$margin-ticket-workflow implement M1-T01`
- `$margin-ticket-workflow review M1-T06`
- `$margin-ticket-workflow fix M1-T06 using these review findings: ...`
- `$margin-ticket-workflow finalize M1-T06`
