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
  const props = feature.getProperties();
  const dtCode = props.device_type_code;

  let baseStyles: Style[];

  if (trafficSignIconsEnabled(feature, overlayConfig) && dtCode) {
    const iconStyleResult = getIconStyle(traffic_sign_icons_url, icon_type, icon_scale, dtCode, props.device_type_icon);
    baseStyles = toStyleArray(iconStyleResult);
  } else {
    baseStyles = toStyleArray(highLightStyle);
  }

  const arrowStyle = getDirectionArrowStyle(feature, icon_scale);
  if (arrowStyle) {
    // Add the arrow style to the end of the array, ensuring it's on top.
    baseStyles.push(arrowStyle);
  }

  return baseStyles;
}

/**
 * Ensures the result is an array of Style objects.
 * @param styleResult The style or array of styles returned by a utility function.
 * @returns An array of Style objects.
 */
const toStyleArray = (styleResult: Style | Style[] | null | undefined): Style[] => {
  if (Array.isArray(styleResult)) {
    return styleResult;
  }
  if (styleResult) {
    return [styleResult];
  }
  return [];
};

const createArrowSvg = (color: string, strokeColor: string): string => {
  // Polygon points: Tip (20,0), Base (0,70) to (40,70)
  const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 70" width="40" height="70">
            <polygon 
                points="20,0 0,70 40,70" 
                fill="${color}" 
                stroke="${strokeColor}" 
                stroke-width="3" 
                stroke-linejoin="round"
            />
        </svg>
    `;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg.trim())}`;
};

const arrowSvgUrl = createArrowSvg("red", "black");
const ARROW_SVG_WIDTH = 40;
const ARROW_SVG_HEIGHT = 70;
const GAP_PIXELS = 70;

const getFeatureRotation = (feature: FeatureLike | Feature): number | undefined => {
  const props = feature.getProperties();
  const rotation = props["direction"];

  if (typeof rotation === "number") {
    return rotation;
  }
  return undefined;
};

/**
 * Creates the Style object for the directional arrow.
 * @param feature The feature being styled.
 * @param icon_scale The scale factor for the icon.
 * @returns A Style object containing the rotated arrow, or null/undefined if no direction data exists.
 */
export function getDirectionArrowStyle(feature: FeatureLike | Feature, icon_scale: number): Style | undefined {
  const rotation_degrees = getFeatureRotation(feature);

  if (typeof rotation_degrees === "number") {
    // OpenLayers wants to have rotation as radians
    const rotation_radians = (rotation_degrees * Math.PI) / 180;

    // Anchor Calculation (Displacement Effect)
    const finalAnchorX = ARROW_SVG_WIDTH / 2;
    const finalAnchorY = ARROW_SVG_HEIGHT + GAP_PIXELS;

    return new Style({
      zIndex: 100, // Highest Z-index to ensure it sits on top
      image: new Icon({
        src: arrowSvgUrl,
        anchor: [finalAnchorX, finalAnchorY],
        anchorXUnits: "pixels",
        anchorYUnits: "pixels",
        scale: icon_scale,
        rotation: rotation_radians,
        rotateWithView: false,
      }),
    });
  }

  return undefined;
}

export function getSinglePointStyle(
  feature: FeatureLike,
  use_traffic_sign_icons: boolean,
  traffic_sign_icons_url: string,
  icon_scale: number,
  icon_type: string,
) {
  const initialStyleResult =
    use_traffic_sign_icons && feature.get("device_type_code") !== null
      ? getIconStyle(
          traffic_sign_icons_url,
          icon_type,
          icon_scale,
          feature.get("device_type_code"),
          feature.get("device_type_icon"),
        )
      : getStylesForGeometry(feature.getGeometry() as Geometry | undefined);

  const finalStyles: Style[] = toStyleArray(initialStyleResult);

  const arrowStyle = getDirectionArrowStyle(feature, icon_scale);
  if (arrowStyle) {
    finalStyles.push(arrowStyle);
  }

  return finalStyles;
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
    return base_src.replace(".svg", ".png");
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
