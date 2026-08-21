# M1-T05 reasoning and context-contract spike

## Decision

Use `openai/gpt-5.6-sol` as the initial reasoning model with the explicit prompt shape and source-
authority guardrails exercised here. In the 2026-08-21 live run, the model produced useful,
grounded answers for B1–B7 and coherent same-session continuity for S1–S3. The complete B6 prompt
fit both deterministic budget modes and produced a grounded multi-section synthesis. The refined B7
prompt disclosed every supplied layer, stated that it had not examined the complete document, and
made no claim of search, retrieval, or verified locations outside the local source window.

This report validates a capability and recommends initial configuration. It does not implement the
production context builder, prompt persistence, automated evaluation, retrieval, or the application
OpenRouter boundary.

## Selected configuration

| Input | Initial value or rule |
| --- | --- |
| Reasoning model | `openai/gpt-5.6-sol` |
| Fitting capability profile | 128,000-token model context limit |
| Reserved answer capacity | 4,096 tokens |
| Safety margin | 2,048 tokens |
| Deterministic token estimator | `tiktoken` 0.11.0, explicit `o200k_base` encoding, plus versioned request-framing overhead |
| Conservative character estimator | 3.0 normalized characters per token |
| Maximum transcribed question | 2,000 normalized characters; reject the complete transcript rather than truncate it |
| Full-document fit rule | Exact estimated input must be no greater than `context limit - answer reserve - safety margin` in the configured enforcement mode |
| Session overflow behavior | Reject the Ask clearly, preserve the episode and reading position, and require a new reading session; never drop, truncate, or summarize a source paragraph or session turn |

The 128,000-token value is an application capability profile, not a claim about the provider's
maximum. It leaves substantial room above the selected Constitution prompt while remaining portable
to future model choices with at least that configured capacity. A 4,096-token answer reserve covered
the longest observed answer (2,329 provider completion tokens) with 1,767 tokens remaining. The
2,048-token safety margin covers estimator drift and request framing but is not permission to omit
content. The 2,000-character question limit is compatible with M1-T03's 120-second recording limit
for normal spoken English while bounding abusive or accidental transcripts; later dogfooding should
measure whether legitimate questions approach it.

Both estimator modes are viable. `o200k_base` was within four tokens of the provider's reported
input for every live call; the four-token difference is request framing outside the message text.
Production must version and include that fixed overhead for its exact request contract. The 3.0
characters-per-token rule was more conservative for this English legal corpus and provides a simple
fallback when the selected model lacks a validated tokenizer. Configuration must select one
enforcement mode; it must not pick whichever estimate makes a candidate fit.

## Prompt and package shape

Every request used two messages. The system message states that uploaded source is authoritative;
orientation, generated synopses, and dialogue are not evidence for new source claims; interpretation,
background, and illustrations need labels; and document-wide locations require supplied canonical
source. The user message serializes, in order:

1. context-scope label;
2. title, author, document type, and ordered section map;
3. exactly one scope-appropriate source package;
4. every complete earlier turn from the active reading session in episode/turn order;
5. the complete current question; and
6. a final reminder that dialogue is conversational memory rather than source authority.

Local packages contained the section title, a clearly non-authoritative generated synopsis, and up
to two preceding whole paragraphs, the unchanged anchor, and one following whole paragraph. B5
contained the complete bounded Article I and no synopsis or duplicate local window. B6 contained all
37 sections and 154 normalized paragraphs once in canonical order with section, paragraph, and page
markers; it contained no duplicate local or section context. B7 contained orientation, the Article I
synopsis, the P2 local window, and complete active-session dialogue (empty in the isolated case), but
no partial canonical document.

Generated prompts and complete answers remain in ignored `var/spikes/m1-t05/` because they are
reproducible diagnostics rather than application data or committed fixtures. The committed spike
script contains no API key and accepts it only through `OPENROUTER_API_KEY`.

## Exact budget measurements

The source input is the checksum-pinned Constitution PDF used by M1-T02. Its canonical source has
53,125 characters, 37 section markers, and 154 paragraph/page markers.

| Candidate | Profile | Exact candidate characters | Estimated input tokens | Input allowance | Character allowance | Token decision | Character decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| B6 full document | 128,000 | 55,680 | 12,845 | 121,856 | 365,568 | Fit | Fit |
| B7 full document | 16,000 | 55,533 | 12,819 | 9,856 | 29,568 | Over budget | Over budget |
| B7 selected limited package | 16,000 | 5,190 | 1,221 | 9,856 | 29,568 | Fit | Fit |

These final measurements include the refined system instructions. The exact candidate is normalized
message text with explicit role labels; it includes all instructions, labels, markers, source,
complete dialogue, and question. Answer reserve and safety margin are subtracted from the model
context limit rather than appended to the candidate text.

Independent arithmetic reproduced both decisions:

- B6: `128,000 - 4,096 - 2,048 = 121,856` input tokens; `12,845 <= 121,856`.
  Character allowance is `121,856 * 3.0 = 365,568`; `55,680 <= 365,568`.
- B7 full candidate: `16,000 - 4,096 - 2,048 = 9,856` input tokens;
  `12,819 > 9,856`. Character allowance is `9,856 * 3.0 = 29,568`;
  `55,533 > 29,568`.

The fit calculation made no model call. The spike asserts that the full source has exactly 37
section and 154 paragraph markers, and that B5/B6 have no forbidden duplicate source layer. When B7
was over budget, the selection changed to a separately assembled complete limited package; no source
or dialogue was trimmed to force a fit.

## Live benchmark results

All initial calls returned HTTP 200 through OpenRouter and were routed to OpenAI. The provider
reported 30,302 input tokens, 6,997 completion tokens, and USD 0.19785875 across the ten B1–B7 and
S1–S3 calls. Latency ranged from 3.394 to 40.397 seconds, with an 8.332-second median. The refined
B7 validation added 1,225 input tokens, 809 completion tokens, 15.207 seconds, and USD 0.01596125.
Costs and latency are point measurements, not guarantees.

| Case | Scope and dialogue | Exact chars | Provider input / output tokens | Latency | Cost | Manual evaluation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| B1 | P1 local; none | 3,359 | 840 / 234 | 4.863 s | $0.005610 | Pass: accurate everyday paraphrase of every Preamble aim; interprets “We the People” without inventing an operative rule. |
| B2 | P2 local; none | 4,964 | 1,173 / 288 | 5.843 s | $0.007984 | Pass: labels checks, deliberation, and accountability as interpretation and grounds the procedural sequence in P2. |
| B3 | P2 local; none | 4,935 | 1,173 / 115 | 3.394 s | $0.005389 | Pass: explicitly made-up hospital example correctly uses bicameral passage, objection, and two-thirds votes. |
| B4 | P3 local; none | 4,045 | 984 / 272 | 8.180 s | $0.006540 | Pass: separates a democratic criticism from what the electoral text states. |
| B5 | Complete Article I; none | 17,074 | 4,127 / 1,952 | 33.273 s | $0.042175 | Pass: covers vesting, bicameral structure, bill procedure, enumerated powers, procedural checks, and express limits from the complete section. |
| B6 | Canonical full document; none | 55,545 | 12,824 / 2,329 | 40.397 s | $0.075008 | Pass: identifies supplied paragraph markers across Article I, Article II, and Amendment XIV and distinguishes horizontal federal checks from state-action limits. |
| B7 initial | Limited; none | 5,055 | 1,200 / 603 | 11.750 s | $0.012793 | Guardrail refinement: disclosed orientation, synopsis, local window, and incomplete-document status, but did not explicitly state that the dialogue layer was empty. It labeled other locations unverified background and did not claim search. |
| B7 refined | Limited; none | 5,190 | 1,225 / 809 | 15.207 s | $0.015961 | Pass: names all four layers including empty dialogue, states the complete document was not examined, confines verified claims to P2's window, and makes no retrieval/search claim. |
| S1 | P1 local; complete B1 turn, same episode | 4,196 | 1,019 / 459 | 8.483 s | $0.009433 | Pass: naturally uses the earlier explanation and separates Preamble goals from rules needing later supplied text. |
| S2 | Complete Article I; complete B5 turn, same episode | 24,661 | 5,598 / 285 | 6.251 s | $0.021767 | Pass: connects the earlier synthesis to vesting, bicameralism, presentment, and override without invoking another Article. |
| S3 | P2 local; complete ended-episode B1 turn | 5,824 | 1,364 / 460 | 9.918 s | $0.011161 | Pass: remembers the goals-versus-rules distinction, uses the new P2 anchor, and labels the Preamble connection as interpretation rather than retrieved P1 evidence. |

The table retains the initial prompt measurements for the original ten-call run; the final budget
table above is authoritative after the B7 guardrail refinement. Manual review used `BENCHMARK.md`'s
grounding, usefulness, depth, and conversational-continuity rubric. No answer treated a generated
synopsis or earlier dialogue as proof of a new source claim. B3 labeled its invented facts. B4 and
B6 labeled interpretive conclusions. The refined B7 verified only claims visible in paragraphs
25–28 and treated the synopsis as orientation.

## Risks and implementation requirements

- **Latency:** B5 and B6 took 33.273 and 40.397 seconds. M3 needs an explicit waiting state, a
  provider timeout comfortably above these point measurements, and stable retry/error behavior.
- **Cost concentration:** B6 alone cost $0.075008, about 38% of the initial run. Full-document asks
  should remain explicit and budget-gated; provider cost and usage should be measured without
  logging prompts or answers.
- **Answer length:** B5 produced 1,952 completion tokens and was thorough but long for spoken
  playback. The 4,096-token reserve is appropriate for safety, while prompt tuning may later improve
  spoken structure without silently lowering the hard reserve.
- **Tokenizer coupling:** `o200k_base` matched this route closely but is not an architecture
  invariant. A model change requires revalidating the estimator and framing overhead, or selecting
  conservative character mode.
- **Provider behavior:** Model availability, routing, price, latency, token accounting, and context
  limits can change. Configuration must remain backend-only and later opt-in live smoke tests must
  detect drift.
- **Guardrail sensitivity:** The initial B7 response shows that a general disclosure instruction can
  omit an empty layer even while remaining substantively honest. The production prompt should retain
  the explicit four-layer disclosure and deterministic UI/API scope metadata should not rely solely
  on model wording.
- **Dialogue growth:** S2 grew to 5,598 provider input tokens after one long B5 answer. Complete
  session history can exhaust the allowance faster than the selected source alone; overflow must
  fail explicitly and require a new session.
- **No automatic grader:** Evaluation was manual and covers one public-domain English document.
  M5 must repeat B1–B7 and S1–S3 against the implemented contract and record dogfooding failures.

## Reproduction

From the repository root, with CPython 3.12 and `uv` installed:

```sh
uv run --python 3.12 \
  --with pypdf==6.1.1 \
  --with pdfplumber==0.11.7 \
  --with tiktoken==0.11.0 \
  python docs/spikes/m1-t05_reasoning.py self-test

OPENROUTER_API_KEY="$(sed -n 's/^OPENROUTER_API_KEY=//p' .env)" \
  uv run --python 3.12 \
  --with pypdf==6.1.1 \
  --with pdfplumber==0.11.7 \
  --with tiktoken==0.11.0 \
  python docs/spikes/m1-t05_reasoning.py live var/spikes/m1-t05/live-results.json
```

The final local verification used CPython 3.13.14 because `uv` was unavailable on this machine;
the three pinned libraries matched the command above. The framework Python certificate store could
not validate the endpoint chain, so live requests used the installed `certifi` CA bundle through
`SSL_CERT_FILE`; TLS verification remained enabled. The first failed TLS attempt reached no model.
