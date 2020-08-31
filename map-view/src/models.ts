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
