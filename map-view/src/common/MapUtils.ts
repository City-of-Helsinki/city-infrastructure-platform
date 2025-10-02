import { Circle, Geometry, GeometryCollection, LineString, MultiPolygon, Point, Polygon } from "ol/geom";
import { Fill, Icon, Stroke, Style, Circle as CircleStyle, Text } from "ol/style";
import { FeatureLike } from "ol/Feature";
import RenderFeature from "ol/render/Feature";
import { Coordinate } from "ol/coordinate";
import { Feature, Layer, LayerConfig, MapConfig } from "../models";
import VectorLayer from "ol/layer/Vector";
import { Cluster } from "ol/source";

const defaultFill = new Fill({ color: "magenta" });
const defaultStroke = new Stroke({
  color: "#000",
  width: 2,
});
const areaStroke = new Stroke({
  color: "black",
  width: 2,
});

const geometryStyles = {
  Point: new Style({
    image: new CircleStyle({
      radius: 5,
      fill: defaultFill,
      stroke: defaultStroke,
    }),
  }),
  MultiPoint: new Style({
    image: new CircleStyle({
      radius: 5,
      fill: defaultFill,
      stroke: defaultStroke,
    }),
  }),
  LineString: new Style({
    stroke: defaultStroke,
  }),
  MultiLineString: new Style({
    stroke: defaultStroke,
  }),
  LinearRing: new Style({
    stroke: defaultStroke,
  }),
  Polygon: new Style({
    fill: defaultFill,
    stroke: areaStroke,
  }),
  MultiPolygon: new Style({
    fill: defaultFill,
    stroke: areaStroke,
  }),
  Circle: new Style({
    fill: defaultFill,
    stroke: areaStroke,
  }),
  GeometryCollection: new Style({
    fill: defaultFill,
    stroke: areaStroke,
    image: new CircleStyle({
      radius: 5,
      fill: defaultFill,
      stroke: defaultStroke,
    }),
  }),
  unknown: new Style({
    stroke: new Stroke({
      color: "black",
      width: 1,
    }),
    fill: new Fill({
      color: "rgba(0, 0, 0, 0.1)",
    }),
  }),
};

const highLightStyle = new Style({
  fill: new Fill({ color: "rgba(255, 255, 0, 0.3)" }),
  image: new CircleStyle({
    radius: 5,
    fill: new Fill({ color: "yellow" }),
    stroke: defaultStroke,
  }),
  stroke: new Stroke({
    color: "yellow",
    width: 2,
  }),
});

function getIconStyle(
  iconsUrl: string,
  iconType: string,
  iconScale: number,
  deviceTypeCode: string,
  deviceTypeIcon: string,
) {
  return new Style({
    image: new Icon({
      src: getIconSrc(iconsUrl, iconType, deviceTypeCode, deviceTypeIcon),
      scale: iconScale,
    }),
  });
}

export function getHighlightStyle(feature: Feature, mapConfig: MapConfig) {
  const { traffic_sign_icons_url, icon_type, icon_scale, overlayConfig } = mapConfig;
  const dtCode = feature.getProperties().device_type_code;
  if (trafficSignIconsEnabled(feature, overlayConfig) && dtCode) {
    return getIconStyle(
      traffic_sign_icons_url,
      icon_type,
      icon_scale,
      dtCode,
      feature.getProperties().device_type_icon,
    );
  }
  return highLightStyle;
}

export function getSinglePointStyle(
  feature: FeatureLike,
  use_traffic_sign_icons: boolean,
  traffic_sign_icons_url: string,
  icon_scale: number,
  icon_type: string,
) {
  if (use_traffic_sign_icons && feature.get("device_type_code") !== null) {
    // Traffic sign style
    return getIconStyle(
      traffic_sign_icons_url,
      icon_type,
      icon_scale,
      feature.get("device_type_code"),
      feature.get("device_type_icon"),
    );
  }
  const geometry = feature.getGeometry();
  return getStylesForGeometry(geometry);
}

export function getAddressMarkerStyle(note: string) {
  return new Style({
    image: new CircleStyle({
      radius: 5,
      fill: defaultFill,
      stroke: defaultStroke,
    }),
    text: new Text({
      text: note,
      font: "14px Calibri,sans-serif",
      fill: new Fill({
        color: "black",
      }),
      stroke: new Stroke({
        color: "white",
        width: 3,
      }),
      offsetY: -15, // Position the text above the marker
    }),
  });
}

function getIconSrc(
  traffic_sign_icons_url: string,
  icon_type: string,
  device_type_code: string,
  overridden_icon: string = "",
) {
  const base_src = getIconBaseSrc(traffic_sign_icons_url, device_type_code, overridden_icon);
  if (icon_type === "png") {
    return base_src.concat(".png");
  } else {
    return base_src;
  }
}

/**
 *
 * @param device_type_code
 * @param overridden_icon it is assumed that this ends always with .svg
 */
function getIconBaseSrc(traffic_sign_icons_url: string, device_type_code: string, overridden_icon: string) {
  return `${traffic_sign_icons_url}${overridden_icon || `${device_type_code}.svg`}`;
}

export function getStylesForGeometry(geometry: Geometry | RenderFeature | undefined) {
  if (geometry === undefined) {
    return geometryStyles["unknown"];
  } else {
    return geometryStyles[geometry.getType()];
  }
}

export function isCoordinateInsideFeature(coordinate: Coordinate, geometry: Geometry | undefined): boolean {
  const [x, y] = coordinate;

  if (geometry === undefined) {
    return false;
  }

  if (geometry instanceof Point) {
    // A point is considered inside itself
    return geometry.getCoordinates()[0] === x && geometry.getCoordinates()[1] === y;
  } else if (geometry instanceof LineString) {
    // Check if the coordinate lies on the line string
    return geometry.intersectsCoordinate(coordinate);
  } else if (geometry instanceof Polygon) {
    // Use containsXY to check if the coordinate is inside the polygon
    return geometry.intersectsCoordinate(coordinate);
  } else if (geometry instanceof MultiPolygon) {
    // Check each polygon within the MultiPolygon
    return geometry.getPolygons().some((polygon) => polygon.intersectsCoordinate(coordinate));
  } else if (geometry instanceof Circle) {
    // Check if the coordinate is within the circle
    const center = geometry.getCenter();
    const radius = geometry.getRadius();
    const distance = Math.sqrt(Math.pow(x - center[0], 2) + Math.pow(y - center[1], 2));
    return distance <= radius;
  } else if (geometry instanceof GeometryCollection) {
    // Check each geometry in the collection
    return geometry.getGeometries().some((geom) => isCoordinateInsideFeature(coordinate, geom));
  } else {
    // Unsupported geometry type
    return false;
  }
}

export function getFeatureAppName(feature: Feature, overlayConfig: LayerConfig) {
  const name_from_feat = feature["app_name"];
  if (name_from_feat) {
    return name_from_feat;
  }
  const feature_layer = getFeatureLayer(getFeatureType(feature), overlayConfig);
  return feature_layer ? feature_layer["app_name"] : "traffic_control";
}

export function getFeatureLayerName(feature: Feature, overlayConfig: LayerConfig) {
  const feature_layer = getFeatureLayer(getFeatureType(feature), overlayConfig);
  return feature_layer ? feature_layer["name"] : "FeatureInfo title (missing)";
}

export function getFeatureLayerExtraInfoFields(feature: Feature, overlayConfig: LayerConfig) {
  const feature_layer = getFeatureLayer(getFeatureType(feature), overlayConfig);
  return feature_layer ? feature_layer["extra_feature_info"] : {};
}

export function isLayerClustered(layer: VectorLayer) {
  return layer.getSource() instanceof Cluster;
}

export function getDiffLayerIdentifier(layer: Layer) {
  return getDiffLayerIdentifierFromLayerIdentifier(layer.identifier);
}

export function getDiffLayerIdentifierFromLayerIdentifier(identifier: string) {
  return identifier.replace("real", "").replace("plan", "");
}

export function getDiffLayerIdentifierFromFeature(feature: Feature | FeatureLike, overlayConfig: LayerConfig) {
  const featureLayer = getFeatureLayer(getFeatureType(feature as Feature), overlayConfig);
  return featureLayer ? getDiffLayerIdentifier(featureLayer) : null;
}

function getFeatureLayer(featureType: string, overlayConfig: LayerConfig) {
  return overlayConfig["layers"].find((l) => l.identifier === featureType);
}

export function getFeatureType(feature: Feature) {
  return feature["id_"].split(".")[0];
}

function trafficSignIconsEnabled(feature: Feature, overlayConfig: LayerConfig) {
  const layer = getFeatureLayer(getFeatureType(feature), overlayConfig);
  return layer?.use_traffic_sign_icons;
}
