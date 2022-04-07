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
        app_name: "traffic_control",
      },
      {
        identifier: "overlay-2",
        name: "Overlay 2",
        app_name: "city_furniture",
      },
    ],
  },
  traffic_sign_icons_url: "http://127.0.0.1:8000/static/traffic_control/svg/traffic_sign_icons/",
};
