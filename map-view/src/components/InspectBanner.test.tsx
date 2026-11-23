import { fireEvent, render } from "@testing-library/react";
import React from "react";
import InspectBanner from "./InspectBanner";

describe("InspectBanner", () => {
  it("shows the inspected layer name with show layer and close buttons", () => {
    const onShowLayer = vi.fn();
    const onClose = vi.fn();
    const { getByText, getByRole } = render(
      <InspectBanner status="found" layerName="Overlay 1" onShowLayer={onShowLayer} onClose={onClose} />,
    );

    expect(getByText(/Inspecting a single feature/)).toBeInTheDocument();
    expect(getByText("Overlay 1")).toBeInTheDocument();

    fireEvent.click(getByRole("button", { name: "Show all features in this layer" }));
    expect(onShowLayer).toHaveBeenCalledTimes(1);

    fireEvent.click(getByRole("button", { name: "close" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("shows a not found message with only the close button", () => {
    const onClose = vi.fn();
    const { getByText, queryByRole, getByRole } = render(
      <InspectBanner status="notFound" layerName="Overlay 1" onShowLayer={() => {}} onClose={onClose} />,
    );

    expect(getByText(/could not be found/)).toBeInTheDocument();
    expect(queryByRole("button", { name: "Show all features in this layer" })).not.toBeInTheDocument();

    fireEvent.click(getByRole("button", { name: "close" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
