import { Point } from "ol/geom";

interface ExtraFeatureInfo {
  title: string;
  order: number;
}

export interface Layer {
  identifier: string;
  name: string;
  app_name?: string;
  filter_fields?: string[];
  use_traffic_sign_icons: boolean;
  clustered: boolean;
  extra_feature_info: Record<string, ExtraFeatureInfo>;
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
  address_search_base_url: string;
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
  device_type_icon: string;
  device_type_description: string;
  device_plan_id: string;
  mount_type_description_fi: string;
  content_s: object;
  content_s_rows: Record<string, string>[];
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
