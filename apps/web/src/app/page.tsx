"use client";

import { FormEvent, useRef, useState } from "react";

type UploadState = "idle" | "submitting" | "processing" | "ready" | "failed";
type DocumentResponse = { id: string; status: "processing" | "ready" | "failed"; title: string | null; failure_message: string | null };
type Review = { document_map: { title: string }[]; sections: { id: string; order: number; title: string; boundary_source: string; start_page: number | null; end_page: number | null }[]; paragraphs: { id: string; section_id: string; order: number; text: string; start_page: number | null; end_page: number | null }[]; offset: number; limit: number; total_paragraphs: number };
type ErrorResponse = { message?: string };

export default function HomePage() {
  const [state, setState] = useState<UploadState>("idle");
  const [message, setMessage] = useState("Choose a text-based PDF to prepare it for reading.");
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [review, setReview] = useState<Review | null>(null);
  const preparationGeneration = useRef(0);

  async function pollDocument(id: string, generation: number) {
    for (;;) {
      const response = await fetch(`/api/documents/${id}`);
      if (generation !== preparationGeneration.current) return;
      if (!response.ok) throw new Error("We could not check the document preparation status.");
      const document = (await response.json()) as DocumentResponse;
      if (document.status === "ready") { setState("ready"); setDocumentId(id); setMessage(`${document.title ?? "Your document"} is ready to inspect.`); return; }
      if (document.status === "failed") throw new Error(document.failure_message ?? "The PDF could not be prepared.");
      await new Promise((resolve) => window.setTimeout(resolve, 400));
      if (generation !== preparationGeneration.current) return;
    }
  }
  function chooseFile() {
    preparationGeneration.current += 1;
    setState("idle"); setDocumentId(null); setReview(null); setMessage("Choose a text-based PDF to prepare it for reading.");
  }
  async function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("document") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || file.size === 0) { setState("failed"); setMessage("Choose a PDF file to upload."); return; }
    const generation = preparationGeneration.current + 1;
    preparationGeneration.current = generation;
    setState("submitting"); setReview(null); setDocumentId(null); setMessage("Uploading your PDF…");
    try {
      const formData = new FormData(); formData.append("file", file);
      const response = await fetch("/api/documents", { method: "POST", body: formData });
      if (!response.ok) { const error = (await response.json()) as ErrorResponse; throw new Error(error.message ?? "The PDF could not be uploaded."); }
      const document = (await response.json()) as DocumentResponse;
      if (generation !== preparationGeneration.current) return;
      setState("processing"); setMessage("Preparing the document…"); await pollDocument(document.id, generation);
    } catch (error) {
      if (generation === preparationGeneration.current) {
        setState("failed"); setMessage(error instanceof Error ? error.message : "The PDF could not be uploaded.");
      }
    }
  }
  async function loadReview(offset = 0) {
    if (!documentId) return;
    const generation = preparationGeneration.current;
    const response = await fetch(`/api/documents/${documentId}/review?offset=${offset}&limit=100`);
    if (generation !== preparationGeneration.current) return;
    if (!response.ok) { const error = (await response.json()) as ErrorResponse; setMessage(error.message ?? "The prepared source could not be loaded."); return; }
    const preparedSource = (await response.json()) as Review;
    if (generation !== preparationGeneration.current) return;
    setReview(preparedSource);
  }
  return <main className="shell"><p className="eyebrow">Margin</p><h1>Stay with difficult ideas.</h1><p className="lede">Upload a text-based PDF to prepare it for reading. Scans and password-protected PDFs are not supported.</p><form className="upload-form" onSubmit={submitUpload}><label htmlFor="document">Text-based PDF</label><input id="document" name="document" type="file" accept="application/pdf,.pdf" onChange={chooseFile}/><button className="retry" disabled={state === "submitting" || state === "processing"}>{state === "submitting" ? "Uploading…" : "Prepare document"}</button></form><p className="status" role="status">{message}</p>{state === "ready" && <button className="review-button" onClick={() => loadReview()}>Review prepared source</button>}{review && <section className="review" aria-label="Prepared source"><h2>Prepared source</h2><h3>Document map</h3><ol>{review.document_map.map((entry, index) => <li key={index}>{entry.title}</li>)}</ol><h3>Sections</h3><ol>{review.sections.map((section) => <li key={section.id}>{section.title}{section.start_page ? ` (pages ${section.start_page}${section.end_page && section.end_page !== section.start_page ? `–${section.end_page}` : ""})` : ""}</li>)}</ol><h3>Paragraphs</h3>{review.paragraphs.map((paragraph) => <article key={paragraph.id}><small>Paragraph {paragraph.order}{paragraph.start_page ? ` · page ${paragraph.start_page}${paragraph.end_page && paragraph.end_page !== paragraph.start_page ? `–${paragraph.end_page}` : ""}` : ""}</small><p>{paragraph.text}</p></article>)}<div className="review-controls">{review.offset > 0 && <button onClick={() => loadReview(Math.max(0, review.offset - review.limit))}>Previous</button>}{review.offset + review.paragraphs.length < review.total_paragraphs && <button onClick={() => loadReview(review.offset + review.limit)}>Next</button>}</div></section>}</main>;
}
