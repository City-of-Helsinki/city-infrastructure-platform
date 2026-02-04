import { render } from "@testing-library/react";
import React from "react";
import { mockMapConfig } from "../api/__mocks__/mock-data";
import LayerSwitcher from "./LayerSwitcher";

vi.mock("../common/Map");

test("renders basemaps and overlays", () => {
  const { getByText } = render(
    <LayerSwitcher
      mapConfig={mockMapConfig}
      onClose={() => {}}
      onOverlayToggle={() => {}}
      iconScale={0.125}
      iconType="png"
      iconSize={128}
      onIconScaleChange={() => {}}
      onIconTypeChange={() => {}}
      onIconSizeChange={() => {}}
      onResetIconSettings={() => {}}
    />,
  );
  const basemaps = getByText(/Basemaps/i);
  expect(basemaps).toBeInTheDocument();
  const overlays = getByText(/Overlays/i);
  expect(overlays).toBeInTheDocument();
});
