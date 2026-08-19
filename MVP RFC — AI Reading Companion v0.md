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

Basic controls:

* Play  
* Pause  
* Skip backward  
* Playback speed

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
| **Current-section context** | Explain how the passage relates to the current section. | Current section title plus a cached generated synopsis for local or limited book-wide questions. The synopsis has a configured maximum length and is generated only from that section's bounded source text. A whole-section question receives the complete current section instead, which must fit the configured section-context limit. |
| **Local passage context** | Ground a passage-level explanation in immediate surrounding prose. | Up to two preceding ordered paragraphs, the unchanged anchored paragraph, and one following ordered paragraph, when those paragraphs exist. Paragraphs are included whole and in source order; configured paragraph limits are enforced during deterministic processing rather than by prompt-time truncation. |
| **Recent dialogue** | Make a follow-up coherent within the paused conversational episode. | The newest complete question-and-answer turns from the active episode, excluding the current question. The builder keeps only whole turns that fit configured maximum turn and character budgets; it never includes turns from another episode. Persisted interactions outside that bounded selection are not model context. |
| **Current question** | State the user's request. | The complete transcript for the current request, subject to a configured input limit that produces a clear error rather than silent truncation. |

The builder selects a scope by a simple, inspectable rule; it does not use a classifier or
retrieval model:

- **Local passage** is the default. It contains document orientation, current-section
  synopsis, local passage context, bounded recent dialogue, and the current question.
- **Current section** is used only when the question explicitly asks about the section or
  chapter as a whole. It contains document orientation, the full bounded current section,
  bounded recent dialogue, and the current question.
- **Limited book-wide** is used only when the question explicitly asks about the document
  as a whole or where else something appears. It contains document orientation,
  current-section synopsis, local passage context, bounded recent dialogue, and the
  current question. It performs no book-wide search.

For every follow-up, the builder retains the original anchored paragraph and adds dialogue
only from the same active episode. Pressing **Continue Reading** ends that episode; the
next Ask starts a new episode with a new anchor and no previous episode dialogue.

### **Source authority and safe claims**

The uploaded PDF and the normalized text supplied in the selected context are authoritative.
The model may say that the uploaded document states or implies something only when the
supplied source text supports that statement. A generated section synopsis and the document
map are orientation aids, not proof of a precise claim.

The model may use general knowledge about an identified work or subject only as clearly
labeled background. Background knowledge must not be presented as evidence from the
uploaded document and must never override supplied source text. The model must not claim
that a passage, theme, or argument appears elsewhere in the uploaded document unless the
builder supplied that evidence.

### **Book-wide limitation shown to the user**

V0 has no full-document retrieval. For a question such as “Where else in the book does he
discuss this?”, it must say that it can discuss the current passage and section but cannot
verify other locations in the uploaded document. It may offer a clearly labeled
best-effort interpretation from the supplied orientation, section, and local context; it
must not present that interpretation as a search result. Full-document retrieval comes later.

### **Question-type walkthrough**

The initial benchmark evaluates these five question types against the contract:

| Question type | Selected scope | Grounding rule |
| --- | --- | --- |
| Explain a passage | Local passage | Explain from the anchor and local window; use the section synopsis only for context. |
| Author intent | Local passage by default | Describe intent as an interpretation of supplied wording and section context, not as an unsupported fact about the author. |
| Give an example | Local passage by default | Label a model-created or general-knowledge example as illustrative, not source text. |
| Follow-up connection | Same scope selected for the follow-up, plus bounded same-episode dialogue | Preserve the original anchor and distinguish a supported connection from background interpretation. |
| Counterargument | Local passage by default | Separate the document's argument from a reasoned or background counterargument. |

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
original anchored paragraph as its reading position, and receives bounded recent dialogue
as additional context.

---

## **7\. Continue reading**

After one or more answers, the user presses:

**▶ Continue Reading**

The document resumes from the original paragraph where they stopped. Continuing ends
the active conversational episode; a later Ask begins a new one at the then-current
paragraph. Exact sentence-level semantic resume is not required yet.

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

Generate a short section synopsis lazily only when a local or limited book-wide question
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

The reading session only needs to remember:

{  
  "document\_id": "doc\_1",  
  "chapter\_index": 3,  
  "paragraph\_index": 12  
}  

While reading is paused, an active conversational episode additionally has one anchored
paragraph and an ordered set of textual question-and-answer interactions. The episode
ends when the user continues reading. Recent turns are selected from that episode only
as bounded temporary reasoning context.
---

# **Prompt Structure**

A typical request to the reasoning model should look like:

You are an expert reading companion.

Your job is to help the user deeply understand the document they are reading.

DOCUMENT:  
{title}  
{author}

DOCUMENT ORIENTATION:
{title, author if available, document type, bounded ordered document map}

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

RECENT DIALOGUE:
{bounded\_recent\_question\_and\_answer\_turns\_from\_this\_episode}

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
\- for a book-wide question, state that full-document retrieval is unavailable and do not
  present a best-effort interpretation as a search result;
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
conversation  
textual question-and-answer interactions
---

# **Explicitly Not Building Yet**

V0 does **not** include:

* autonomous agents;  
* multi-agent systems;  
* embeddings;  
* vector databases;  
* full-document RAG;  
* long-term conversation or learner memory;
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
12. receive and hear a follow-up answer that uses the original anchored passage and recent dialogue;
13. press **Continue**;
14. keep listening from the original anchored paragraph.

At that point, stop building features and use the product on a real difficult book.

The central MVP principle is:

> **Give the model enough context to understand the text deeply, but do not build retrieval infrastructure until real usage proves that we need it.**
