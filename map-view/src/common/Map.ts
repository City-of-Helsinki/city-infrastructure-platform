import OLMap from "ol/Map";
import Projection from "ol/proj/Projection";
import Collection from "ol/Collection";
import Control from "ol/control/Control";
import MousePosition from "ol/control/MousePosition";
import { createStringXY } from "ol/coordinate";
import ScaleLine from "ol/control/ScaleLine";
import { defaults as defaultControls } from "ol/control";
import View from "ol/View";
import { Feature, LayerConfig, MapConfig } from "../models";
import ImageLayer from "ol/layer/Image";
import LayerGroup from "ol/layer/Group";
import ImageWMS from "ol/source/ImageWMS";
import GeoJson from "ol/format/GeoJSON";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import { Circle, Fill, Stroke, Style } from "ol/style";

class Map {
  /**
   * Projection code used by the map
   */
  private projectionCode = "EPSG:3879";
  /**
   * Openlayers Map instance
   */
  private map: OLMap;
  /**
   * Current visible basemap
   */
  private visibleBasemap: string;
  /**
   * GeoJSON parser
   */
  private geojsonFormat = new GeoJson();
  /**
   * Available basemap layers
   */
  private basemapLayers: { [identifier: string]: ImageLayer } = {};
  /**
   * Available overlay layers
   */
  private overlayLayers: { [identifier: string]: VectorLayer } = {};
  /**
   * Callback function to process features returned from GetFeatureInfo requests
   *
   * @param features Features returned from GetFeatureInfo requests
   */
  private featureInfoCallback: (features: Feature[]) => void = (features: Feature[]) => {};

  /**
   * Initialize map on target element
   *
   * @param target The id of the element on which the map will be mounted
   * @param mapConfig Configurations for the map
   */
  initialize(target: string, mapConfig: MapConfig) {
    const { basemapConfig, overlayConfig } = mapConfig;
    const basemapLayerGroup = this.createBasemapLayerGroup(basemapConfig);
    const overlayLayerGroup = this.createOverlayLayerGroup(overlayConfig);

    const helsinkiCoords = [25499052.02, 6675851.38];
    const resolutions = [256, 128, 64, 32, 16, 8, 4, 2, 1, 0.5, 0.25, 0.125, 0.0625];
    const projection = this.getProjection();
    const view = new View({
      projection,
      center: helsinkiCoords,
      zoom: 5,
      resolutions,
      extent: projection.getExtent(),
    });
    this.map = new OLMap({
      target: target,
      layers: [basemapLayerGroup, overlayLayerGroup],
      controls: this.getControls(),
      view,
    });

    this.map.on("singleclick", (event) => {
      const visibleLayers = Object.values(this.overlayLayers).filter((layer) => layer.getVisible());
      if (visibleLayers.length > 0) {
        // Combine the topmost feature from all visible layers into a single array
        Promise.all(visibleLayers.map((layer) => layer.getFeatures(event.pixel))).then((features) => {
          if (features.length) {
            // @ts-ignore
            const all_features = [].concat.apply([], features);
            this.featureInfoCallback(all_features);
          }
        });
      }
    });
  }

  registerFeatureInfoCallback(fn: (features: Feature[]) => void) {
    this.featureInfoCallback = fn;
  }

  setVisibleBasemap(basemap: string) {
    // there can be only one visible base
    this.basemapLayers[this.visibleBasemap].setVisible(false);
    this.visibleBasemap = basemap;
    this.basemapLayers[this.visibleBasemap].setVisible(true);
  }

  setOverlayVisible(overlay: string, visible: boolean) {
    this.overlayLayers[overlay].setVisible(visible);
  }

  private createBasemapLayerGroup(layerConfig: LayerConfig) {
    const { layers, sourceUrl } = layerConfig;
    const basemapLayers = layers.map(({ identifier }, index) => {
      const wmsSource = new ImageWMS({
        url: sourceUrl,
        params: { LAYERS: identifier },
      });
      const layer = new ImageLayer({
        source: wmsSource,
        visible: index === 0,
      });
      if (index === 0) {
        this.visibleBasemap = identifier;
      }
      this.basemapLayers[identifier] = layer;
      return layer;
    });

    return new LayerGroup({
      layers: basemapLayers,
    });
  }

  private createOverlayLayerGroup(layerConfig: LayerConfig) {
    const { layers, sourceUrl } = layerConfig;
    const vectorLayerStyle = new Style({
      image: new Circle({
        radius: 6,
        fill: new Fill({
          color: "#ff0000",
        }),
      }),
      stroke: new Stroke({
        color: "#ffcc33",
        width: 2,
      }),
    });

    // Fetch device layers
    const overlayLayers = layers.map(({ identifier }) => {
      const vectorSource = new VectorSource({
        format: this.geojsonFormat,
        url: sourceUrl + `?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&OUTPUTFORMAT=geojson&TYPENAMES=${identifier}`,
      });

      const vectorLayer = new VectorLayer({
        source: vectorSource,
        style: vectorLayerStyle,
        visible: false,
      });

      this.overlayLayers[identifier] = vectorLayer;
      return vectorLayer;
    });
    return new LayerGroup({
      layers: overlayLayers,
    });
  }

  private getProjection(): Projection {
    return new Projection({
      code: this.projectionCode,
      extent: [25440000, 6630000, 25571072, 6761072],
      units: "m",
      axisOrientation: "neu",
    });
  }

  private getControls(): Collection<Control> {
    const mousePosition = new MousePosition({
      coordinateFormat: createStringXY(0),
      projection: this.projectionCode,
      className: "mouse-position",
    });

    const scaleLine = new ScaleLine();

    return defaultControls().extend([mousePosition, scaleLine]);
  }
}

export default new Map();
