import { Icon } from "ol/style";
import { Feature } from "../models";
import { mockMapConfig } from "../api/__mocks__/mock-data";
import { getHighlightStyle } from "./MapUtils";

test.each([
  ["plan", { real_count: 1 }],
  ["real", {}],
])("renders selected %s device icons fully opaque", (_deviceType, deviceProperties) => {
  const feature: Feature = {
    id_: "overlay-1.device",
    geometry: {},
    geometry_name: "location",
    type: "Feature",
    getProperties: () =>
      ({
        device_type_code: "device",
        device_type_icon: "",
        ...deviceProperties,
      }) as ReturnType<Feature["getProperties"]>,
  };
  const mapConfig = {
    ...mockMapConfig,
    overlayConfig: {
      ...mockMapConfig.overlayConfig,
      layers: mockMapConfig.overlayConfig.layers.map((layer) => ({
        ...layer,
        use_traffic_sign_icons: true,
      })),
    },
  };

  const styles = getHighlightStyle(feature, mapConfig);
  const icon = styles[0].getImage() as Icon;

  expect(icon.getOpacity()).toBe(1);
});
