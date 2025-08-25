import { Extent } from "ol/extent";
import { Feature } from "../models";
import { FeatureLike } from "ol/Feature";
import {
  Feature as TurfFeature,
  Polygon as TurfPolygon,
  MultiPolygon as TurfMultiPolygon,
  FeatureCollection as TurfFeatureCollection,
} from "geojson";
import { bboxPolygon, booleanIntersects, union, booleanContains } from "@turf/turf";

/**
 * The Spatial Reference System (SRS) name used for GML geometries.
 * This should match the CRS of the WFS layer's geometry property as defined in the
 * OGC Web Feature Service (WFS) specification.
 * @see {@link https://www.ogc.org/standards/wfs | OGC WFS Specification}
 * @constant {string}
 */
const SRS_NAME = "urn:ogc:def:crs:EPSG::3879";

/**
 * The name of the spatial property (geometry column) in the WFS layer.isBboxTotallyCoveredByCachedFeatures
 * This is used within the `<PropertyName>` element of the filter.
 * @constant {string}
 */
const SPATIAL_PROPERTY = "location";

export function getDistanceBetweenFeatures(feature1: Feature | FeatureLike, feature2: Feature | FeatureLike) {
  const location1 = feature1.getProperties().geometry.getFlatCoordinates();
  const location2 = feature2.getProperties().geometry.getFlatCoordinates();

  // Calculate distance between two points using Pythagorean theorem
  const distance = Math.sqrt(
    (location1[0] - location2[0]) * (location1[0] - location2[0]) +
      (location1[1] - location2[1]) * (location1[1] - location2[1]),
  );
  // Round to two decimal places
  return Math.round(distance * 100) / 100;
}

/**
 * Builds a WFS GetFeature query string with optional property filtering,
 * BBOX filtering for the current view, and server-side exclusion of cached polygons.
 * If the provided bbox is completely covered by the cached features, the function returns undefined.
 *
 * @param {string} identifier - The TYPENAME for the WFS layer (e.g., 'your:layer_name').
 * @param {Array<turf.Feature>} cachedFeatures - An array of Turf.js Features (polygons)
 * that should be excluded from the WFS response. These features are assumed to be
 * directly in **EPSG:3879** (or the CRS defined by srsName) for the WFS filter and client-side check.
 * @param {string} [filterField] - The name of the property to filter by (e.g., 'name').
 * @param {string} [filterValue] - The value to filter the property by (e.g., 'Area A').
 * @param {Extent} [bbox] - The OpenLayers extent of the current map view ([minX, minY, maxX, maxY]).
 * Assumed to be in **EPSG:3879**.
 * @returns {string | undefined} The URL search parameters string for the WFS GetFeature request,
 * or `undefined` if the bbox is totally covered by cached features,
 * or if no active filters are generated.
 */
export function buildWFSQuery(
  identifier: string,
  cachedFeatures: Array<TurfFeature> | undefined,
  filterField?: string,
  filterValue?: string,
  bbox?: Extent,
): string | undefined {
  if (isBboxTotallyCoveredByCachedFeatures(bbox, cachedFeatures)) {
    console.log("Current BBOX is totally covered by cached feature. No WFS query needed.");
    return undefined; // No new areas to fetch
  }

  let searchParams = new URLSearchParams({
    SERVICE: "WFS",
    VERSION: "2.0.0", // Ensure your WFS server supports 2.0.0 for advanced filters
    REQUEST: "GetFeature",
    OUTPUTFORMAT: "geojson", // Request GeoJSON output for easier client-side handling
    TYPENAMES: identifier,
  });

  // Generate individual filter parts
  const propertyFilterStr = getFilterFieldFilterStr(identifier, filterField, filterValue);
  const bboxFilterStr = getBboxFilterStr(bbox);
  const exclusionFilterStr = getExclusionFilterForCachedPolygons(cachedFeatures);

  // Combine all active filters
  const combinedFilterStr = getCombinedFilter(propertyFilterStr, bboxFilterStr, exclusionFilterStr);

  if (combinedFilterStr) {
    searchParams.set("FILTER", combinedFilterStr);
    return searchParams.toString();
  }
  // If no filters are generated and it wasn't totally covered,
  // you might still want to return a basic query or undefined.
  // For now, if there are no filters, we return undefined.
  // Adjust this based on whether you want a 'get all' query if no filters.
  return undefined;
}

/**
 * Checks if a given bounding box (OpenLayers Extent) is entirely covered by an array of Turf.js Features (polygons).
 * Assumes both bbox and cachedFeatures are in EPSG:3879.
 *
 * @param {Array<TurfFeature>} cachedFeatures - An array of Turf.js Polygon or MultiPolygon features.
 * @param {Extent} bbox - The OpenLayers extent to check for coverage.
 * @returns {boolean} True if the bbox is entirely contained within the union of cached features, false otherwise.
 */
function isBboxTotallyCoveredByCachedFeatures(bbox?: Extent, cachedFeatures?: Array<TurfFeature>): boolean {
  if (!bbox?.length || !cachedFeatures?.length) {
    return false;
  }

  const bboxPolygonFeature = bboxPolygon([bbox[0], bbox[1], bbox[2], bbox[3]]);

  const intersectingFeatures = cachedFeatures.filter((feature) => {
    try {
      return (
        feature.geometry &&
        ["Polygon", "MultiPolygon"].includes(feature.geometry.type) &&
        booleanIntersects(bboxPolygonFeature, feature)
      );
    } catch (e) {
      console.error("Error during booleanIntersects filter:", e);
      return false;
    }
  });

  if (intersectingFeatures.length === 0) {
    return false;
  }

  try {
    let unionResultFeature: TurfFeature<TurfPolygon | TurfMultiPolygon> = intersectingFeatures[0] as TurfFeature<
      TurfPolygon | TurfMultiPolygon
    >;

    for (let i = 1; i < intersectingFeatures.length; i++) {
      const currentFeature = intersectingFeatures[i] as TurfFeature<TurfPolygon | TurfMultiPolygon>;

      // Wrap unionResultFeature in a FeatureCollection to satisfy the type requirement.
      const unionCollection: TurfFeatureCollection<TurfPolygon | TurfMultiPolygon> = {
        type: "FeatureCollection",
        features: [unionResultFeature],
      };

      const currentUnion = union(unionCollection, currentFeature);

      if (!currentUnion) {
        console.warn("Turf.js union operation resulted in null.");
        return false;
      }
      unionResultFeature = currentUnion;
    }

    return booleanContains(unionResultFeature, bboxPolygonFeature);
  } catch (e) {
    console.error("Error during union or booleanContains:", e);
    return false;
  }
}

/**
 * Generates an OGC Filter Encoding PropertyIsLike or ResourceId filter string.
 *
 * @param {string} identifier - The layer identifier.
 * @param {string} [filterField] - The field name to filter.
 * @param {string} [filterValue] - The value for the filter.
 * @returns {string | undefined} The XML filter string or undefined.
 */
function getFilterFieldFilterStr(identifier: string, filterField?: string, filterValue?: string): string | undefined {
  if (filterField !== undefined && filterValue !== undefined && filterValue !== "") {
    if (filterField === "id") {
      // For filtering by feature ID
      return `<ResourceId rid="${identifier}.${filterValue}"/>`;
    } else {
      // For generic property LIKE filtering
      return (
        `<PropertyIsLike wildCard='*' singleChar='.' escapeChar='!'>` +
        `<PropertyName>${filterField}</PropertyName><Literal>${filterValue}</Literal>` +
        `</PropertyIsLike>`
      );
    }
  }
  return undefined;
}

/**
 * Generates an OGC Filter Encoding BBOX filter string for the given extent.
 * The `location` property name is assumed to be the geometry property.
 *
 * @param {Extent} [bbox] - The OpenLayers extent.
 * @returns {string | undefined} The XML BBOX filter string or undefined.
 */
function getBboxFilterStr(bbox?: Extent): string | undefined {
  if (bbox) {
    return (
      `<BBOX><PropertyName>location</PropertyName>` +
      `<gml:Envelope srsName="${SRS_NAME}">` +
      `<gml:lowerCorner>${bbox[0]} ${bbox[1]}</gml:lowerCorner>` +
      `<gml:upperCorner>${bbox[2]} ${bbox[3]}</gml:upperCorner>` +
      `</gml:Envelope></BBOX>`
    );
  }
  return undefined;
}

/**
 * Creates a GML string for a single Polygon or MultiPolygon interior ring.
 *
 * @param {Array<Array<number>>} ringCoords - The coordinates of the interior ring.
 * @returns {string} The GML string for the interior ring.
 */
function createInteriorRingGML(ringCoords: Array<Array<number>>): string {
  const posList = ringCoords.map((coord) => `${coord[0]} ${coord[1]}`).join(" ");
  return `<gml:interior><gml:LinearRing><gml:posList>${posList}</gml:posList></gml:LinearRing></gml:interior>`;
}

/**
 * Creates a GML string for a single Polygon geometry.
 *
 * @param {Array<Array<Array<number>>>} polygonCoords - The coordinates of the polygon.
 * @returns {string} The GML string for the polygon.
 */
function createPolygonGML(polygonCoords: Array<Array<Array<number>>>): string {
  const exteriorPosList = polygonCoords[0].map((coord) => `${coord[0]} ${coord[1]}`).join(" ");
  const exteriorRing = `<gml:exterior><gml:LinearRing><gml:posList>${exteriorPosList}</gml:posList></gml:LinearRing></gml:exterior>`;

  const interiorRings = polygonCoords.length > 1 ? polygonCoords.slice(1).map(createInteriorRingGML).join("") : "";

  return `<gml:Polygon srsName="${SRS_NAME}">${exteriorRing}${interiorRings}</gml:Polygon>`;
}

/**
 * Creates an OGC <Intersects> filter for a single Turf.js feature.
 *
 * @param {TurfFeature} feature - The Turf.js feature to convert.
 * @returns {string | null} The <Intersects> filter string or null if the feature is not a Polygon or MultiPolygon.
 */
function createIntersectsFilter(feature: TurfFeature): string | null {
  if (!feature.geometry || (feature.geometry.type !== "Polygon" && feature.geometry.type !== "MultiPolygon")) {
    return null;
  }

  let gmlGeometry = "";
  if (feature.geometry.type === "Polygon") {
    gmlGeometry = createPolygonGML(feature.geometry.coordinates);
  } else if (feature.geometry.type === "MultiPolygon") {
    // For simplicity, converting MultiPolygon to multiple Polygon filters.
    gmlGeometry = feature.geometry.coordinates.map(createPolygonGML).join("");
  }

  return `<Intersects><PropertyName>${SPATIAL_PROPERTY}</PropertyName>${gmlGeometry}</Intersects>`;
}

/**
 * Generates an OGC Filter Encoding XML string to exclude features that intersect
 * with any of the provided cached polygons.
 * This constructs a <Not><Or><Intersects>...</Intersects></Or></Not> filter,
 * or simply <Not><Intersects>...</Intersects></Not> if only one feature.
 *
 * @param {Array<TurfFeature> | undefined} cachedFeatures - The array of polygons to exclude.
 * @returns {string | undefined} The XML exclusion filter string or undefined if no features to exclude.
 */
function getExclusionFilterForCachedPolygons(cachedFeatures: Array<TurfFeature> | undefined): string | undefined {
  if (!cachedFeatures || cachedFeatures.length === 0) {
    return undefined;
  }

  const intersectionFilters = cachedFeatures.map(createIntersectsFilter).filter(Boolean);

  if (intersectionFilters.length === 0) {
    return undefined;
  }

  const filterContent =
    intersectionFilters.length === 1 ? intersectionFilters[0] : `<Or>${intersectionFilters.join("")}</Or>`;

  return `<Not>${filterContent}</Not>`;
}

/**
 * Combines multiple filter XML strings using an <And> operator if more than one filter is present.
 *
 * @param {...(string | undefined)} filterStrings - Variable number of filter XML strings.
 * @returns {string | undefined} The combined filter XML string, wrapped in <Filter>, or undefined.
 */
function getCombinedFilter(...filterStrings: (string | undefined)[]): string | undefined {
  const activeFilters = filterStrings.filter(Boolean) as string[]; // Filter out undefined/null

  if (activeFilters.length === 0) {
    return undefined; // No filters to apply
  }

  const filterContent = activeFilters.join("");

  // Use <And> if there's more than one active filter
  const startTag = activeFilters.length > 1 ? "<Filter><And>" : "<Filter>";
  const endTag = activeFilters.length > 1 ? "</And></Filter>" : "</Filter>";

  return `${startTag}${filterContent}${endTag}`;
}
