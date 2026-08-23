---
name: margin-deliver-ticket
description: Deliver one Margin TASKS.md ticket end to end through implementation, independent read-only review, correction, re-review, verification, a focused commit, branch push, and pull-request creation. Use only in the Margin repository when the user invokes this skill with one ticket ID or one uniquely matching ticket title and wants the complete ticket workflow without manually starting separate sessions.
---

# Margin Deliver Ticket

Orchestrate one ticket from `Ready` to a reviewed, verified, committed, and pushed branch. Reuse the
sibling `margin-ticket-workflow` skill for each ticket phase; do not duplicate its ticket rules here.

## Resolve the ticket and workflow

1. Require one ticket reference after the skill name. Accept an exact ticket ID such as `M1-T08` or
   a title that uniquely matches one entry in `TASKS.md`. Ask only when the reference is missing or
   ambiguous.
2. Read `../margin-ticket-workflow/SKILL.md` completely, then follow its repository discovery and
   governing-document requirements.
3. Inspect the worktree and branch before acting. Preserve unrelated user changes. Stop when the
   ticket cannot be isolated safely.
4. Confirm the selected ticket is `Ready`, every dependency is `Done`, and no other implementation
   ticket is `In Progress`.
5. Work on exactly the selected ticket. Never begin the next eligible ticket.

## Prepare isolated delivery

- Run all mutating phases sequentially; never let two agents edit the worktree concurrently.
- Use the current isolated worktree when one is already provided.
- Deliver on `codex/<lowercase-ticket-id>` unless the user explicitly names another branch. Create
  or switch to that branch only when safe. Never push directly to the default branch.
- Treat explicit invocation as authorization to create one focused commit, push the delivery
  branch, and open a pull request for this ticket. Do not merge the pull request.

## Run the delivery phases

### 1. Implement

Delegate to one implementation subagent with the resolved repository path and this exact task:

`Use $margin-ticket-workflow implement <ticket-id>.`

Wait for completion. Require the subagent to leave the ticket `Done` only when all acceptance
criteria and verification pass. If it reports a blocker or leaves the ticket `In Progress`, stop
and report the evidence; do not review or finalize incomplete work.

### 2. Review independently

Delegate to a fresh read-only reviewer subagent with only the repository path, ticket ID, and this
task:

`Use $margin-ticket-workflow review <ticket-id>.`

Do not provide the implementer's reasoning, summary, suspected defects, or intended answer. Wait
for the complete review. Treat unverified acceptance criteria as unresolved, not as a clean review.

### 3. Fix and re-review

When the reviewer reports material actionable findings or unverified required criteria:

1. Delegate a fix subagent with the exact review report:
   `Use $margin-ticket-workflow fix <ticket-id> using these exact review findings: <findings>`.
2. Wait for the fix and complete original plus fix-specific verification.
3. Delegate another review to a new read-only reviewer with no prior reasoning or conclusions.
4. Repeat until a fresh reviewer reports no material actionable findings and no required criterion
   remains unverified.

Allow at most three fix/review cycles. If material issues remain, stop without committing and
report the unresolved findings.

### 4. Finalize

Delegate to a fresh subagent:

`Use $margin-ticket-workflow finalize <ticket-id>.`

Wait for completion. Confirm the resulting commit contains only ticket-scoped files and required
status or documentation updates. Confirm verification is current after the last fix. Do not amend,
squash, or create additional commits unless required to correct a failed finalization check.

### 5. Push and open the pull request

1. Verify the focused commit, branch name, and clean separation from unrelated changes.
2. Push the delivery branch to `origin` without force.
3. When GitHub authentication and tooling are available, open one pull request against the default
   branch. Include the ticket outcome, verification results, and known limitations. Do not merge it.
4. If authentication or remote access is unavailable, preserve the local commit and report the
   exact missing prerequisite. Never weaken repository permissions or expose credentials.

## Operating rules

- Preserve unrelated changes, including `.agents/` content not required by the selected ticket.
- Stage explicit ticket files only; never use a broad staging command that can absorb unrelated
  work.
- Run every ticket verification step and the smallest relevant regression suite.
- Exercise browser acceptance criteria in a real browser and inspect runtime and console errors.
- Do not claim an unavailable or substituted check passed. Exhaust safe ticket-scoped alternatives,
  then report the precise limitation.
- Record newly discovered required work in `TASKS.md` and deferred concepts in `FUTURE_IDEAS.md`
  according to repository policy; do not implement them.
- Keep progress updates compact: phase, evidence, remaining work, and blocker status.

## Stop and completion conditions

Stop early only for a material unresolved product decision, missing credential or permission,
unsafe or destructive action, inseparable pre-existing changes, unmet ticket dependency, repeated
verification failure, or unresolved material findings after three review cycles.

Complete only when:

- the ticket is `Done` and every acceptance criterion is demonstrated;
- all required verification passes;
- a fresh independent reviewer reports no material actionable findings;
- exactly one focused ticket commit exists;
- the branch is pushed to `origin`; and
- a pull request is opened when authentication is available.

Report the outcome, important files, acceptance evidence, verification commands and results,
review findings and resolutions, commit hash, pushed branch, pull-request link, limitations,
follow-up work, and the next eligible ticket without starting it.

## Invocation examples

- `$margin-deliver-ticket M1-T08`
- `$margin-deliver-ticket Establish same-origin web-to-API communication`
