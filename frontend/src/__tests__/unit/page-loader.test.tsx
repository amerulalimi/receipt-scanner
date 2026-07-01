import { render, screen } from "@testing-library/react";

import { PageLoader, PageSkeleton } from "@/components/ui/page-loader";

describe("PageLoader", () => {
  it("renders spinner", () => {
    render(<PageLoader />);
    expect(screen.getByRole("status", { name: "Memuatkan" })).toBeInTheDocument();
    expect(screen.getByText("Memuatkan...")).toBeInTheDocument();
  });

  it("Skeleton renders placeholder elements", () => {
    const { container } = render(<PageSkeleton />);
    expect(container.querySelectorAll("[data-slot='skeleton']").length).toBeGreaterThan(
      0,
    );
  });
});
