# Prompt: Design a Human-Friendly Margin Planning Visualizer

Copy the prompt below into a new Codex session when you are ready to design this tool.

---

I want to design a human-friendly visual planning companion for the Margin repository.

Do not implement or modify anything yet. Begin with repository inspection, product/design
discussion, and a decision-complete implementation plan. Wait for my explicit approval before
editing files.

Repository:
`/Users/visheshmathur/Margin`

Primary source files:

- `ROADMAP.md`
- `TASKS.md`

Before proposing changes, read:

- `AGENTS.md`
- `Founding Thesis.md`
- `MVP RFC — AI Reading Companion v0.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `TASKS.md`
- `FUTURE_IDEAS.md`
- `DEVELOPMENT.md`

Follow all ticket-selection and change-discipline rules in `AGENTS.md`. Do not attach this work to
an existing M2 product implementation ticket. Determine whether this planning tool requires its
own documentation/tooling ticket and include that recommendation in the plan.

## Goal

Design a generated visual planning view that makes the roadmap and task backlog understandable to
a human reviewer without requiring them to read the complete Markdown files linearly.

The Markdown planning documents must remain authoritative. The visual view is a generated
read-only companion and must not become a second source of truth.

The current plan has:

- M0: complete product and architecture alignment
- M1: complete application foundation
- M2: six dependency-ordered tickets for the first conversational-reading prototype
- M3: outcome-level reader and context expansion ideas to revisit after M2
- M4: outcome-level hardening and dogfooding ideas to revisit after M3

Verify all of that against the repository rather than trusting this summary.

## What the visual should help me understand

At a glance, I should be able to answer:

1. What has already been completed?
2. What milestone are we working toward now?
3. Which ticket is currently eligible to begin?
4. What depends on what?
5. What will each ticket deliver in simple human language?
6. Why is each ticket necessary?
7. What is deliberately excluded from each ticket?
8. How will we know when the ticket is complete?
9. Where will human judgment, testing, approval, or feedback be required?
10. Which ideas are intentionally retained for M3 or M4 rather than silently discarded?

## Required views

Design an interface with two levels.

### 1. Milestone overview

Show:

- milestone number and title;
- status;
- concise outcome;
- relationship to the previous and next milestone;
- which ideas are included;
- which capabilities are deferred;
- a clear distinction between committed/decomposed work and outcome-level ideas that will be
  reconsidered later.

M3 and M4 must not look like implementation commitments. They should be visibly labeled as ideas
and outcome criteria to revisit after evidence from the preceding milestone.

### 2. Ticket detail

For every implementation ticket, provide a human-readable view with:

- Ticket ID and status
- Dependency or predecessor
- “What are we building?”
- “Why does this matter?”
- “What will the user be able to do afterward?”
- “What important technical work is involved?”
- “What are we deliberately not doing?”
- “How will we know it is finished?”
- “Risks or uncertainties”
- “Where human feedback is needed”
- Link or reference back to the authoritative Markdown section

Rewrite or summarize the information in straightforward human language. Do not merely dump the
existing Scope and Acceptance Criteria sections into differently styled boxes.

Preserve important technical constraints, but explain them plainly. For example, translate
concepts such as immutable episode anchors, complete active-session dialogue, deterministic context
limits, fake provider testing, and authoritative source text into language a non-specialist
reviewer can understand.

## Human-feedback markers

Create a consistent visual convention for human involvement. Consider categories such as:

- Decision needed before implementation
- Manual product or UX review
- Live-provider verification
- Content or answer-quality judgment
- Security/privacy review
- Acceptance sign-off
- No special human decision required

Do not invent a human decision for every ticket. If no special decision is required, say that
normal acceptance review is sufficient.

For each actual feedback point, explain:

- what the human must inspect or decide;
- when that feedback is needed;
- what evidence should be presented;
- whether work can continue without it.

## Source-of-truth and drift problem

A major design requirement is preventing the visual view from becoming stale.

Compare approaches for producing the plain-language summaries and human-feedback notes:

1. Deterministically deriving them from the existing Markdown structure.
2. Adding a small structured sidecar file keyed by milestone/ticket ID.
3. Adding optional human-review metadata to `TASKS.md`.
4. Generating summaries with an AI model during the build process.

Recommend one approach. Consider:

- duplication of information;
- reviewer readability;
- deterministic output;
- maintenance burden;
- whether missing or stale summaries can be detected;
- whether using AI during generation would make output inconsistent;
- how changes to task IDs, dependencies, or statuses are validated.

Do not silently choose an approach if it creates a second manually maintained planning source.

## Technical expectations

Prefer a small static generated site or standalone HTML output that:

- needs no backend or database;
- works locally;
- contains no provider credentials or private source content;
- uses accessible semantic HTML;
- works on desktop and mobile;
- supports keyboard navigation;
- uses restrained interaction—such as selecting a milestone or ticket to inspect details;
- does not introduce a large frontend framework without a demonstrated need;
- is generated from repository files rather than maintained by hand;
- can show the source commit or content hash used to generate it;
- can detect malformed headings, duplicate ticket IDs, missing dependencies, invalid statuses, and
  references to nonexistent tickets;
- has one documented generation command;
- can be regenerated reliably after `ROADMAP.md` or `TASKS.md` changes.

The generated output should be easy to open locally. Decide whether generated HTML should be
committed, ignored, or produced as a disposable artifact, and explain the tradeoff.

Do not change Margin’s product runtime, API, database, or existing web application merely to host
this internal planning view.

## Design expectations

Keep the interface focused. Avoid turning it into a generic project-management dashboard.

The central visualization should make the milestone sequence and M2 ticket dependency chain
immediately understandable. Selecting a ticket should reveal its human-language explanation,
boundaries, completion evidence, and feedback points.

Use status and color carefully, but do not rely on color alone. Avoid invented progress
percentages, effort estimates, dates, or health scores unless they exist in the source documents.

## Verification expectations

The eventual implementation plan should include tests for:

- parsing milestones and tickets;
- status and dependency validation;
- missing or duplicate IDs;
- Markdown structural changes;
- correct ordering of M2-T01 through M2-T06;
- output escaping and safe rendering;
- keyboard accessibility;
- responsive layout;
- stale-source detection;
- preservation of deferred M3/M4 ideas;
- successful generation from the repository’s current planning documents.

## First response

Do not implement anything in your first response.

First:

1. Inspect the repository and existing planning structure.
2. Explain the core information-design problem.
3. Recommend the source-of-truth strategy.
4. Propose the visual hierarchy and interactions.
5. Identify decisions that genuinely require my input.
6. Provide a decision-complete implementation plan, including whether a new ticket is required.

Do not edit files, install dependencies, create the viewer, or modify ticket statuses until I
approve the design and work-selection approach.
