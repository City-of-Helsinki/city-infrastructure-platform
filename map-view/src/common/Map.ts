import OLMap from "ol/Map";
import Projection from "ol/proj/Projection";
import Collection from "ol/Collection";
import Control from "ol/control/Control";
import MousePosition from "ol/control/MousePosition";
import { createStringXY } from "ol/coordinate";
import ScaleLine from "ol/control/ScaleLine";
import { defaults as defaultControls, OverviewMap } from "ol/control";
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
import { Extent, getCenter } from "ol/extent";
import {
  getAddressMarkerStyle,
  getDiffLayerIdentifier,
  getDiffLayerIdentifierFromFeature,
  getFeatureType,
  getHighlightStyle,
  getSinglePointStyle,
  isCoordinateInsideFeature,
  isLayerClustered,
} from "./MapUtils";
import Static from "ol/source/ImageStatic";
import { bboxPolygon, booleanIntersects, union, featureCollection } from "@turf/turf";
import { Feature as TurfFeature, Polygon as TurfPolygon, MultiPolygon as TurfMultiPolygon, BBox } from "geojson";
import { buildAddressSearchQuery } from "./AddressSearchUtils";
type TurfPolygonFeature = TurfFeature<TurfPolygon | TurfMultiPolygon>;

function debounce<T extends (...args: any[]) => void>(func: T, wait: number): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null;
  return function (this: any, ...args: Parameters<T>): void {
    const context = this;
    const later = () => {
      timeout = null;
      func.apply(context, args);
    };
    if (timeout !== null) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

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
   * OpenLayers overviewmap
   */
  private overViewMap: OverviewMap;
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
   * Layers for drawing difference lines between reals and plans
   */
  private planRealDiffVectorLayers: { [identifier: string]: VectorLayer<VectorSource> } = {};

  /**
   * A layer to draw plan of selected feature (from FeatureInfo)
   */
  private planOfRealVectorLayer: VectorLayer<VectorSource>;

  /**
   * A layer to draw highlighted feature (when active in FeatureInfo dialog)
   */
  private highLightedFeatureLayer: VectorLayer<VectorSource>;

  /**
   * A layer to draw selected address marker
   */
  private selectedAddressFeatureLayer: VectorLayer<VectorSource>;

  /**
   * Callback function to process features returned from GetFeatureInfo requests
   *
   * @param features Features returned from GetFeatureInfo requests
   */
  private featureInfoCallback: (features: Feature[]) => void = (features: Feature[]) => {};

  /**

   * Callback function to handle showing of features being loaded
   */
  private ongoingFeatureFetchesCallback: (fetches: Set<string>) => void = (fetches: Set<string>) => {};
  /**
   *  Array to store ongoing feature fetches
   */
  private readonly ongoingFeatureFetches: Set<string> = new Set();

  /**
   * mapConfig passed to this instance
   */
  private mapConfig: MapConfig;

  /**
   * Stores bounding box polygons from areas from which data has already been fetched.
   * This array might grow as the user explores the map, intersecting area will be merged.
   */
  private fetchedAreaPolygons: { [identifier: string]: TurfFeature<TurfPolygon | TurfMultiPolygon>[] } = {};

  /**
   * Debounce time before data fetch is initiated after move event
   */
  private readonly getFeaturesDebounceTime = 1000;

  /**
   * Initialize map on target element
   *
   * @param target The id of the element on which the map will be mounted
   * @param mapConfig Configurations for the map
   */
  initialize(target: string, mapConfig: MapConfig) {
    const { basemapConfig, overlayConfig, overviewConfig } = mapConfig;
    this.mapConfig = mapConfig;
    const basemapLayerGroup = this.createBasemapLayerGroup(basemapConfig);
    const clusteredOverlayLayerGroup = this.createClusteredOverlayLayerGroup(mapConfig);
    const nonClusteredOverlayLayerGroup = this.createNonClusteredOverlayLayerGroup(mapConfig);
    this.planOfRealVectorLayer = Map.createPlanOfRealVectorLayer();
    this.highLightedFeatureLayer = Map.createHighLightLayer();
    this.selectedAddressFeatureLayer = Map.createSelectedAddressLayer();
    const planRealDiffVectorLayerGroup = this.createPlanRealDiffVectorLayerGroup(mapConfig);

    const resolutions = [256, 128, 64, 32, 16, 8, 4, 2, 1, 0.5, 0.25, 0.125, 0.0625];
    const projection = this.getProjection();
    const view = new View({
      projection,
      center: this.getDefaulViewCenter(),
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
        planRealDiffVectorLayerGroup,
        this.highLightedFeatureLayer,
        this.planOfRealVectorLayer,
        this.selectedAddressFeatureLayer,
      ],
      controls: this.getControls(),
      view,
    });
    this.highLightedFeatureLayer.setVisible(true);
    this.selectedAddressFeatureLayer.setVisible(true);
    this.overViewMap = new OverviewMap({
      className: "ol-overviewmap",
      layers: [
        new ImageLayer({
          source: new Static({
            url: overviewConfig["imageUrl"],
            imageExtent: overviewConfig["imageExtent"],
          }),
        }),
      ],
      collapsed: false,
      view: new View({
        extent: overviewConfig["imageExtent"],
        showFullExtent: true,
        resolutions: [128],
      }),
    });
    this.map.addControl(this.overViewMap);

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
    // for fetching data on all layers after move or zoom
    this.map.on("moveend", debounce(this.updateVisibleLayers.bind(this), this.getFeaturesDebounceTime));
  }

  /**
   * Fetch new bounding box data for all visible layers
   */
  private updateVisibleLayers() {
    const allLayers = {
      ...this.clusteredOverlayLayers,
      ...this.nonClusteredOverlayLayers,
    };

    for (const [identifier, layer] of Object.entries(allLayers)) {
      if (layer.getVisible()) {
        const isClustered = identifier in this.clusteredOverlayLayers;
        this.getAndAddFeaturesFromBoundingBox(identifier, isClustered);
      }
    }
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
    const diffLayerIdentifier = getDiffLayerIdentifierFromFeature(feature1, this.mapConfig.overlayConfig);
    if (diffLayerIdentifier) {
      this.planRealDiffVectorLayers[diffLayerIdentifier]?.getSource()?.addFeature(olFeature);
    }
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
            url: this.getWfsUrl(feature_layer.identifier, "id", feature.getProperties().device_plan_id, true),
          });
          this.planOfRealVectorLayer.setSource(vectorSource);

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
        this.clearPlanOfRealVectorLayer();
      }
    });
  }

  /**
   *
   * @param feature Target feature to be highlighted
   */
  highlightFeature(feature: Feature, mapConfig: MapConfig) {
    this.clearHighlightLayer();
    const olFeature = new OlFeature({
      geometry: feature.getProperties().geometry,
      name: "HiglightedFeature",
      featureType: getFeatureType(feature),
    });

    this.highLightedFeatureLayer.setStyle(getHighlightStyle(feature, mapConfig));
    this.highLightedFeatureLayer.getSource()?.addFeature(olFeature);
  }

  /**
   *
   */
  getHighlightFeatureType() {
    const features = this.highLightedFeatureLayer.getSource()?.getFeatures();
    // there is always 0 or 1 highlighted features
    if (features && features?.length > 0) {
      return features[0].getProperties().featureType;
    }
  }

  /**
   *
   */
  markSelectedAddress(coords: [number, number], address: string) {
    const olFeature = new OlFeature({
      geometry: new Point(coords),
      name: "selectedAddress",
    });
    this.selectedAddressFeatureLayer.setStyle(getAddressMarkerStyle(address));
    this.selectedAddressFeatureLayer.getSource()?.addFeature(olFeature);
  }

  showAllPlanAndRealDifferences(realLayer: VectorLayer<VectorSource>, planLayer: VectorLayer<VectorSource>) {
    let realFeatures: FeatureLike[],
      planFeatures: FeatureLike[] = [];

    const realLayerFeatures = realLayer.getSource()?.getFeatures();
    const planLayerFeatures = planLayer.getSource()?.getFeatures();
    if (realLayerFeatures !== undefined && planLayerFeatures !== undefined) {
      // Get all features to single flat lists
      realFeatures = realLayerFeatures
        .map((feature) => (isLayerClustered(realLayer) ? feature.get("features") : feature))
        .flat(1);
      planFeatures = planLayerFeatures
        .map((feature) => (isLayerClustered(planLayer) ? feature.get("features") : feature))
        .flat(1);

      if (realFeatures.length && planFeatures.length) {
        const byPlanId = Object.fromEntries(
          planFeatures.map((pf) => {
            return [pf.get("id"), pf];
          }),
        );
        for (const realFeature of realFeatures) {
          const device_plan_id = realFeature.get("device_plan_id");
          if (device_plan_id) {
            const planFeature = byPlanId[device_plan_id];
            if (planFeature) {
              this.drawLineBetweenFeatures(realFeature, planFeature);
            }
          }
        }
      }
    }
  }

  handleShowAllPlanAndRealDifferences() {
    // Get only visible layers
    const visibleLayers = this.getVisibleLayers();

    for (const [identifier, layer] of Object.entries(visibleLayers)) {
      // Check if real layer and its plan layer are both visible
      if (identifier.includes("real") && identifier.replace("real", "plan") in visibleLayers) {
        this.showAllPlanAndRealDifferences(layer, visibleLayers[identifier.replace("real", "plan")]);
      }
    }
  }

  getVisibleLayers() {
    return Object.fromEntries(
      Object.entries({ ...this.clusteredOverlayLayers, ...this.nonClusteredOverlayLayers }).filter(([key, layer]) =>
        layer.getVisible(),
      ),
    );
  }

  private static createHighLightLayer() {
    const highLightLayerSource = new VectorSource({});
    return new VectorLayer({
      source: highLightLayerSource,
    });
  }

  private static createSelectedAddressLayer() {
    const selectedAddressSource = new VectorSource({});
    return new VectorLayer({
      source: selectedAddressSource,
    });
  }

  private static createPlanRealDiffVectorLayer() {
    const planRealDiffVectorLayerSource = new VectorSource({});
    return new VectorLayer({
      source: planRealDiffVectorLayerSource,
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

  private static createPlanOfRealVectorLayer() {
    const planOfRealVectorLayerSource = new VectorSource({});
    return new VectorLayer({
      source: planOfRealVectorLayerSource,
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
      }),
    });
  }

  registerFeatureInfoCallback(fn: (features: Feature[]) => void) {
    this.featureInfoCallback = fn;
  }

  registerOngoingFeatureFetchesCallback(fn: (fetches: Set<string>) => void) {
    this.ongoingFeatureFetchesCallback = fn;
  }

  setVisibleBasemap(basemap: string) {
    // there can be only one visible base
    this.basemapLayers[this.visibleBasemap].setVisible(false);
    this.visibleBasemap = basemap;
    this.basemapLayers[this.visibleBasemap].setVisible(true);
  }

  setOverlayVisible(overlayIdentifier: string, visible: boolean) {
    if (overlayIdentifier in this.clusteredOverlayLayers) {
      if (visible) {
        this.getAndAddFeaturesFromBoundingBox(overlayIdentifier, true);
      }
      this.clusteredOverlayLayers[overlayIdentifier].setVisible(visible);
    } else {
      if (visible) {
        this.getAndAddFeaturesFromBoundingBox(overlayIdentifier, false);
      }
      this.nonClusteredOverlayLayers[overlayIdentifier].setVisible(visible);
    }
  }

  getWfsUrl(overlayIdentifier: string, filterId?: string, filterValue?: string, ignoreBbox?: boolean) {
    const urlBuildResult = buildWFSQuery(
      overlayIdentifier,
      ignoreBbox ? undefined : this.fetchedAreaPolygons[overlayIdentifier],
      filterId,
      filterValue,
      ignoreBbox ? undefined : this.getCurrentBoundingBox(),
    );
    if (urlBuildResult) {
      return this.mapConfig.overlayConfig.sourceUrl + `?${urlBuildResult}`;
    } else {
      return undefined;
    }
  }

  getAndAddFeaturesFromBoundingBox(overlayIdentifier: string, isClustered: boolean) {
    const wfsUrl = this.getWfsUrl(overlayIdentifier);
    if (!wfsUrl) {
      // nothing to fetch
      return;
    }

    const tempSource = isClustered ? this.createClusterSource(wfsUrl) : this.createNonClusteredSource(wfsUrl);
    const tempVectorSource = isClustered ? (tempSource as Cluster).getSource() : tempSource;
    if (!tempVectorSource) {
      console.log("No vector source, skipping getting new features");
      return;
    }

    this.ongoingFeatureFetches.add(overlayIdentifier);
    this.ongoingFeatureFetchesCallback(this.ongoingFeatureFetches);
    // create a temporary layer and add it to the map
    // to initialize data fetch
    const tempLayer = new VectorLayer({
      source: tempVectorSource,
      visible: true,
      style: new Style({
        fill: new Fill({ color: "rgba(0, 0, 0, 0)" }),
        stroke: new Stroke({ color: "rgba(0, 0, 0, 0)" }),
      }),
    });
    this.map.addLayer(tempLayer);
    tempVectorSource.once("featuresloadend", (featureEvent: any) => {
      const features = featureEvent.features;
      if (features && features.length > 0) {
        const layer = isClustered
          ? this.clusteredOverlayLayers[overlayIdentifier]
          : this.nonClusteredOverlayLayers[overlayIdentifier];
        layer.once("postrender", () => {
          this.handleShowAllPlanAndRealDifferences();
        });

        const existingSource = layer.getSource();
        if (existingSource) {
          const targetVectorSource = isClustered ? (existingSource as Cluster).getSource() : existingSource;
          if (!targetVectorSource) {
            console.log("No vector source, skipping add of new features");
            return;
          }
          targetVectorSource.addFeatures(features);
        } else {
          layer.setSource(tempSource);
        }
        this.addFetchedArea(overlayIdentifier, this.getCurrentBoundingBox());
      }
      this.map.removeLayer(tempLayer);
      this.ongoingFeatureFetches.delete(overlayIdentifier);
      this.ongoingFeatureFetchesCallback(this.ongoingFeatureFetches);
    });
  }

  /**
   * Checks if two polygons intersect and attempts to merge them.
   * @param mergedPolygon The polygon to merge with.
   * @param existingPolygon The existing polygon to check for intersection.
   * @returns An array containing the merged polygon if successful, otherwise returns the existing polygon.
   */
  attemptMerge(mergedPolygon: TurfPolygonFeature, existingPolygon: TurfPolygonFeature): TurfPolygonFeature[] {
    // Check for invalid geometry before performing the union.
    if (!mergedPolygon?.geometry || !existingPolygon?.geometry) {
      console.error("Skipping union due to invalid input geometry.", mergedPolygon, existingPolygon);
      return [existingPolygon]; // Return original to prevent data loss.
    }

    try {
      const unionResult = union(featureCollection([mergedPolygon, existingPolygon]));
      return unionResult ? [unionResult] : [existingPolygon];
    } catch (e) {
      console.error("Error during polygon union. Keeping the original polygon.", e);
      return [existingPolygon];
    }
  }

  /**
   * Iterates through existing polygons and merges them with a new polygon if they intersect.
   * @param newPolygon The new polygon to merge.
   * @param existingPolygons The array of existing polygons.
   * @returns An object containing the final merged polygon and the list of non-intersecting polygons.
   */
  mergeIntersectingPolygons(
    newPolygon: TurfPolygonFeature,
    existingPolygons: TurfPolygonFeature[],
  ): { mergedPolygon: TurfPolygonFeature; nonIntersecting: TurfPolygonFeature[]; wasMerged: boolean } {
    let mergedPolygon = newPolygon;
    let wasMerged = false;
    const nonIntersecting: TurfPolygonFeature[] = [];

    for (const existingPolygon of existingPolygons) {
      if (booleanIntersects(mergedPolygon, existingPolygon)) {
        const unionResults = this.attemptMerge(mergedPolygon, existingPolygon);
        mergedPolygon = unionResults[0];
        wasMerged = true;
      } else {
        nonIntersecting.push(existingPolygon);
      }
    }

    return { mergedPolygon, nonIntersecting, wasMerged };
  }

  /**
   * Adds a new fetched area polygon to the cache, merging it with any intersecting polygons.
   * @param layerIdentifier The identifier for the layer.
   * @param fetchedBbox The bounding box of the newly fetched area.
   */
  addFetchedArea(layerIdentifier: string, fetchedBbox: Extent) {
    // Use a guard clause for early return if there's no layer identifier
    if (!layerIdentifier) {
      console.error("No layer identifier provided.");
      return;
    }

    // Initialize the array if it doesn't exist
    this.fetchedAreaPolygons[layerIdentifier] = this.fetchedAreaPolygons[layerIdentifier] || [];

    const newTurfPolygon = bboxPolygon(fetchedBbox as BBox);

    const { mergedPolygon, nonIntersecting, wasMerged } = this.mergeIntersectingPolygons(
      newTurfPolygon as TurfPolygonFeature,
      this.fetchedAreaPolygons[layerIdentifier],
    );

    // Update the cache with the final merged polygon and the non-intersecting ones
    this.fetchedAreaPolygons[layerIdentifier] = [...nonIntersecting, mergedPolygon];

    this.logMergeStatus(layerIdentifier, wasMerged);
  }

  /**
   * Logs the status of the polygon merge.
   * @param layerIdentifier The identifier for the layer.
   * @param wasMerged Indicates if a merge occurred.
   */
  private logMergeStatus(layerIdentifier: string, wasMerged: boolean) {
    if (wasMerged) {
      console.log(`Merged fetched polygons for layer '${layerIdentifier}'.`);
    } else {
      console.log(`Added new polygon to layer '${layerIdentifier}'.`);
    }
    console.log(
      `Total polygons for '${layerIdentifier}': ${this.fetchedAreaPolygons[layerIdentifier].length}`,
      this.fetchedAreaPolygons[layerIdentifier],
    );
  }

  /**
   * This is called from settings in LayerSwitcher to show or hide all difference layers
   * @param visible
   * @param identifier
   */
  setPlanRealDiffVectorLayersVisible(visible: boolean) {
    Object.values(this.planRealDiffVectorLayers).forEach((layer) => layer.setVisible(visible));

    if (visible) {
      this.handleShowAllPlanAndRealDifferences();
    }
  }

  clearPlanRealDiffVectorLayer(identifier: string) {
    if (identifier) {
      this.planRealDiffVectorLayers[identifier]?.getSource()?.clear();
    }
  }

  clearPlanOfRealVectorLayer() {
    this.planOfRealVectorLayer.getSource()?.clear();
  }

  clearHighlightLayer() {
    this.highLightedFeatureLayer.getSource()?.clear();
  }

  clearSelectedAddressLayer() {
    this.selectedAddressFeatureLayer.getSource()?.clear();
  }

  showSelectedAddressLayer(show: boolean) {
    this.selectedAddressFeatureLayer.setVisible(show);
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
      // atleast for now everyhing is just loaded within the current bbox, not exclusion
      const layer_config = overlayConfig["layers"].find((l) => l.identifier === identifier);
      if (layer_config !== undefined && layer_config.filter_fields!.includes(filter_field)) {
        const clusterSource = this.createClusterSource(
          sourceUrl + `?${buildWFSQuery(identifier, undefined, filter_field, projectId, this.getCurrentBoundingBox())}`,
        );
        layer.setSource(clusterSource);
      }
    }
  }

  centerToCoordinates(coords: Array<number>) {
    this.map.once("moveend", () => {
      this.updateVisibleLayers();
    });
    this.map.getView().animate({
      center: coords,
      zoom: 10,
      duration: 2000,
    });
  }

  getAddressSearchUrl(address: string) {
    const searchUrlWithParams = buildAddressSearchQuery(address);
    return `${this.mapConfig.address_search_base_url}?${searchUrlWithParams}`;
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

  private createPlanRealDiffVectorLayerGroup(mapConfig: MapConfig) {
    const { overlayConfig } = mapConfig;
    const { layers } = overlayConfig;
    this.planRealDiffVectorLayers = Object.fromEntries(
      layers
        .filter((layer) => layer.identifier.includes("real"))
        .map((layer) => {
          return [getDiffLayerIdentifier(layer), Map.createPlanRealDiffVectorLayer()];
        }),
    );
    return new LayerGroup({ layers: Object.values(this.planRealDiffVectorLayers) });
  }

  private createNonClusteredOverlayLayerGroup(mapConfig: MapConfig) {
    const { overlayConfig, traffic_sign_icons_url, icon_scale, icon_type } = mapConfig;
    const { layers } = overlayConfig;
    const overlayLayers = layers
      .filter(({ clustered }) => !clustered)
      .map(({ identifier, use_traffic_sign_icons }) => {
        const vectorLayer = new VectorLayer({
          style: (feature: FeatureLike) =>
            getSinglePointStyle(feature, use_traffic_sign_icons, traffic_sign_icons_url, icon_scale, icon_type),
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
    const { overlayConfig, traffic_sign_icons_url, icon_scale, icon_type } = mapConfig;
    const { layers } = overlayConfig;
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
              style = getSinglePointStyle(
                feature,
                use_traffic_sign_icons,
                traffic_sign_icons_url,
                icon_scale,
                icon_type,
              );
              styleCache[feature.get("device_type_code")] = style;
            }
          }
          return style;
        };

        const vectorLayer = new VectorLayer({
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

  private createNonClusteredSource(wfsUrl: string) {
    return this.createVectorSource(wfsUrl);
  }

  private createClusterSource(wfsUrl: string) {
    const vectorSource = this.createVectorSource(wfsUrl);

    return new Cluster({
      distance: 40, // Distance in pixels within which features will be clustered together.
      source: vectorSource,
      geometryFunction: this.clusterGeometryFunction,
      createCluster: this.createCluster,
    });
  }

  private createVectorSource(wfsUrl: string) {
    const vectorSource = new VectorSource({
      format: this.geojsonFormat,
      url: wfsUrl,
    });
    return vectorSource;
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

  private getDefaulViewCenter() {
    return [25499052.02, 6675851.38];
  }

  private getCurrentBoundingBox() {
    return this.map.getView().calculateExtent();
  }
}

export default new Map();
