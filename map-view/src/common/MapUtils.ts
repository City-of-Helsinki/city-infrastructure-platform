import { Circle, Geometry, GeometryCollection, LineString, MultiPolygon, Point, Polygon } from "ol/geom";
import { Fill, Icon, Stroke, Style, Circle as CircleStyle } from "ol/style";
import { FeatureLike } from "ol/Feature";
import RenderFeature from "ol/render/Feature";
import { Coordinate } from "ol/coordinate";
import { Feature, LayerConfig } from "../models";

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

export function getSinglePointStyle(
  feature: FeatureLike,
  use_traffic_sign_icons: boolean,
  traffic_sign_icons_url: string,
  icon_scale: number,
  icon_type: string,
) {
  if (use_traffic_sign_icons && feature.get("device_type_code") !== null) {
    // Traffic sign style
    return new Style({
      image: new Icon({
        src: getIconSrc(
          traffic_sign_icons_url,
          icon_type,
          feature.get("device_type_code"),
          feature.get("device_type_icon"),
        ),
        scale: icon_scale,
      }),
    });
  }

  const geometry = feature.getGeometry();
  return getStylesForGeometry(geometry);
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

function getFeatureLayer(featureType: string, overlayConfig: LayerConfig) {
  return overlayConfig["layers"].find((l) => l.identifier === featureType);
}

function getFeatureType(feature: Feature) {
  return feature["id_"].split(".")[0];
}
