import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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

    const file = new File(["%PDF-1.7"], "constitution.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Selected PDF"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Prepare document" }));

    expect(await screen.findByText("The Constitution is ready to read.")).toBeInTheDocument();
    expect(fetchMock.mock.calls[0][0]).toBe("/api/documents");
    expect(fetchMock.mock.calls[0][1]?.body).toBeInstanceOf(FormData);
    expect(fetchMock.mock.calls[1][0]).toBe("/api/documents/doc-1");
  });

  it("shows a clear failure returned by the API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: "Upload the supported PDF file." }), { status: 415 })));
    render(<HomePage />);

    const file = new File(["not a pdf"], "notes.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText("Selected PDF"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Prepare document" }));

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Upload the supported PDF file."));
  });
});
