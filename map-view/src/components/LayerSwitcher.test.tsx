import { fireEvent, render } from "@testing-library/react";
import React from "react";
import { mockMapConfig } from "../api/__mocks__/mock-data";
import { OverlayVisibility } from "../models";
import LayerSwitcher from "./LayerSwitcher";

vi.mock("../common/Map");

const renderLayerSwitcher = (
  visibleOverlays: OverlayVisibility = {},
  onOverlayVisibilityChange: (layerIdentifier: string, visible: boolean) => void = () => {},
) =>
  render(
    <LayerSwitcher
      mapConfig={mockMapConfig}
      onClose={() => {}}
      visibleOverlays={visibleOverlays}
      onOverlayVisibilityChange={onOverlayVisibilityChange}
      iconScale={0.125}
      iconType="png"
      iconSize={128}
      realPlanDistanceThreshold={0}
      onIconScaleChange={() => {}}
      onIconTypeChange={() => {}}
      onIconSizeChange={() => {}}
      onResetIconSettings={() => {}}
      onRealPlanDistanceThresholdChange={() => {}}
    />,
  );

test("renders basemaps and overlays", () => {
  const { getByText } = renderLayerSwitcher();
  const basemaps = getByText(/Basemaps/i);
  expect(basemaps).toBeInTheDocument();
  const overlays = getByText(/Overlays/i);
  expect(overlays).toBeInTheDocument();
});

test("overlay checkboxes follow the visibleOverlays prop", () => {
  const { getByLabelText } = renderLayerSwitcher({ "overlay-1": false, "overlay-2": true });
  expect(getByLabelText("Overlay 1")).not.toBeChecked();
  expect(getByLabelText("Overlay 2")).toBeChecked();
});

test("toggling an overlay reports the change to the parent", () => {
  const onOverlayVisibilityChange = vi.fn();
  const { getByLabelText } = renderLayerSwitcher({ "overlay-1": false, "overlay-2": false }, onOverlayVisibilityChange);
  fireEvent.click(getByLabelText("Overlay 1"));
  expect(onOverlayVisibilityChange).toHaveBeenCalledWith("overlay-1", true);
});
