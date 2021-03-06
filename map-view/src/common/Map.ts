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
import Style from "ol/style/Style";
import Icon from "ol/style/Icon";
import ArrowIcon from "../assets/arrow.svg";

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
   * A layer to draw temporary vector features on the map
   */
  private vectorLayer: VectorLayer;
  /**
   * Available basemap layers
   */
  private basemapLayers: { [identifier: string]: ImageLayer } = {};
  /**
   * Available overlay layers
   */
  private overlayLayers: { [identifier: string]: ImageLayer } = {};
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
    this.vectorLayer = this.createVectorLayer();
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
      layers: [basemapLayerGroup, overlayLayerGroup, this.vectorLayer],
      controls: this.getControls(),
      view,
    });

    this.map.on("singleclick", (event) => {
      const viewResolution = view.getResolution();
      const visibleLayers = Object.values(this.overlayLayers).filter((layer) => layer.getVisible());
      if (visibleLayers.length > 0) {
        const layerNames = visibleLayers.map((layer) => (layer.getSource() as ImageWMS).getParams().LAYERS);
        const url = (visibleLayers[0].getSource() as ImageWMS).getFeatureInfoUrl(
          event.coordinate,
          viewResolution as number,
          projection,
          {
            INFO_FORMAT: "application/json",
            LAYERS: layerNames.join(","),
            QUERY_LAYERS: layerNames.join(","),
            FEATURE_COUNT: 10,
          }
        );

        if (url) {
          fetch(url)
            .then((response) => response.text())
            .then((responseText) => {
              const data = JSON.parse(responseText);
              this.featureInfoCallback(data["features"]);
            });
        }
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

  /**
   * Show a direction arrow on the feature
   *
   * @param feature Target feature on which a direction arrow will be shown
   */
  showDirectionArrow(feature: Feature) {
    this.vectorLayer.getSource().clear();
    const olFeature = this.geojsonFormat.readFeature(feature);
    const rotation = (olFeature.get("direction") * Math.PI) / 180;
    const arrowStyle = new Style({
      image: new Icon({
        src: ArrowIcon,
        scale: 2.0,
        rotation,
      }),
    });
    olFeature.setStyle(arrowStyle);
    this.vectorLayer.getSource().addFeature(olFeature);
  }

  private createVectorLayer() {
    const vectorSource = new VectorSource();
    return new VectorLayer({ source: vectorSource });
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
    const overlayLayers = layers.map(({ identifier }) => {
      const wmsSource = new ImageWMS({
        url: sourceUrl,
        params: { LAYERS: identifier },
      });
      const layer = new ImageLayer({
        source: wmsSource,
        visible: false,
      });
      this.overlayLayers[identifier] = layer;
      return layer;
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
