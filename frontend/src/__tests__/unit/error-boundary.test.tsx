import { render, screen } from "@testing-library/react";

import { ErrorBoundary } from "@/components/error-boundary";

function ThrowingChild(): never {
  throw new Error("Test error");
}

describe("ErrorBoundary", () => {
  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <p>Content OK</p>
      </ErrorBoundary>,
    );
    expect(screen.getByText("Content OK")).toBeInTheDocument();
  });

  it("renders fallback UI on error", () => {
    jest.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );

    expect(
      screen.getByText("Ralat berlaku. Sila muat semula halaman."),
    ).toBeInTheDocument();
  });

  it("reload button calls window.location.reload", () => {
    jest.spyOn(console, "error").mockImplementation(() => {});
    const reload = jest.fn();
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { reload },
    });

    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );

    screen.getByRole("button", { name: "Muat Semula" }).click();
    expect(reload).toHaveBeenCalled();
  });
});
