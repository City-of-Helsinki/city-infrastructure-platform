import { MapConfig } from "../../models";

export const mockMapConfig: MapConfig = {
  basemapConfig: {
    name: "Basemaps",
    sourceUrl: "/basemaps",
    layers: [
      {
        identifier: "basemap-1",
        name: "Basemap 1",
      },
      {
        identifier: "basemap-2",
        name: "Basemap 2",
      },
    ],
  },
  overlayConfig: {
    name: "Overlays",
    sourceUrl: "/overlays",
    layers: [
      {
        identifier: "overlay-1",
        name: "Overlay 1",
      },
      {
        identifier: "overlay-2",
        name: "Overlay 2",
      },
    ],
  },
};
