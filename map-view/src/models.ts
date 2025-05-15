import { Point } from "ol/geom";

export interface Layer {
  identifier: string;
  name: string;
  app_name?: string;
  filter_fields?: string[];
  use_traffic_sign_icons: boolean;
  clustered: boolean;
}

export interface LayerConfig {
  name: string;
  layers: Layer[];
  sourceUrl: string;
}

export interface OverviewConfig {
  imageUrl: string;
  imageExtent: number[];
}

export interface MapConfig {
  basemapConfig: LayerConfig;
  overlayConfig: LayerConfig;
  overviewConfig: OverviewConfig;
  traffic_sign_icons_url: string;
  featureTypeEditNameMapping: Record<string, string>;
  icon_scale: number;
  icon_type: string;
}

export interface FeatureProperties {
  id: string;
  geometry: Point;
  txt: string;
  direction: string;
  value: number;
  device_type_code: string;
  device_type_description: string;
  device_plan_id: string;
  mount_type_description_fi: string;
  content_s: Object;
  additional_information: string;
}

export interface Feature {
  id_: string;
  geometry: object;
  geometry_name: string;
  type: string;
  app_name?: string;
  getProperties(): FeatureProperties;
}
