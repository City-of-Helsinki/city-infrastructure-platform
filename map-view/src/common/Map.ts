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
import { Circle, Fill, Icon, Stroke, Style, Text } from "ol/style";
import { Pixel } from "ol/pixel";
import { Feature as OlFeature } from "ol";
import ImageSource from "ol/source/Image";
import { LineString } from "ol/geom";
import { buildWFSQuery, calculateDistance } from "./functions";
import { FeatureLike } from "ol/Feature";
import { Cluster } from "ol/source";

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
  private basemapLayers: { [identifier: string]: ImageLayer<ImageSource> } = {};
  /**
   * Available overlay layers
   */
  private overlayLayers: { [identifier: string]: VectorLayer<VectorSource> } = {};
  /**
   * A layer to draw temporary vector features on the map
   */
  private extraVectorLayer: VectorLayer<VectorSource>;

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
    const overlayLayerGroup = this.createOverlayLayerGroup(mapConfig);
    this.extraVectorLayer = Map.createExtraVectorLayer();

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
      layers: [basemapLayerGroup, overlayLayerGroup, this.extraVectorLayer],
      controls: this.getControls(),
      view,
    });

    async function getFeatureFromLayer(layer: VectorLayer<VectorSource>, pixel: Pixel) {
      // Save layer model's app name to feature so it can be used when making the Admin URL
      return await layer.getFeatures(pixel).then((features) => {
        if (features.length) {
          // @ts-ignore
          const feature: Feature = features[0];
          // Only get features that have ids (devices)
          if (feature["id_"]) {
            const featureType: string = feature["id_"].split(".")[0];
            const feature_layer = overlayConfig["layers"].find((l) => l.identifier === featureType);
            feature["app_name"] = feature_layer ? feature_layer["app_name"] : "traffic_control";
            return [feature];
          }
        }
        return features;
      });
    }

    this.map.on("singleclick", (event) => {
      const layers = { ...this.overlayLayers, extraVectorLayer: this.extraVectorLayer };
      const visibleLayers = Object.values(layers).filter((layer) => layer.getVisible());
      if (visibleLayers.length > 0) {
        // Combine the topmost feature from all visible layers into a single array
        Promise.all(visibleLayers.map((layer) => getFeatureFromLayer(layer, event.pixel))).then((features) => {
          // Extract features from a cluster
          // @ts-ignore
          if (features.length && features[0].length && features[0][0].get("features")) {
            // @ts-ignore
            features = features[0][0].get("features");
          }

          // @ts-ignore
          const all_features = [].concat.apply([], features);
          if (all_features.length > 0) {
            this.featureInfoCallback(all_features);
          }
        });
      }
    });
  }

  /**
   * Show a plan object of the selected real device on map
   *
   * @param feature Target feature of which the plan/real device will be shown
   * @param mapConfig
   */
  showPlanOfRealDevice(feature: Feature, mapConfig: MapConfig) {
    return new Promise((resolve) => {
      if (feature.getProperties().device_plan_id) {
        const { overlayConfig } = mapConfig;

        // Find selected Real device's Plan layer's config
        const featureType: string = feature["id_"].split(".")[0].replace("real", "plan");
        const feature_layer = overlayConfig["layers"].find((l) => l.identifier === featureType);

        if (feature_layer) {
          const vectorSource = new VectorSource({
            format: this.geojsonFormat,
            url:
              overlayConfig.sourceUrl +
              `?${buildWFSQuery(feature_layer.identifier, "id", feature.getProperties().device_plan_id)}`,
          });
          this.extraVectorLayer.setSource(vectorSource);

          // Add a line between the plan and real points
          vectorSource.on("featuresloadend", (featureEvent) => {
            const features = featureEvent.features;
            if (features) {
              const plan_location = features[0].getProperties().geometry.getFlatCoordinates();
              const real_location = feature.getProperties().geometry.getFlatCoordinates();
              const lineString = new LineString([plan_location, real_location]);
              const olFeature = new OlFeature({
                geometry: lineString,
                name: "Line",
              });
              this.extraVectorLayer.getSource()!.addFeature(olFeature);

              // Calculate distance between Real and Plan

              resolve(calculateDistance(real_location, plan_location));
            }
          });
        }
      } else {
        // If clicked feature belongs to extraVectorLayer, don't clear the layer
        const extraVectorLayerSource = this.extraVectorLayer.getSource();
        // @ts-ignore
        const extraFeatures = Object.values(extraVectorLayerSource!.getFeatures()).filter((f) => f.id_ === feature.id_);
        if (!extraFeatures.length) {
          extraVectorLayerSource!.clear();
        }
      }
    });
  }

  private static createExtraVectorLayer() {
    const extraVectorLayer = new VectorSource({});
    return new VectorLayer({
      source: extraVectorLayer,
      // Point style
      style: new Style({
        image: new Circle({
          radius: 6,
          fill: new Fill({
            color: "#F20",
          }),
          stroke: new Stroke({
            color: "#222",
            width: 1,
          }),
        }),
        // Line style
        stroke: new Stroke({
          color: "#222",
          width: 4,
        }),
      }),
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

  setExtraVectorLayerVisible(visible: boolean) {
    this.extraVectorLayer.setVisible(visible);
  }

  clearExtraVectorLayer() {
    this.extraVectorLayer.getSource()!.clear();
  }

  applyProjectFilters(overlayConfig: LayerConfig, projectId: string) {
    const { sourceUrl } = overlayConfig;
    const filter_field = "project_id";

    // Override layer source to apply the filter
    for (const [identifier, layer] of Object.entries(this.overlayLayers)) {
      // Make sure filter can be applied to the layer
      const layer_config = overlayConfig["layers"].find((l) => l.identifier === identifier);
      if (layer_config !== undefined && layer_config.filter_fields!.includes(filter_field)) {
        const clusterSource = this.createClusterSource(
          sourceUrl + `?${buildWFSQuery(identifier, filter_field, projectId)}`
        );
        layer.setSource(clusterSource);
      }
    }
  }

  private createBasemapLayerGroup(basemapConfig: LayerConfig) {
    const { layers, sourceUrl } = basemapConfig;
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

  private createOverlayLayerGroup(mapConfig: MapConfig) {
    const { overlayConfig, traffic_sign_icons_url } = mapConfig;
    const { layers, sourceUrl } = overlayConfig;

    // Fetch device layers
    const overlayLayers = layers.map(({ identifier, use_traffic_sign_icons }) => {

      const getImageStyle = (feature: FeatureLike) => {
        if (use_traffic_sign_icons && feature.get("device_type_code") !== null) {
          return new Icon({
            src: `${traffic_sign_icons_url}${feature.get("device_type_code")}.svg`,
            scale: 0.075,
          });
        } else {
          return new Circle({
            radius: 8,
            fill: new Fill({
              color: feature.get("color_code") || "#FFF",
            }),
            stroke: new Stroke({
              color: "#000",
              width: 2,
            }),
          });
        }
      };
      const clusterSource = this.createClusterSource(sourceUrl + `?${buildWFSQuery(identifier)}`);
      const vectorLayer = new VectorLayer({
        source: clusterSource,
        style: (feature: FeatureLike) => {
          return new Style({
            image: getImageStyle(feature),
          });
        },
        visible: false,
        opacity: identifier.includes("plan") ? 0.5 : 1, // 100% opacity for reals, 50% opacity for plans
      });

      this.overlayLayers[identifier] = vectorLayer;
      return vectorLayer;
    });
    return new LayerGroup({
      layers: overlayLayers,
    });
  }

  private createClusterSource(wfsUrl: string) {
    return new Cluster({
      distance: 40, // Distance in pixels within which features will be clustered together.
      source: new VectorSource({
        format: this.geojsonFormat,
        url: wfsUrl,
      }),
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
