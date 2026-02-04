import { Point } from "ol/geom";

export type IconSize = 32 | 64 | 128 | 256;

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
  icon_size: number;
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

/**
 * Builds a traffic sign icons URL with the specified icon type and size.
 * Replaces /svg/ or /png/{size}/ path segments in the base URL.
 *
 * @param baseUrl - The base traffic_sign_icons_url from MapConfig
 * @param iconType - Either 'svg' or 'png'
 * @param iconSize - The PNG icon size (32, 64, 128, 256)
 * @returns Modified URL with correct icon type and size path
 */
export function buildIconUrl(baseUrl: string, iconType: string, iconSize: IconSize): string {
  // Replace /svg/ or /png/{any number}/ with the appropriate path
  if (iconType === "png") {
    // Replace /svg/ with /png/{size}/ or replace /png/{oldSize}/ with /png/{newSize}/
    return baseUrl.replace(/\/svg\//, `/png/${iconSize}/`).replace(/\/png\/\d+\//, `/png/${iconSize}/`);
  } else {
    // Replace /png/{size}/ with /svg/
    return baseUrl.replace(/\/png\/\d+\//, `/svg/`);
  }
}
