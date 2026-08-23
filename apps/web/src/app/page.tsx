"use client";

import { FormEvent, useState } from "react";

type UploadState = "idle" | "submitting" | "processing" | "ready" | "failed";
type DocumentResponse = { id: string; status: "processing" | "ready" | "failed"; title: string | null; failure_message: string | null };
type ErrorResponse = { message?: string };

export default function HomePage() {
  const [state, setState] = useState<UploadState>("idle");
  const [message, setMessage] = useState("Choose the selected PDF to prepare it for reading.");

  async function pollDocument(id: string) {
    for (;;) {
      const response = await fetch(`/api/documents/${id}`);
      if (!response.ok) throw new Error("We could not check the document preparation status.");
      const document = (await response.json()) as DocumentResponse;
      if (document.status === "ready") {
        setState("ready");
        setMessage(`${document.title ?? "Your document"} is ready to read.`);
        return;
      }
      if (document.status === "failed") throw new Error(document.failure_message ?? "The PDF could not be prepared.");
      await new Promise((resolve) => window.setTimeout(resolve, 400));
    }
  }

  async function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("document") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || file.size === 0) {
      setState("failed");
      setMessage("Choose a PDF file to upload.");
      return;
    }
    setState("submitting");
    setMessage("Uploading your PDF…");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch("/api/documents", { method: "POST", body: formData });
      if (!response.ok) {
        const error = (await response.json()) as ErrorResponse;
        throw new Error(error.message ?? "The PDF could not be uploaded.");
      }
      const document = (await response.json()) as DocumentResponse;
      setState("processing");
      setMessage("Preparing the document…");
      await pollDocument(document.id);
    } catch (error) {
      setState("failed");
      setMessage(error instanceof Error ? error.message : "The PDF could not be uploaded.");
    }
  }

  return <main className="shell"><p className="eyebrow">Margin</p><h1>Stay with difficult ideas.</h1><p className="lede">Upload the selected PDF to prepare it for reading.</p><form className="upload-form" onSubmit={submitUpload}><label htmlFor="document">Selected PDF</label><input id="document" name="document" type="file" accept="application/pdf,.pdf"/><button className="retry" disabled={state === "submitting" || state === "processing"}>{state === "submitting" ? "Uploading…" : "Prepare document"}</button></form><p className="status" role="status">{message}</p></main>;
}
