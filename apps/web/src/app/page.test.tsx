import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "./page";

describe("HomePage", () => {
  it("renders the stable V0 application shell", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: "Stay with difficult ideas." }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("The V0 application foundation is ready."),
    ).toBeInTheDocument();
  });
});
