import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import HomePage from "./page";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("HomePage", () => {
  it("uploads only through the same-origin API and shows the ready state", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "doc-1", status: "processing" }), { status: 202 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ id: "doc-1", status: "ready", title: "The Constitution", failure_message: null }),
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    render(<HomePage />);

    const file = new File(["%PDF-1.7"], "paper.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Text-based PDF"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Prepare document" }));

    expect(await screen.findByText("The Constitution is ready to inspect.")).toBeInTheDocument();
    expect(fetchMock.mock.calls[0][0]).toBe("/api/documents");
    expect(fetchMock.mock.calls[0][1]?.body).toBeInstanceOf(FormData);
    expect(fetchMock.mock.calls[1][0]).toBe("/api/documents/doc-1");
  });

  it("shows a clear failure returned by the API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: "Upload a PDF file." }), { status: 415 })));
    render(<HomePage />);

    const file = new File(["not a pdf"], "notes.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText("Text-based PDF"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Prepare document" }));

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Upload a PDF file."));
  });

  it("clears stale status on a new file and pages through prepared source", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "doc-1", status: "processing" }), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "doc-1", status: "ready", title: "Paper", failure_message: null })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ document_map: [{ title: "Opening" }], sections: [{ id: "section-1", order: 1, title: "Opening", boundary_source: "outline", start_page: 1, end_page: 1 }], paragraphs: [{ id: "paragraph-1", section_id: "section-1", order: 1, text: "First paragraph.", start_page: 1, end_page: 1 }], offset: 0, limit: 100, total_paragraphs: 101 })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ document_map: [{ title: "Opening" }], sections: [{ id: "section-1", order: 1, title: "Opening", boundary_source: "outline", start_page: 1, end_page: 1 }], paragraphs: [{ id: "paragraph-101", section_id: "section-1", order: 101, text: "Last paragraph.", start_page: 2, end_page: 2 }], offset: 100, limit: 100, total_paragraphs: 101 })));
    vi.stubGlobal("fetch", fetchMock);
    render(<HomePage />);
    const file = new File(["%PDF-1.7"], "paper.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Text-based PDF"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Prepare document" }));
    await screen.findByText("Paper is ready to inspect.");
    fireEvent.click(screen.getByRole("button", { name: "Review prepared source" }));
    expect(await screen.findByText("First paragraph.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Last paragraph.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Text-based PDF"), { target: { files: [file] } });
    expect(screen.getByRole("status")).toHaveTextContent("Choose a text-based PDF");
  });

  it("does not let an earlier poll overwrite the state after another file is selected", async () => {
    let resolveStatus: ((response: Response) => void) | undefined;
    const status = new Promise<Response>((resolve) => { resolveStatus = resolve; });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "old-document", status: "processing" }), { status: 202 }))
      .mockReturnValueOnce(status);
    vi.stubGlobal("fetch", fetchMock);
    render(<HomePage />);
    const input = screen.getByLabelText("Text-based PDF");
    const first = new File(["%PDF-1.7"], "first.pdf", { type: "application/pdf" });
    const second = new File(["%PDF-1.7"], "second.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [first] } });
    fireEvent.click(screen.getByRole("button", { name: "Prepare document" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    fireEvent.change(input, { target: { files: [second] } });
    resolveStatus?.(new Response(JSON.stringify({ id: "old-document", status: "ready", title: "Old document", failure_message: null })));

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Choose a text-based PDF"));
    expect(screen.queryByText("Old document is ready to inspect.")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Review prepared source" })).not.toBeInTheDocument();
  });

  it("does not restore an earlier prepared-source review after another file is selected", async () => {
    let resolveReview: ((response: Response) => void) | undefined;
    const reviewResponse = new Promise<Response>((resolve) => { resolveReview = resolve; });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "old-document", status: "processing" }), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "old-document", status: "ready", title: "Old document", failure_message: null })))
      .mockReturnValueOnce(reviewResponse);
    vi.stubGlobal("fetch", fetchMock);
    render(<HomePage />);
    const input = screen.getByLabelText("Text-based PDF");
    const first = new File(["%PDF-1.7"], "first.pdf", { type: "application/pdf" });
    const second = new File(["%PDF-1.7"], "second.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [first] } });
    fireEvent.click(screen.getByRole("button", { name: "Prepare document" }));
    await screen.findByText("Old document is ready to inspect.");
    fireEvent.click(screen.getByRole("button", { name: "Review prepared source" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    fireEvent.change(input, { target: { files: [second] } });
    await act(async () => {
      resolveReview?.(new Response(JSON.stringify({
        document_map: [{ title: "Old section" }],
        sections: [],
        paragraphs: [],
        offset: 0,
        limit: 100,
        total_paragraphs: 0,
      })));
      await reviewResponse;
    });

    expect(screen.getByRole("status")).toHaveTextContent("Choose a text-based PDF");
    expect(screen.queryByRole("region", { name: "Prepared source" })).not.toBeInTheDocument();
  });
});
