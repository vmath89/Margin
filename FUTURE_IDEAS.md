# Margin Future Ideas

## Purpose

This file is the durable register for product and engineering ideas that are intentionally outside
V0. It prevents useful ideas from disappearing without turning them into commitments prematurely.

`ROADMAP.md` remains the source of truth for committed milestone outcomes. `TASKS.md` remains the
source of truth for approved, actionable work. An entry in this file is neither approval nor
authorization to implement it.

## How to use this register

- Capture a deferred idea when it arises in product discussion or implementation discovery.
- State why it is not part of V0 and what evidence would justify reconsidering it.
- Do not assign delivery dates or detailed implementation plans before promotion.
- Do not implement an idea directly from this file.
- Promote an idea only through an explicit product decision that updates `ROADMAP.md` and creates
  one or more implementation-ready tickets in `TASKS.md`.
- When promoted, rejected, or merged with another idea, retain the entry and update its status and
  links so the decision history remains visible.

Allowed statuses:

- `Captured` — worth remembering, but not prioritized or committed.
- `Investigating` — evidence is being gathered; implementation is still not authorized.
- `Promoted` — approved into a roadmap milestone and linked backlog ticket.
- `Rejected` — deliberately declined, with the reason recorded.

## Conversation and learner continuity

### FI-001 — Recall ended reading sessions

**Status:** Captured  
**Candidate horizon:** Post-V0 / V2

Allow a new reading session to recall relevant discussions from earlier sessions on the same
document. V0 includes the complete active-session dialogue only.

**Revisit when:** Users repeatedly refer to earlier sessions or report that starting a new session
makes the companion feel forgetful.

### FI-002 — Compact long active-session dialogue

**Status:** Captured  
**Candidate horizon:** Post-V0 / V2

Summarize or otherwise compact older active-session turns while preserving important distinctions,
reader intent, unresolved questions, and source-grounding boundaries. V0 instead requires starting
a new session when the complete prompt no longer fits.

**Revisit when:** Real sessions regularly reach the configured context limit.

### FI-003 — Persistent learner model and explanation preferences

**Status:** Captured  
**Candidate horizon:** Later version

Learn what the reader knows, where they struggle, and whether examples, analogies, first principles,
historical context, mathematics, or debate work best for them.

**Revisit when:** Repeated use shows stable preferences that would materially improve explanations.

### FI-004 — Cross-document connections and personal knowledge graph

**Status:** Captured  
**Candidate horizon:** Later version

Connect ideas, passages, highlights, and conversations across books, papers, and reading sessions.

**Revisit when:** Users have read multiple documents in Margin and request connections across them.

## Retrieval and knowledge

### FI-005 — Retrieval for oversized documents

**Status:** Captured  
**Candidate horizon:** Post-V0 / V2

Use evidence-bearing full-document retrieval for documents that do not fit the bounded canonical
full-document scope. Possible techniques may include embeddings, lexical search, hybrid retrieval,
reranking, and source-linked context assembly; none is selected yet.

**Revisit when:** Oversized documents frequently trigger limited document-wide answers and those
limitations materially reduce usefulness.

### FI-006 — External web research

**Status:** Captured  
**Candidate horizon:** Later version

Let the companion research external background, current facts, criticism, or related scholarship
while clearly separating external sources from the uploaded document.

**Revisit when:** Readers frequently need information unavailable in the document or model's safe
background knowledge.

## Navigation and reading controls

V0 provides only deterministic navigation to the saved position, document beginning, or a flat
ordered detected/fallback section list. The ideas below remain outside that contract.

### FI-007 — Full-text and phrase search

**Status:** Captured  
**Candidate horizon:** Post-V0

Find exact words, phrases, names, or concepts and navigate to matching passages.

**Revisit when:** Section-based navigation is insufficient for locating known passages.

### FI-008 — Semantic and voice-controlled navigation

**Status:** Captured  
**Candidate horizon:** Post-V0 / V2

Support commands such as “take me to the chapter about monetary policy,” “go to chapter seven,” or
“return to the passage we discussed earlier.”

**Revisit when:** Users naturally attempt these commands during hands-free use.

### FI-009 — Bookmarks, highlights, annotations, and named locations

**Status:** Captured  
**Candidate horizon:** Post-V0

Allow readers to save, label, annotate, and revisit important passages.

**Revisit when:** Dogfooding shows repeated manual attempts to remember or return to passages.

### FI-010 — Rich document navigation

**Status:** Captured  
**Candidate horizon:** Later version

Add nested tables of contents, page thumbnails, printed-page-number mapping, and arbitrary
sentence-level positioning. V0 uses a flat ordered section picker and paragraph anchors.

**Revisit when:** Real documents expose significant friction that a flat section list cannot solve.

### FI-011 — Sentence-level audio alignment and resume

**Status:** Captured  
**Candidate horizon:** Post-V0 / V2

Highlight and resume at the exact spoken sentence or word rather than restarting the paragraph.

**Revisit when:** Paragraph-level restart repeatedly disrupts the listening experience.

## Speech and interaction

### FI-012 — Real-time speech-to-speech conversation

**Status:** Captured  
**Candidate horizon:** Later version

Support lower-latency conversational speech, streaming responses, and more natural turn-taking while
retaining the option for deep, reasoned answers.

**Revisit when:** Measured transcription, reasoning, or synthesis latency prevents the V0 loop from
feeling conversational.

### FI-013 — Wake words, voice activity detection, and answer interruption

**Status:** Captured  
**Candidate horizon:** Post-V0 / V2

Allow hands-free pausing and questioning, detect conversational turns, and let the reader interrupt
an answer that is already playing.

**Revisit when:** Users frequently reach for explicit controls or want to redirect long answers.

## Documents, platforms, and distribution

### FI-014 — EPUB, articles, and additional text formats

**Status:** Captured  
**Candidate horizon:** Post-V0

Support EPUB, web articles, essays, and other structured text formats beyond text-based PDFs.

**Revisit when:** The PDF V0 proves compelling and format availability becomes a primary adoption
constraint.

### FI-015 — OCR and difficult PDF support

**Status:** Captured  
**Candidate horizon:** Post-V0 / V2

Handle scanned, image-only, malformed, encrypted where authorized, multi-column, and otherwise
difficult PDFs through OCR or more capable document processing.

**Revisit when:** A meaningful share of desired documents fail V0 extraction.

### FI-016 — Native mobile application

**Status:** Captured  
**Candidate horizon:** Later version

Provide a native mobile experience optimized for walking, commuting, exercising, background audio,
and device-level media controls.

**Revisit when:** The web experience proves repeat use and mobile constraints block core behavior.

### FI-017 — Kindle and publisher integrations

**Status:** Captured  
**Candidate horizon:** Later version

Integrate licensed books, existing libraries, reading positions, and publisher content workflows.

**Revisit when:** Content acquisition and rights become more important than interaction validation.

### FI-018 — Library, social, marketplace, and publishing ecosystem

**Status:** Captured  
**Candidate horizon:** Later version

Add broader product surfaces around document libraries, sharing, discovery, social use, publishing,
or a marketplace.

**Revisit when:** The core reading loop demonstrates retention and a clear ecosystem need emerges.

## Product intelligence and infrastructure

### FI-019 — Autonomous or multi-agent workflows

**Status:** Captured  
**Candidate horizon:** Later version

Use agents for tasks that demonstrably require planning or multiple tool-driven steps. V0 uses an
explicit deterministic context builder and direct model operations.

**Revisit when:** A validated user workflow cannot be handled reliably by the simpler architecture.

### FI-020 — Multi-provider routing and provider abstraction

**Status:** Captured  
**Candidate horizon:** Later version

Support direct providers, capability registries, or runtime routing beyond the single OpenRouter
gateway.

**Revisit when:** Availability, cost, quality, compliance, or provider-specific features create a
measured need.

### FI-021 — Accounts, multi-user isolation, billing, and production scale

**Status:** Captured  
**Candidate horizon:** After single-user validation

Add authentication, authorization, quotas, billing, durable job processing, scalable persistence,
and multi-host production operations.

**Revisit when:** The single-user prototype proves valuable enough to onboard additional users.
