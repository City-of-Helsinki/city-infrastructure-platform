import { Feature as OlFeature } from "ol";
import OLMap from "ol/Map";
import MapBrowserEvent from "ol/MapBrowserEvent";
import View from "ol/View";
import { LineString, Point } from "ol/geom";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import { getUnderlyingLayerFeatures } from "./functions";
import { Circle as CircleStyle } from "ol/style";
import { LayerConfig, MapConfig } from "../models";
import { mockMapConfig } from "../api/__mocks__/mock-data";
import Map, { ClusterColor } from "./Map";

const clusterCases = [
  { layerIdentifier: "device_real", featureProperties: { device_plan_id: "plan-1" }, expectedColor: ClusterColor.Real },
  { layerIdentifier: "device_plan", featureProperties: { real_count: 1 }, expectedColor: ClusterColor.Plan },
  { layerIdentifier: "device_plan", featureProperties: { real_count: 0 }, expectedColor: ClusterColor.PlanWithoutReal },
];

test.each(clusterCases)(
  "chooses $expectedColor for a cluster identified by $layerIdentifier feature data",
  ({ layerIdentifier, featureProperties, expectedColor }) => {
    const overlayConfig: LayerConfig = {
      ...mockMapConfig.overlayConfig,
      layers: ["device_real", "device_plan"].map((identifier) => ({
        ...mockMapConfig.overlayConfig.layers[0],
        identifier,
        clustered: true,
      })),
    };
    const mapConfig: MapConfig = { ...mockMapConfig, overlayConfig };

    Map["mapConfig"] = mapConfig;
    const layers = Map["createClusteredOverlayLayerGroup"](mapConfig).getLayersArray();
    const layerIndex = layerIdentifier === "device_real" ? 0 : 1;
    const styleFunction = (layers[layerIndex] as VectorLayer).getStyleFunction();
    const features = [0, 1].map(
      () =>
        new OlFeature({
          geometry: new Point([0, 0]),
          ...featureProperties,
        }),
    );
    const clusterFeature = new OlFeature({
      geometry: new Point([0, 0]),
      features,
    });

    const styles = styleFunction?.(clusterFeature, 1);
    const clusterStyle = Array.isArray(styles) ? styles[0] : styles;
    const image = clusterStyle?.getImage() as CircleStyle;

    expect(image.getFill()?.getColor()).toBe(expectedColor);
  },
);

describe("inspect mode", () => {
  const layerConfig = mockMapConfig.overlayConfig.layers[1]; // overlay-2, app_name city_furniture

  beforeEach(() => {
    Map["mapConfig"] = mockMapConfig;
    // A real OLMap needs ResizeObserver, which jsdom lacks; only the view is needed here
    const view = new View({ center: [0, 0], zoom: 0, resolutions: [256, 128, 64, 32, 16, 8, 4, 2, 1, 0.5, 0.25] });
    Map["map"] = { getView: () => view } as unknown as OLMap;
    Map["inspectedFeatureLayer"] = new VectorLayer({ source: new VectorSource() });
    Map["highLightedFeatureLayer"] = new VectorLayer({ source: new VectorSource() });
  });

  const createLineFeature = () => {
    const feature = new OlFeature({
      geometry: new LineString([
        [10, 20],
        [110, 70],
      ]),
    });
    feature.setId("overlay-2.3a1f0c52-8c2e-4f6d-9b7a-1e2d3c4b5a69");
    return feature;
  };

  it("shows, highlights and fits the view to the inspected feature", () => {
    const fitSpy = vi.spyOn(Map["map"].getView(), "fit");
    const olFeature = createLineFeature();

    const feature = Map["showInspectedFeature"](olFeature, layerConfig);

    expect(feature.app_name).toBe("city_furniture");
    expect(getUnderlyingLayerFeatures(Map["inspectedFeatureLayer"])).toEqual([olFeature]);
    expect(getUnderlyingLayerFeatures(Map["highLightedFeatureLayer"])).toHaveLength(1);
    expect(Map["inspectedFeatureLayer"].getStyleFunction()?.(olFeature, 1)).toBeTruthy();
    expect(fitSpy).toHaveBeenCalledWith([10, 20, 110, 70], expect.objectContaining({ maxZoom: 10 }));
  });

  it("exitInspectMode removes the inspected feature but keeps the highlight", () => {
    Map["showInspectedFeature"](createLineFeature(), layerConfig);

    Map.exitInspectMode();

    expect(getUnderlyingLayerFeatures(Map["inspectedFeatureLayer"])).toHaveLength(0);
    expect(getUnderlyingLayerFeatures(Map["highLightedFeatureLayer"])).toHaveLength(1);
  });

  it("exitInspectMode resolves a still loading inspectFeature with null", async () => {
    const result = Map.inspectFeature(layerConfig.identifier, "3a1f0c52-8c2e-4f6d-9b7a-1e2d3c4b5a69");

    Map.exitInspectMode();

    await expect(result).resolves.toBeNull();
    expect(getUnderlyingLayerFeatures(Map["inspectedFeatureLayer"])).toHaveLength(0);
  });

  it("inspectFeature resolves null for a layer not in overlay config", async () => {
    await expect(Map.inspectFeature("unknown-layer", "3a1f0c52-8c2e-4f6d-9b7a-1e2d3c4b5a69")).resolves.toBeNull();
  });

  describe("clicking the map", () => {
    const featureInfoCallback = vi.fn();
    // A coordinate on the line of createLineFeature
    const clickEvent = { coordinate: [60, 45], pixel: [0, 0] } as unknown as MapBrowserEvent;
    let clickHandler: (event: MapBrowserEvent) => void;

    beforeEach(() => {
      featureInfoCallback.mockClear();
      const view = Map["map"].getView();
      Map["map"] = {
        getView: () => view,
        on: (type: string, handler: (event: MapBrowserEvent) => void) => {
          if (type === "singleclick") clickHandler = handler;
        },
      } as unknown as OLMap;
      Map["clusteredOverlayLayers"] = {};
      Map["nonClusteredOverlayLayers"] = {};
      // Pixel hit detection needs a rendered map; the coordinate check finds the line feature
      vi.spyOn(Map["inspectedFeatureLayer"], "getFeatures").mockResolvedValue([]);
      Map["setupMapClickHandlers"](mockMapConfig.overlayConfig);
      Map.registerFeatureInfoCallback(featureInfoCallback);
    });

    afterEach(() => {
      Map["realPlanDistanceThreshold"] = 0;
    });

    it("opens FeatureInfo for the inspected feature, also when the distance threshold would hide it", async () => {
      const olFeature = createLineFeature();
      olFeature.set("real_count", 1); // A plan with a real, hidden by a threshold outside inspect mode
      Map["realPlanDistanceThreshold"] = 5;
      Map["showInspectedFeature"](olFeature, layerConfig);

      clickHandler(clickEvent);

      await vi.waitFor(() => expect(featureInfoCallback).toHaveBeenCalledWith([olFeature]));
    });

    it("does not open FeatureInfo after inspect mode is exited", async () => {
      Map["showInspectedFeature"](createLineFeature(), layerConfig);
      Map.exitInspectMode();

      clickHandler(clickEvent);

      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(featureInfoCallback).not.toHaveBeenCalled();
    });
  });
});
