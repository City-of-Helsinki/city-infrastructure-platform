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
import { Circle, Fill, Stroke, Style, Text } from "ol/style";
import { Pixel } from "ol/pixel";
import { MapBrowserEvent, Feature as OlFeature } from "ol";
import ImageSource from "ol/source/Image";
import { LineString, Point } from "ol/geom";
import { buildWFSQuery, getDistanceBetweenFeatures } from "./functions";
import { FeatureLike } from "ol/Feature";
import { Cluster } from "ol/source";
import BaseObject from "ol/Object";
import { getCenter } from "ol/extent";
import { getSinglePointStyle, isCoordinateInsideFeature } from "./MapUtils";

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
   * Available clustered overlay layers
   */
  private clusteredOverlayLayers: { [identifier: string]: VectorLayer<VectorSource> } = {};
  /**
   * Available non-clustered overlay layers
   */
  private nonClusteredOverlayLayers: { [identifier: string]: VectorLayer<VectorSource> } = {};
  /**
   * A layer to draw temporary vector features on the map
   */
  private planRealDiffVectorLayer: VectorLayer<VectorSource>;

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
    const clusteredOverlayLayerGroup = this.createClusteredOverlayLayerGroup(mapConfig);
    const nonClusteredOverlayLayerGroup = this.createNonClusteredOverlayLayerGroup(mapConfig);
    this.planRealDiffVectorLayer = Map.createPlanRealDiffVectorLayer();

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
      layers: [
        basemapLayerGroup,
        clusteredOverlayLayerGroup,
        nonClusteredOverlayLayerGroup,
        this.planRealDiffVectorLayer,
      ],
      controls: this.getControls(),
      view,
    });

    /**
     * Return all features that exist in the position that user clicked the map
     * This is ran once per visible layer
     */
    async function getFeatureFromLayer(layer: VectorLayer<VectorSource>, pixel: Pixel) {
      // Get features from clicked pixel
      return await layer.getFeatures(pixel).then((features) => {
        if (features.length) {
          // `features` always contains zero or only one Feature
          const clusterFeature = features[0];
          // Only get features are devices, ignore any non-device features such as lines between real and plan
          const clusterFeatures = clusterFeature.get("features");
          if (clusterFeatures !== undefined && clusterFeatures.length) {
            // Add `app_name` property to all features inside the `clusterFeature`
            (clusterFeature as BaseObject).set(
              "features",
              clusterFeatures.map((feature: Feature) => {
                const featureType: string = feature["id_"].split(".")[0];
                const feature_layer = overlayConfig["layers"].find((l) => l.identifier === featureType);
                feature["app_name"] = feature_layer ? feature_layer["app_name"] : "traffic_control";
                return feature;
              }),
            );
          }
        }
        return features;
      });
    }

    async function getFeaturesFromLayer(layer: VectorLayer<VectorSource>, event: MapBrowserEvent) {
      /**
       * Getting features by pixel returns just the topmost one from a single layer, so coordinate check needs to be done
       * separately.
       * Return features from event coordinate and pixel.
       * Filter out duplicate feature, as in some cases same feature is found from both.
       */
      // Get features from clicked coordinate
      const at_coordinate = layer
        .getSource()
        ?.getFeatures()
        .filter((feature) => {
          const geometry = feature.getGeometry();
          return isCoordinateInsideFeature(event.coordinate, geometry);
        });

      // get feature from pixel, filter out the ones already from coordinate
      const at_pixel = (await getFeatureFromLayer(layer, event.pixel)).filter((pixel_feat) => {
        return !at_coordinate?.map((coord_feat) => coord_feat.getId()).includes(pixel_feat.getId());
      });
      return [...(at_coordinate || []), ...at_pixel];
    }

    this.map.on("singleclick", (event) => {
      const layers = {
        ...this.clusteredOverlayLayers,
        ...this.nonClusteredOverlayLayers,
      };
      const visibleLayers = Object.values(layers).filter((layer) => layer.getVisible());

      if (visibleLayers.length > 0) {
        Promise.all(visibleLayers.map((layer) => getFeaturesFromLayer(layer, event))).then((features) => {
          const transformedFeatures = features
            .filter((f) => f.length > 0)
            .map((feature) => {
              if (feature.length && feature[0].get("features")) {
                return feature[0].get("features");
              } else {
                return feature;
              }
            });
          if (transformedFeatures.length > 0) {
            this.featureInfoCallback(transformedFeatures.flat());
          }
        });
      }
    });
  }

  /**
   * Draw a line to planRealDiffVectorLayer between two features
   */
  drawLineBetweenFeatures(feature1: Feature | FeatureLike, feature2: Feature | FeatureLike) {
    const location1 = feature1.getProperties().geometry.getFlatCoordinates();
    const location2 = feature2.getProperties().geometry.getFlatCoordinates();
    const lineString = new LineString([location1, location2]);
    const olFeature = new OlFeature({
      geometry: lineString,
      name: "Line",
    });
    this.planRealDiffVectorLayer.getSource()!.addFeature(olFeature);
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
          // Fetch feature's Plan from WFS API if it exists
          const vectorSource = new VectorSource({
            format: this.geojsonFormat,
            url:
              overlayConfig.sourceUrl +
              `?${buildWFSQuery(feature_layer.identifier, "id", feature.getProperties().device_plan_id)}`,
          });
          this.planRealDiffVectorLayer.setSource(vectorSource);

          vectorSource.on("featuresloadend", (featureEvent) => {
            const features = featureEvent.features;
            if (features) {
              this.drawLineBetweenFeatures(feature, features[0]);

              // Return distance between Real and Plan
              resolve(getDistanceBetweenFeatures(feature, features[0]));
            }
          });
        }
      } else {
        // If clicked feature belongs to planRealDiffVectorLayer, don't clear the layer
        const planRealDiffVectorLayerSource = this.planRealDiffVectorLayer.getSource();
        // @ts-ignore
        const diffFeatures = Object.values(planRealDiffVectorLayerSource!.getFeatures()).filter(
          (f) => f.getId() === feature.id_,
        );
        if (!diffFeatures.length) {
          planRealDiffVectorLayerSource!.clear();
        }
      }
    });
  }

  showAllPlanAndRealDifferences(realLayer: VectorLayer<VectorSource>, planLayer: VectorLayer<VectorSource>) {
    let realFeatures: FeatureLike[],
      planFeatures: FeatureLike[] = [];
    if (realLayer.getSource()?.getFeatures() !== undefined && planLayer.getSource()?.getFeatures() !== undefined) {
      // Get all features to single flat lists
      realFeatures = realLayer
        .getSource()!
        .getFeatures()
        .map((clusterFeature) => clusterFeature!.get("features"))
        .flat(1);
      planFeatures = planLayer
        .getSource()!
        .getFeatures()
        .map((clusterFeature) => clusterFeature!.get("features"))
        .flat(1);

      if (realFeatures.length && planFeatures.length) {
        realFeatures.forEach((realFeature) => {
          const device_plan_id = realFeature.get("device_plan_id");
          if (device_plan_id) {
            const planFeature = planFeatures.filter((planFeature) => planFeature.get("id") === device_plan_id);
            if (planFeature.length) {
              this.drawLineBetweenFeatures(realFeature, planFeature[0]);
            }
          }
        });
      }
    }
  }

  handleShowAllPlanAndRealDifferences() {
    // Make sure plan/real difference setting is enabled
    if (!this.planRealDiffVectorLayer.getVisible()) {
      return;
    }

    // Get only visible layers
    const visibleLayers = Object.fromEntries(
      Object.entries({ ...this.clusteredOverlayLayers, ...this.nonClusteredOverlayLayers }).filter(([key, layer]) =>
        layer.getVisible(),
      ),
    );

    for (const [identifier, layer] of Object.entries(visibleLayers)) {
      // Check if real layer and its plan layer are both visible
      if (identifier.includes("real") && identifier.replace("real", "plan") in visibleLayers) {
        this.showAllPlanAndRealDifferences(layer, visibleLayers[identifier.replace("real", "plan")]);
      }
    }
  }

  private static createPlanRealDiffVectorLayer() {
    const planRealDiffVectorLayer = new VectorSource({});
    return new VectorLayer({
      source: planRealDiffVectorLayer,
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

  setOverlayVisible(overlayIdentifier: string, visible: boolean) {
    if (overlayIdentifier in this.clusteredOverlayLayers) {
      this.clusteredOverlayLayers[overlayIdentifier].setVisible(visible);
    } else {
      this.nonClusteredOverlayLayers[overlayIdentifier].setVisible(visible);
    }

    if (visible) {
      this.handleShowAllPlanAndRealDifferences();
    }
  }

  setPlanRealDiffVectorLayerVisible(visible: boolean) {
    this.planRealDiffVectorLayer.setVisible(visible);

    if (visible) {
      this.handleShowAllPlanAndRealDifferences();
    }
  }

  clearPlanRealDiffVectorLayer() {
    this.planRealDiffVectorLayer.getSource()!.clear();
  }

  applyProjectFilters(overlayConfig: LayerConfig, projectId: string) {
    const { sourceUrl } = overlayConfig;
    const filter_field = "responsible_entity_name";

    // Override layer source to apply the filter
    for (const [identifier, layer] of Object.entries({
      ...this.clusteredOverlayLayers,
      ...this.nonClusteredOverlayLayers,
    })) {
      // Make sure filter can be applied to the layer
      const layer_config = overlayConfig["layers"].find((l) => l.identifier === identifier);
      if (layer_config !== undefined && layer_config.filter_fields!.includes(filter_field)) {
        const clusterSource = this.createClusterSource(
          sourceUrl + `?${buildWFSQuery(identifier, filter_field, projectId)}`,
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

  private createNonClusteredOverlayLayerGroup(mapConfig: MapConfig) {
    const { overlayConfig, traffic_sign_icons_url } = mapConfig;
    const { layers, sourceUrl } = overlayConfig;
    const overlayLayers = layers
      .filter(({ clustered }) => !clustered)
      .map(({ identifier, use_traffic_sign_icons }) => {
        const vectorSource = new VectorSource({
          format: this.geojsonFormat,
          url: sourceUrl + `?${buildWFSQuery(identifier)}`,
          overlaps: true,
        });

        // When features are loaded, check if difference between plans/reals should be shown
        vectorSource.on("featuresloadend", (featureEvent) => {
          const features = featureEvent.features;
          if (features) {
            this.handleShowAllPlanAndRealDifferences();
          }
        });

        const vectorLayer = new VectorLayer({
          source: vectorSource,
          style: (feature: FeatureLike) => getSinglePointStyle(feature, use_traffic_sign_icons, traffic_sign_icons_url),
          visible: false,
          opacity: identifier.includes("plan") ? 0.5 : 1, // 100% opacity for reals, 50% opacity for plans
        });

        this.nonClusteredOverlayLayers[identifier] = vectorLayer;
        return vectorLayer;
      });

    return new LayerGroup({
      layers: overlayLayers,
    });
  }

  private createClusteredOverlayLayerGroup(mapConfig: MapConfig) {
    const { overlayConfig, traffic_sign_icons_url } = mapConfig;
    const { layers, sourceUrl } = overlayConfig;
    // Fetch device layers
    const overlayLayers = layers
      .filter(({ clustered }) => clustered)
      .map(({ identifier, use_traffic_sign_icons }) => {
        const styleCache: { [key: string]: Style } = {};
        const getCachedStyle = (feature: FeatureLike) => {
          const features = feature.get("features");

          if (features !== undefined && features.length > 1) {
            return styleCache[features.length.toString()];
          }
          return styleCache[feature.get("features")[0].get("device_type_code")];
        };
        const getClusterStyle = (clusterFeature: FeatureLike) => {
          return new Style({
            image: new Circle({
              radius: 10,
              stroke: new Stroke({
                color: "#fff",
              }),
              fill: new Fill({
                color: "#3399CC",
              }),
            }),
            text: new Text({
              text: clusterFeature.get("features").length.toString(),
              fill: new Fill({
                color: "#fff",
              }),
            }),
          });
        };

        const getImageStyle = (clusterFeature: FeatureLike) => {
          if (clusterFeature.get("features") === undefined) return;

          let style = getCachedStyle(clusterFeature);
          if (!style) {
            const size: number = clusterFeature.get("features") ? clusterFeature.get("features").length : 0;
            if (size > 1) {
              style = getClusterStyle(clusterFeature);
              styleCache[size] = style;
            } else {
              const feature = clusterFeature.get("features")[0];
              style = getSinglePointStyle(feature, use_traffic_sign_icons, traffic_sign_icons_url);
              styleCache[feature.get("device_type_code")] = style;
            }
          }
          return style;
        };

        const clusterSource = this.createClusterSource(sourceUrl + `?${buildWFSQuery(identifier)}`);
        const vectorLayer = new VectorLayer({
          source: clusterSource,
          style: (clusterFeature: FeatureLike) => getImageStyle(clusterFeature),
          visible: false,
          opacity: identifier.includes("plan") ? 0.5 : 1, // 100% opacity for reals, 50% opacity for plans
        });

        this.clusteredOverlayLayers[identifier] = vectorLayer;
        return vectorLayer;
      });
    return new LayerGroup({
      layers: overlayLayers,
    });
  }

  private createClusterSource(wfsUrl: string) {
    const vectorSource = new VectorSource({
      format: this.geojsonFormat,
      url: wfsUrl,
    });

    // When features are loaded, check if difference between plans/reals should be shown
    vectorSource.on("featuresloadend", (featureEvent) => {
      const features = featureEvent.features;
      if (features) {
        this.handleShowAllPlanAndRealDifferences();
      }
    });

    return new Cluster({
      distance: 40, // Distance in pixels within which features will be clustered together.
      source: vectorSource,
      geometryFunction: this.clusterGeometryFunction,
      createCluster: this.createCluster,
    });
  }

  private clusterGeometryFunction(feature: FeatureLike) {
    const geometry = feature.getGeometry();
    if (geometry instanceof Point) {
      return geometry;
    } else {
      const extent = feature.getGeometry()?.getExtent();
      if (!extent) {
        return null;
      }
      return new Point(getCenter(extent));
    }
  }

  private createCluster(point: Point, features: Array<OlFeature>) {
    return new OlFeature({
      geometry: features[0].getGeometry(),
      features: features,
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
