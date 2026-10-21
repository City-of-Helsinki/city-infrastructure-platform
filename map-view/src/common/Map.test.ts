import { Feature as OlFeature } from "ol";
import { Point } from "ol/geom";
import VectorLayer from "ol/layer/Vector";
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
