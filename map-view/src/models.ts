import { Point } from "ol/geom";

export interface Layer {
  identifier: string;
  name: string;
  app_name?: string;
}

export interface LayerConfig {
  name: string;
  layers: Layer[];
  sourceUrl: string;
}

export interface MapConfig {
  basemapConfig: LayerConfig;
  overlayConfig: LayerConfig;
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
}

export interface Feature {
  id_: string;
  geometry: object;
  geometry_name: string;
  type: string;
  app_name?: string;
  getProperties(): FeatureProperties;
}
