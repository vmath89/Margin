# **MVP RFC — AI Reading Companion v0**

## **Goal**

Build the **smallest web application** that proves this interaction:

> **Upload a document → listen → pause → ask → hear an answer → ask follow-ups → continue.**

The purpose of V0 is to validate whether this experience is compelling before building agents, long-term memory, sophisticated RAG, mobile apps, or personalization.

---

## **Core User Flow**

### **1\. Upload a document**

Support **PDF only** initially.

The system:

1. extracts the text;  
2. identifies chapters or sections where possible;  
3. creates a deterministic document map from extracted metadata and ordered section titles;
4. generates and caches a short section synopsis only when a selected question context needs one.

V0 does not generate or store a whole-document synopsis. The document map is orientation,
not evidence that a particular claim appears in the source.

---

### **2\. Listen**

The user presses:

**▶ Read**

The application reads the document aloud using high-quality text-to-speech.

The current paragraph is highlighted.

Pressing **Read** creates or resumes an active **reading session** for the document. A reading
session spans narration and every pause-and-discuss episode until the user explicitly ends the
session or starts a new one. Pressing **Continue Reading** does not end the reading session, and
a page reload does not silently discard it.

Basic controls:

* Play  
* Pause  
* Skip backward  
* Playback speed
* End reading session as a secondary action

---

### **3\. Ask something**

The user pauses and presses:

**🎙 Ask**

For example:

> “Explain this paragraph to me in detail.”

Speech is converted to text.

The system records the paragraph where the user stopped. That paragraph is the stable
reading-position anchor: it determines where narration resumes, but it is not the
complete semantic context for the question.

Asking begins a **conversational episode**. Reading remains paused while that episode
is active. The user can hear the answer, ask a follow-up, hear another answer, and
repeat before continuing.

---

## **4\. Document-context contract**

The reasoning model receives an explicit context package built by deterministic application
logic. It never chooses passages, searches the document, or infers that unsupplied source
text was retrieved. The anchored paragraph remains the episode's stable reading-position
anchor; it is not the complete semantic context boundary.

Every package ends with the current question and may include the following layers:

| Layer | Purpose | Contents and bound |
| --- | --- | --- |
| **Document orientation** | Identify the work and orient the explanation in its structure. It is not evidence for a precise textual claim. | Extracted title and author when available, document type, and an ordered document map of section titles. The map is limited by configured entry and character limits; omitted entries are marked as omitted. V0 stores this map, not a generated document synopsis. |
| **Current-section context** | Explain how the passage relates to the current section. | Current section title plus a cached generated synopsis for local or limited document-wide questions. The synopsis has a configured maximum length and is generated only from that section's bounded source text. A whole-section question receives the complete current section instead, which must fit the configured section-context limit. |
| **Local passage context** | Ground a passage-level explanation in immediate surrounding prose. | Up to two preceding ordered paragraphs, the unchanged anchored paragraph, and one following ordered paragraph, when those paragraphs exist. Paragraphs are included whole and in source order; configured paragraph limits are enforced during deterministic processing rather than by prompt-time truncation. |
| **Full-document source** | Ground an explicit document-wide question in the complete uploaded work when it safely fits. | Every normalized section and paragraph exactly once in canonical section and paragraph order, with section, paragraph, and available page markers. It replaces, rather than duplicates, local and current-section source context. It is included only after deterministic whole-prompt budget validation. |
| **Reading-session dialogue** | Preserve conversational continuity while the user alternates between reading and discussion. | Every complete question-and-answer turn from the active reading session, across both ended and active conversational episodes, excluding the current question. Turns are supplied in chronological order. V0 never silently drops, truncates, or summarizes a session turn. If the complete session dialogue plus required source context would exceed the configured model-input limit, the Ask is rejected clearly and the user is asked to begin a new reading session. |
| **Current question** | State the user's request. | The complete transcript for the current request, subject to a configured input limit that produces a clear error rather than silent truncation. |

The builder selects a scope by a simple, inspectable rule; it does not use a classifier or
retrieval model:

- **Local passage** is the default. It contains document orientation, current-section
  synopsis, local passage context, complete active-session dialogue, and the current question.
- **Current section** is used only when the question explicitly asks about the section or
  chapter as a whole. It contains document orientation, the full bounded current section,
  complete active-session dialogue, and the current question.
- **Full document** is used only when the question explicitly asks about the document as a
  whole or where else something appears *and* the complete required prompt fits the configured
  budget. It contains document orientation, the canonical full-document source, complete
  active-session dialogue, and the current question. It does not include a duplicate local
  window or section synopsis.
- **Limited document-wide** is used for the same explicit question forms when the full-document
  package does not fit. It contains document orientation, current-section synopsis, local
  passage context, complete active-session dialogue, and the current question. It performs no
  book-wide search and is explicitly labeled as limited.

Full-document eligibility is deterministic and model-call-free. Before selecting it, the builder
serializes the exact candidate prompt, including system and prompt instructions, all labels and
markers, orientation, canonical source, every complete active-session turn, and the complete
current question. It measures that normalized candidate with the configured deterministic token
estimator (or its conservative normalized-character equivalent). The candidate fits only when its
estimated input is no greater than `model_context_limit - reserved_answer_tokens - safety_margin`.
Character-mode enforcement converts that allowance with a configured conservative
characters-per-token value and counts the actual normalized assembled text; PDF page and word
counts are informational only. The builder never trims source text or dialogue to make this test
pass. If even the selected limited package cannot fit with every session turn and the question,
the Ask fails clearly and requires a new reading session.

Canonical full-document serialization walks persisted sections by ascending section order and
each section's paragraphs by ascending paragraph order. It emits each section marker and each
paragraph marker and text once, retaining start/end page markers when available. This lossless
ordered serialization is the entire supplied document; it is not retrieval, sampling, or a
generated summary.

Within one episode, every follow-up retains that episode's original anchored paragraph. Pressing
**Continue Reading** ends the episode but not the reading session. A later Ask in the same reading
session creates a new episode with a new anchor and still receives every complete earlier turn
from that reading session. Dialogue from an ended reading session is not included in a new one.

### **Source authority and safe claims**

The uploaded PDF and the normalized text supplied in the selected context are authoritative.
The model may say that the uploaded document states or implies something only when the
supplied source text supports that statement. A generated section synopsis and the document
map are orientation aids, not proof of a precise claim.

Reading-session dialogue is conversational memory, not additional source evidence. The model may
remember an earlier explanation or user preference from it, but a statement in an earlier answer
does not prove that the uploaded document contains that statement. New claims about the source
must remain grounded in source text supplied for the current request.

The model may use general knowledge about an identified work or subject only as clearly
labeled background. Background knowledge must not be presented as evidence from the
uploaded document and must never override supplied source text. The model must not claim
that a passage, theme, or argument appears elsewhere in the uploaded document unless the
builder supplied that evidence.

### **Document-wide answers and limitation shown to the user**

For an explicit document-wide question such as “Where else in the book does he discuss this?”,
V0 uses the complete normalized document only when the deterministic budget test passes. In that
case, it may identify locations or make document-wide claims only when the supplied canonical
source supports them, citing its supplied section, paragraph, or page markers where useful.

When that complete package does not fit, V0 says it is answering in **limited document-wide
context**: it examined the document orientation, current-section synopsis, local passage window,
and complete active-session dialogue, but did not examine the complete document. It must not
claim to have searched or analyzed the whole document, identify other locations as verified, or
present a best-effort interpretation as a search result. Full-document retrieval/RAG remains
deferred.

### **Question-type walkthrough**

The initial benchmark evaluates these question types against the contract:

| Question type | Selected scope | Grounding rule |
| --- | --- | --- |
| Explain a passage | Local passage | Explain from the anchor and local window; use the section synopsis only for context. |
| Author intent | Local passage by default | Describe intent as an interpretation of supplied wording and section context, not as an unsupported fact about the author. |
| Give an example | Local passage by default | Label a model-created or general-knowledge example as illustrative, not source text. |
| Follow-up connection | Same scope selected for the follow-up, plus complete active-session dialogue | Preserve the current episode's original anchor and distinguish a supported connection from background interpretation. |
| Counterargument | Local passage by default | Separate the document's argument from a reasoned or background counterargument. |
| Document-wide location or synthesis | Full document when its complete prompt fits; otherwise limited document-wide | Identify other locations or make cross-section claims only from the supplied canonical full-document source. In limited mode, clearly state the source layers examined and the whole-document limitation. |

This contract requires only ordered persisted source text, deterministic scope selection,
and bounded prompt assembly. It requires no embeddings, vector database, semantic search,
or hidden retrieval.

---

## **5\. Generate the explanation**

The architecture remains:

Speech  
   ↓  
Text  
   ↓  
Context builder  
   ↓  
Reasoning model  
   ↓  
Detailed textual answer  
   ↓  
Text-to-speech

We deliberately use a strong text reasoning model rather than relying on a low-latency speech-to-speech model for the core answer.

The generated answer is also displayed on screen.

---

## **6\. Hear the explanation**

The AI response is read aloud.

For V0, the user does **not** need to interrupt an answer while it is playing. That can
come later. After the answer finishes, the user may ask a follow-up while reading
remains paused. The follow-up stays in the same conversational episode, uses the
original anchored paragraph as its reading position, and receives the complete active reading
session dialogue as additional context.

---

## **7\. Continue reading**

After one or more answers, the user presses:

**▶ Continue Reading**

The document resumes from the original paragraph where they stopped. Continuing ends
the active conversational episode; a later Ask begins a new one at the then-current
paragraph. The reading session remains active, so the later Ask also receives all earlier
question-and-answer turns from that session. Exact sentence-level semantic resume is not
required yet.

---

# **Document Processing**

During upload, perform only:

PDF  
 ↓  
Extract text  
 ↓  
Identify chapters / sections  
 ↓  
Split into paragraphs  
 ↓  
Create document map
 ↓  
Store

Generate a short section synopsis lazily only when a local or limited document-wide question
needs it, then reuse that bounded synopsis for the section. A whole-section question uses
the bounded section text itself.

No embeddings are required.

No vector database is required.

No sophisticated retrieval system is required.

---

# **Suggested Data Structure**

A document can initially look like:

{  
  "title": "Letters from a Stoic",  
  "author": "Seneca",  
  "document_map": ["Letter I", "Letter II", "Letter III"],
  "chapters": \[  
    {  
      "title": "Letter I",  
      "cached_synopsis": "...",
      "paragraphs": \[  
        "...",  
        "...",  
        "..."  
      \]  
    }  
  \]  
}

The active reading session remembers:

{  
  "reading_session_id": "session_1",
  "document\_id": "doc\_1",  
  "chapter\_index": 3,  
  "paragraph\_index": 12  
}  

Each time reading is paused for discussion, a conversational episode adds one immutable anchored
paragraph and an ordered set of textual question-and-answer interactions. Continue ends that
episode but retains it inside the active reading session. Every later reasoning request in the
same reading session receives all complete interactions from all of its episodes in chronological
order. If the whole required prompt no longer fits the configured limit, V0 asks the user to start
a new session rather than silently omitting or summarizing earlier turns.
---

# **Prompt Structure**

A typical request to the reasoning model should look like:

You are an expert reading companion.

Your job is to help the user deeply understand the document they are reading.

DOCUMENT:  
{title}  
{author}

CONTEXT SCOPE:
{local passage | current section | full document | limited document-wide}

DOCUMENT ORIENTATION:
{title, author if available, document type, bounded ordered document map}

FULL DOCUMENT SOURCE (full-document scope only; canonical source order):
{each section and paragraph exactly once, with available markers}

CURRENT CHAPTER:  
{chapter\_title}

CHAPTER CONTEXT:  
{cached\_section\_synopsis OR full bounded current section when section scope is selected}

LOCAL CONTEXT:  
{previous\_paragraphs}

CURRENT PARAGRAPH:  
{current\_paragraph}

NEXT PARAGRAPH:  
{next\_paragraph}

READING SESSION DIALOGUE:
{all\_complete\_prior\_question\_and\_answer\_turns\_from\_this\_reading\_session}

USER QUESTION:  
{question}

Answer the user's question carefully and at the depth they request.

When explaining a passage:  
\- explain what the author is saying;  
\- explain why it matters in the context of the chapter;  
\- clarify difficult phrases where relevant;  
\- do not reduce a requested deep explanation to a short summary;  
\- distinguish clearly between what the text says and your interpretation;  
\- label general knowledge and invented examples as background or illustration;
\- do not claim that unsupported material appears elsewhere in the uploaded document;
\- for a full-document question, identify locations only when the supplied canonical full source
  supports them; for limited document-wide context, state the layers examined and that the
  complete document was not examined;
\- do not invent claims unsupported by the provided context.  
---

# **UI**

One simple screen is enough:

┌───────────────────────────────────────────────────────┐  
│                    Book / Paper                       │  
├───────────────────────────────────────────────────────┤  
│                                                       │  
│  Previous paragraph...                                │  
│                                                       │  
│  ► CURRENT PARAGRAPH BEING READ                       │  
│                                                       │  
│  Next paragraph...                                    │  
│                                                       │  
├───────────────────────────────────────────────────────┤  
│                                                       │  
│  AI                                                   │  
│  Seneca is essentially arguing that...                │  
│                                                       │  
├───────────────────────────────────────────────────────┤  
│        ⏪        ▶ / ⏸        🎙 Ask        1×         │  
└───────────────────────────────────────────────────────┘  
---

# **Tech Stack**

### **Frontend**

**Next.js \+ React**

### **Backend**

**Python \+ FastAPI**

### **Reasoning**

One strong reasoning model through the backend's single OpenRouter gateway. Model IDs are
configuration, but V0 does not add provider interchangeability, routing, or provider-specific
credentials.

### **Speech input**

Speech-to-text API.

### **Speech output**

High-quality TTS API.

### **Storage**

SQLite is the V0 database.

Store:

documents  
chapters  
paragraphs  
document maps and lazily cached section synopses
reading position  
reading sessions and conversational episodes
textual question-and-answer interactions
---

# **Explicitly Not Building Yet**

V0 does **not** include:

* autonomous agents;  
* multi-agent systems;  
* embeddings;  
* vector databases;  
* full-document RAG or retrieval beyond the bounded canonical full-document scope;
* cross-session conversation recall or learner memory;
* personalized knowledge graphs;  
* external web research;  
* cross-book connections;  
* native mobile apps;  
* Kindle integration;  
* publisher integrations;
* interruption while an AI answer is playing;
* wake words, voice activity detection, or streaming speech-to-speech.

The only intelligence beyond basic prompting is the **hierarchical document context**.

---

# **What We Need to Prove**

We only need to answer three questions.

### **1\. Is the explanation quality good enough?**

Does giving the model:

> document context \+ chapter context \+ local passage

produce explanations that feel genuinely useful?

### **2\. Does voice materially improve the reading experience?**

Is it easier to stay with difficult material when questions can be asked without leaving the reading experience?

### **3\. Does the core loop feel natural?**

Does:

> **Listen → Pause → Ask → Answer → Follow-up → Answer → Continue**

feel substantially better than manually switching between a reader and ChatGPT?

Does the interaction still feel continuous after the reader resumes narration, reaches another
passage, and asks a question that refers to an earlier discussion from the same reading session?

---

# **Definition of Done**

V0 is done when I can:

1. upload a PDF;  
2. have the system identify its chapters;  
3. have it create a document map and generate a bounded section synopsis only when needed;
4. press **Read**;  
5. listen to the document;  
6. pause on a paragraph;  
7. press **Ask**;  
8. say:  
   **“Explain this entire paragraph to me in detail.”**  
9. receive an explanation that understands both the paragraph and the chapter context;  
10. hear that explanation naturally;  
11. ask at least one follow-up question while reading remains paused;
12. receive and hear a follow-up answer that uses the original anchored passage and active-session dialogue;
13. press **Continue**;
14. keep listening from the original anchored paragraph;
15. pause later in the same reading session at a different paragraph;
16. ask a question that refers to the earlier conversation;
17. receive an answer that uses the complete earlier session dialogue while grounding new source
    claims in the newly anchored passage and its selected context.

At that point, stop building features and use the product on a real difficult book.

The central MVP principle is:

> **Give the model enough context to understand the text deeply, but do not build retrieval infrastructure until real usage proves that we need it.**
