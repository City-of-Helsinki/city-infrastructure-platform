export interface Layer {
  identifier: string;
  name: string;
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
  txt: string;
  direction: string;
  value: number;
  device_type_code: string;
  device_type_description: string;
}

export interface Feature {
  geometry: object;
  geometry_name: string;
  id: string;
  properties: FeatureProperties;
  type: string;
}
