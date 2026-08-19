# **MVP RFC — AI Reading Companion v0**

## **Goal**

Build the **smallest web application** that proves this interaction:

> **Upload a document → listen → pause → ask a question → hear a detailed AI answer → continue.**

The purpose of V0 is to validate whether this experience is compelling before building agents, long-term memory, sophisticated RAG, mobile apps, or personalization.

---

## **Core User Flow**

### **1\. Upload a document**

Support **PDF only** initially.

The system:

1. extracts the text;  
2. identifies chapters or sections where possible;  
3. generates a short summary of the whole document;  
4. generates a short summary for each chapter.

These summaries are stored and reused during reading.

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

The system records the paragraph where the user stopped.

---

## **4\. Build the reasoning context**

The reasoning model should not receive only the current paragraph.

For most questions, it receives four layers of context:

DOCUMENT CONTEXT  
\- Title  
\- Author, if available  
\- Short document summary

CHAPTER CONTEXT  
\- Current chapter title  
\- Short chapter summary

LOCAL CONTEXT  
\- Previous 2–3 paragraphs  
\- Current paragraph  
\- Next paragraph

USER QUESTION

This gives the model enough context to understand both the immediate passage and the larger argument.

---

## **Context Strategy**

Keep the logic very simple in V0.

### **If the user asks about the current passage**

Examples:

> “What does this mean?”

> “Explain this paragraph.”

> “Why is he saying this?”

Send:

Document summary  
\+  
Chapter summary  
\+  
Previous 2–3 paragraphs  
\+  
Current paragraph  
\+  
Next paragraph  
\+  
User question  
---

### **If the user asks about the whole chapter**

Example:

> “What is the overall argument of this chapter?”

Send:

Document summary  
\+  
Full current chapter  
\+  
User question

Assuming the chapter fits comfortably within the model context window.

---

### **If the user asks about the whole book**

Example:

> “Where else in the book does he discuss this?”

Proper book-wide retrieval is **out of scope for V0**.

We can either tell the user this capability is limited or make a best-effort response from the document summary and current chapter.

Full-document RAG comes later.

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

For V0, the user does **not** need to interrupt the explanation with another question.

That can come later.

---

## **7\. Continue reading**

After the explanation, the user presses:

**▶ Continue Reading**

The document resumes from the paragraph where they stopped.

Exact sentence-level semantic resume is not required yet.

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
Generate document summary  
 ↓  
Generate chapter summaries  
 ↓  
Store

No embeddings are required.

No vector database is required.

No sophisticated retrieval system is required.

---

# **Suggested Data Structure**

A document can initially look like:

{  
  "title": "Letters from a Stoic",  
  "author": "Seneca",  
  "summary": "...",  
  "chapters": \[  
    {  
      "title": "Letter I",  
      "summary": "...",  
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
---

# **Prompt Structure**

A typical request to the reasoning model should look like:

You are an expert reading companion.

Your job is to help the user deeply understand the document they are reading.

DOCUMENT:  
{title}  
{author}

DOCUMENT CONTEXT:  
{document\_summary}

CURRENT CHAPTER:  
{chapter\_title}

CHAPTER CONTEXT:  
{chapter\_summary}

LOCAL CONTEXT:  
{previous\_paragraphs}

CURRENT PARAGRAPH:  
{current\_paragraph}

NEXT PARAGRAPH:  
{next\_paragraph}

USER QUESTION:  
{question}

Answer the user's question carefully and at the depth they request.

When explaining a passage:  
\- explain what the author is saying;  
\- explain why it matters in the context of the chapter;  
\- clarify difficult phrases where relevant;  
\- do not reduce a requested deep explanation to a short summary;  
\- distinguish clearly between what the text says and your interpretation;  
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

One strong reasoning model.

Keep the provider interchangeable.

### **Speech input**

Speech-to-text API.

### **Speech output**

High-quality TTS API.

### **Storage**

SQLite or Postgres is enough for V0.

Store:

documents  
chapters  
paragraphs  
summaries  
reading position  
conversation  
---

# **Explicitly Not Building Yet**

V0 does **not** include:

* autonomous agents;  
* multi-agent systems;  
* embeddings;  
* vector databases;  
* full-document RAG;  
* long-term learner memory;  
* personalized knowledge graphs;  
* external web research;  
* cross-book connections;  
* native mobile apps;  
* Kindle integration;  
* publisher integrations.

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

> **Listen → Pause → Ask → Understand → Continue**

feel substantially better than manually switching between a reader and ChatGPT?

---

# **Definition of Done**

V0 is done when I can:

1. upload a PDF;  
2. have the system identify its chapters;  
3. have it create a document summary and chapter summaries;  
4. press **Read**;  
5. listen to the document;  
6. pause on a paragraph;  
7. press **Ask**;  
8. say:  
   **“Explain this entire paragraph to me in detail.”**  
9. receive an explanation that understands both the paragraph and the chapter context;  
10. hear that explanation naturally;  
11. press **Continue**;  
12. keep listening.

At that point, stop building features and use the product on a real difficult book.

The central MVP principle is:

> **Give the model enough context to understand the text deeply, but do not build retrieval infrastructure until real usage proves that we need it.**

