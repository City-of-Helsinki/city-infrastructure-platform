import { Feature as OlFeature } from "ol";
import { Point } from "ol/geom";
import ImageState from "ol/ImageState";
import OLEvent from "ol/events/Event";
import { Icon, Text } from "ol/style";
import { afterEach, vi } from "vitest";
import { Feature } from "../models";
import { mockMapConfig } from "../api/__mocks__/mock-data";
import { getHighlightStyle, getSinglePointStyle } from "./MapUtils";

afterEach(() => vi.restoreAllMocks());

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

test("offsets the question mark by half the estimated sign height after its width loads", () => {
  let imageChangeListener: ((event: OLEvent) => void) | undefined;
  const imageState = vi.spyOn(Icon.prototype, "getImageState").mockReturnValue(ImageState.IDLE);
  vi.spyOn(Icon.prototype, "getWidth").mockReturnValue(140);
  vi.spyOn(Icon.prototype, "listenImageChange").mockImplementation((listener) => {
    imageChangeListener = listener;
  });
  const unlistenImageChange = vi.spyOn(Icon.prototype, "unlistenImageChange").mockImplementation(() => {});
  const feature = new OlFeature({
    geometry: new Point([0, 0]),
    device_type_code: "device",
    device_type_icon: "",
    real_count: 0,
  });

  const styles = getSinglePointStyle(feature, true, "/icons/", 0.5, "svg");
  const text = styles[1].getText() as Text;

  expect(text.getOffsetY()).toBe(0);
  expect(text.getOffsetX()).toBe(0);
  expect(text.getTextBaseline()).toBe("middle");

  imageState.mockReturnValue(ImageState.LOADED);
  imageChangeListener?.(new OLEvent("change"));

  expect(text.getOffsetY()).toBe(-30);
  expect(unlistenImageChange).toHaveBeenCalledWith(imageChangeListener);
});
