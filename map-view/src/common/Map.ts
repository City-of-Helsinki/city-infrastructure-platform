import OLMap from "ol/Map";
import Projection from "ol/proj/Projection";
import Collection from "ol/Collection";
import Control from "ol/control/Control";
import MousePosition from "ol/control/MousePosition";
import { createStringXY } from "ol/coordinate";
import ScaleLine from "ol/control/ScaleLine";
import { defaults as defaultControls } from "ol/control";
import View from "ol/View";
import { LayerConfig, MapConfig } from "../models";
import ImageLayer from "ol/layer/Image";
import LayerGroup from "ol/layer/Group";
import ImageWMS from "ol/source/ImageWMS";

class Map {
  private projectionCode = "EPSG:3879";
  private map: OLMap;

  initialize(target: string, mapConfig: MapConfig) {
    const { basemaps, overlays } = mapConfig;
    const basemapLayerGroup = this.createBasemapLayerGroup(basemaps);
    const overlayLayerGroup = this.createOverlayLayerGroup(overlays);
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
  }

  private createBasemapLayerGroup(layerConfig: LayerConfig) {
    const { layers, sourceUrl } = layerConfig;
    const basemapLayers = layers.map(({ identifier }, index) => {
      const wmsSource = new ImageWMS({
        url: sourceUrl,
        params: { LAYERS: identifier },
      });
      return new ImageLayer({
        source: wmsSource,
        visible: index === 0,
      });
    });

    return new LayerGroup({
      layers: basemapLayers,
    });
  }

  private createOverlayLayerGroup(layerConfig: LayerConfig) {
    const { layers, sourceUrl } = layerConfig;
    const overlayLayers = layers.map(({ identifier }) => {
      const wmsSource = new ImageWMS({
        url: sourceUrl,
        params: { LAYERS: identifier },
      });
      return new ImageLayer({
        source: wmsSource,
        visible: true,
      });
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
