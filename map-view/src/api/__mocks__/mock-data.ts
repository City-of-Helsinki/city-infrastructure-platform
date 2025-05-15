import { MapConfig } from "../../models";

export const mockMapConfig: MapConfig = {
  basemapConfig: {
    name: "Basemaps",
    sourceUrl: "/basemaps",
    layers: [
      {
        identifier: "basemap-1",
        name: "Basemap 1",
        use_traffic_sign_icons: false,
        clustered: false,
      },
      {
        identifier: "basemap-2",
        name: "Basemap 2",
        use_traffic_sign_icons: false,
        clustered: false,
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
        use_traffic_sign_icons: false,
        clustered: false,
      },
      {
        identifier: "overlay-2",
        name: "Overlay 2",
        app_name: "city_furniture",
        use_traffic_sign_icons: false,
        clustered: false,
      },
    ],
  },
  overviewConfig: {
    imageExtent: [0, 0, 0, 0],
    imageUrl: "testurl",
  },
  traffic_sign_icons_url: "http://127.0.0.1:8000/static/traffic_control/svg/traffic_sign_icons/",
  featureTypeEditNameMapping: {},
  icon_scale: 0.1,
  icon_type: "svg",
};
