import { act, fireEvent, render, waitFor, within } from "@testing-library/react";
import React from "react";
import MapConfigAPI from "./api/MapConfigAPI";
import { mockMapConfig } from "./api/__mocks__/mock-data";
import App from "./App";
import Map from "./common/Map";
import { Feature } from "./models";
import { Point } from "ol/geom";
import { MockedFunction } from "vitest";

vi.mock("./common/Map");
vi.mock("./api/MapConfigAPI");

const featureId = "fcdbbc6f-5903-4574-baa3-fef33a4b0621";
const inspectedFeature: Feature = {
  geometry: { type: "Point", coordinates: [1, 1] },
  geometry_name: "location",
  id_: `overlay-1.${featureId}`,
  app_name: "traffic_control",
  getProperties: () => ({
    id: featureId,
    geometry: new Point([25496040, 6676200]),
    direction: "",
    txt: "inspected feature text",
    value: 0,
    additional_information: "",
    content_s: {},
    content_s_rows: [],
    device_type_code: "",
    device_type_description: "",
    device_type_icon: "",
    device_plan_id: "",
    mount_type_description_fi: "",
  }),
  type: "Feature",
};

const mockInspectFeature = Map.inspectFeature as MockedFunction<typeof Map.inspectFeature>;

const setUrl = (url: string) => window.history.pushState(null, "", url);

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const addListener = MapConfigAPI.getMapConfig as MockedFunction<typeof MapConfigAPI.getMapConfig>;
    addListener.mockResolvedValue(mockMapConfig);
    mockInspectFeature.mockResolvedValue(inspectedFeature);
  });

  afterEach(() => {
    setUrl("/");
  });

  it("should initialize map with mock map config", async () => {
    const { findByText } = render(<App />);
    expect(await findByText("Layers")).toBeInTheDocument();
    expect(MapConfigAPI.getMapConfig).toHaveBeenCalled();
    expect(Map.initialize).toHaveBeenCalledWith("map", mockMapConfig);
  });

  it("does not enter inspect mode without inspect params", async () => {
    setUrl("/fi/map/?foo=bar");
    const { findByText, queryByText } = render(<App />);
    await findByText("Layers");
    await waitFor(() => expect(Map.registerOngoingFeatureFetchesCallback).toHaveBeenCalled());
    expect(Map.inspectFeature).not.toHaveBeenCalled();
    expect(queryByText(/Inspecting a single feature/)).not.toBeInTheDocument();
  });

  describe("with inspect params", () => {
    beforeEach(() => {
      setUrl(`/map/?foo=bar&inspect_layer=overlay-1&inspect_id=${featureId}`);
    });

    it("shows only the inspected feature with banner and FeatureInfo", async () => {
      const { findByText, getByText, getByLabelText } = render(<App />);

      expect(await findByText(/Inspecting a single feature/)).toBeInTheDocument();
      expect(Map.inspectFeature).toHaveBeenCalledWith("overlay-1", featureId);
      // FeatureInfo is open for the inspected feature
      expect(getByText(/inspected feature text/)).toBeInTheDocument();
      expect(getByLabelText("Overlay 1")).not.toBeChecked();
      expect(Map.setOverlayVisible).not.toHaveBeenCalled();
    });

    it("show all features in this layer turns on the inspected feature's layer and keeps FeatureInfo", async () => {
      const { findByRole, getByText, getByLabelText, queryByText } = render(<App />);

      fireEvent.click(await findByRole("button", { name: "Show all features in this layer" }));

      expect(Map.exitInspectMode).toHaveBeenCalledTimes(1);
      expect(Map.setOverlayVisible).toHaveBeenCalledWith("overlay-1", true);
      expect(getByLabelText("Overlay 1")).toBeChecked();
      expect(getByLabelText("Overlay 2")).not.toBeChecked();
      expect(queryByText(/Inspecting a single feature/)).not.toBeInTheDocument();
      expect(getByText(/inspected feature text/)).toBeInTheDocument();
      expect(Map.clearHighlightLayer).not.toHaveBeenCalled();
      expect(window.location.pathname).toBe("/map/");
      expect(window.location.search).toBe("?foo=bar");
    });

    it("close button exits inspect mode and leaves layers off", async () => {
      const { findByRole, getByLabelText, queryByText } = render(<App />);

      await findByRole("button", { name: "Show all features in this layer" });
      // The banner is a MUI Alert; FeatureInfo and LayerSwitcher have their own close buttons
      fireEvent.click(within(await findByRole("alert")).getByRole("button", { name: "close" }));

      expect(Map.exitInspectMode).toHaveBeenCalledTimes(1);
      expect(Map.setOverlayVisible).not.toHaveBeenCalled();
      expect(getByLabelText("Overlay 1")).not.toBeChecked();
      expect(queryByText(/Inspecting a single feature/)).not.toBeInTheDocument();
      expect(window.location.search).toBe("?foo=bar");
    });

    it("toggling a layer exits inspect mode", async () => {
      const { findByText, getByLabelText, queryByText } = render(<App />);

      await findByText(/Inspecting a single feature/);
      fireEvent.click(getByLabelText("Overlay 2"));

      expect(Map.exitInspectMode).toHaveBeenCalledTimes(1);
      expect(Map.setOverlayVisible).toHaveBeenCalledWith("overlay-2", true);
      expect(getByLabelText("Overlay 2")).toBeChecked();
      expect(queryByText(/Inspecting a single feature/)).not.toBeInTheDocument();
      expect(window.location.search).toBe("?foo=bar");
    });

    it("toggling a layer while the feature is loading exits inspect mode and ignores the loaded feature", async () => {
      let resolveInspect: (feature: Feature | null) => void = () => {};
      mockInspectFeature.mockReturnValue(new Promise((resolve) => (resolveInspect = resolve)));
      const { getByLabelText, findByLabelText, queryByText } = render(<App />);

      await waitFor(() => expect(Map.inspectFeature).toHaveBeenCalled());
      fireEvent.click(await findByLabelText("Overlay 2"));
      await act(async () => resolveInspect(inspectedFeature));

      expect(Map.exitInspectMode).toHaveBeenCalledTimes(1);
      expect(getByLabelText("Overlay 2")).toBeChecked();
      expect(window.location.search).toBe("?foo=bar");
      expect(queryByText(/Inspecting a single feature/)).not.toBeInTheDocument();
      expect(queryByText(/could not be found/)).not.toBeInTheDocument();
      expect(queryByText(/inspected feature text/)).not.toBeInTheDocument();
    });

    it("shows not found banner when the feature can't be loaded", async () => {
      mockInspectFeature.mockResolvedValue(null);
      const { findByText, queryByRole, queryByText } = render(<App />);

      expect(await findByText(/could not be found/)).toBeInTheDocument();
      expect(queryByRole("button", { name: "Show all features in this layer" })).not.toBeInTheDocument();
      expect(queryByText(/inspected feature text/)).not.toBeInTheDocument();
    });
  });

  it("treats an unknown inspect layer as not found", async () => {
    setUrl(`/map/?inspect_layer=unknown-layer&inspect_id=${featureId}`);
    const { findByText } = render(<App />);

    expect(await findByText(/could not be found/)).toBeInTheDocument();
    expect(Map.inspectFeature).not.toHaveBeenCalled();
  });

  it("treats an invalid inspect id as not found", async () => {
    setUrl("/map/?inspect_layer=overlay-1&inspect_id=not-a-uuid");
    const { findByText } = render(<App />);

    expect(await findByText(/could not be found/)).toBeInTheDocument();
    expect(Map.inspectFeature).not.toHaveBeenCalled();
  });
});
