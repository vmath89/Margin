import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ApiHealthStatus from "./api-health-status";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ApiHealthStatus", () => {
  it("checks the local API through the same-origin health path", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ApiHealthStatus />);

    expect(await screen.findByText("The local API is connected.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/health", expect.anything());
  });

  it("shows a clear local-development error when the API is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Network error")));

    render(<ApiHealthStatus />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The local API is unavailable. Start FastAPI at http://127.0.0.1:8000 and refresh.",
    );
  });
});
