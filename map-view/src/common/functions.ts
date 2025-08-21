import { Extent } from "ol/extent";
import { Feature } from "../models";
import { FeatureLike } from "ol/Feature";
import { Feature as TurfFeature } from "geojson";

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
 *
 * @param {string} identifier - The TYPENAME for the WFS layer (e.g., 'your:layer_name').
 * @param {Array<TurfFeature>} cachedFeatures - An array of Turf.js Features (polygons)
 * that should be excluded from the WFS response. These features are assumed to be
 * in the same CRS as the WFS layer (e.g., EPSG:3879).
 * @param {string} [filterField] - The name of the property to filter by (e.g., 'name').
 * @param {string} [filterValue] - The value to filter the property by (e.g., 'Area A').
 * @param {Extent} [bbox] - The OpenLayers extent of the current map map view ([minX, minY, maxX, maxY]).
 * @returns {string} The URL search parameters string for the WFS GetFeature request.
 */
export function buildWFSQuery(
  identifier: string,
  cachedFeatures?: Array<TurfFeature>,
  filterField?: string,
  filterValue?: string,
  bbox?: Extent,
): string {
  let searchParams = new URLSearchParams({
    SERVICE: "WFS",
    VERSION: "2.0.0",
    REQUEST: "GetFeature",
    OUTPUTFORMAT: "geojson",
    TYPENAMES: identifier,
  });

  // Generate individual filter parts
  const propertyFilterStr = getFilterFieldFilterStr(identifier, filterField, filterValue);
  const bboxFilterStr = getBboxFilterStr(bbox);
  // Generate the exclusion filter based on cached features
  const exclusionFilterStr = getExclusionFilterForCachedPolygons(cachedFeatures);

  // Combine all active filters
  const combinedFilterStr = getCombinedFilter(propertyFilterStr, bboxFilterStr, exclusionFilterStr);

  if (combinedFilterStr) {
    searchParams.set("FILTER", combinedFilterStr);
  }

  return searchParams.toString();
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
    const srsName = "urn:ogc:def:crs:EPSG::3879";
    return (
      `<BBOX><PropertyName>location</PropertyName>` +
      `<gml:Envelope srsName="${srsName}">` +
      `<gml:lowerCorner>${bbox[0]} ${bbox[1]}</gml:lowerCorner>` +
      `<gml:upperCorner>${bbox[2]} ${bbox[3]}</gml:upperCorner>` +
      `</gml:Envelope></BBOX>`
    );
  }
  return undefined;
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
    return undefined; // No features to exclude
  }

  const srsName = "urn:ogc:def:crs:EPSG::3879"; // Needs to match WFS layer's geometry CRS
  const spatialProperty = "location"; // The name of the geometry property in WFS layer

  // Create an <Or> block for all cached polygons
  const intersectionFilters = cachedFeatures
    .map((feature) => {
      // Only process Polygon or MultiPolygon geometries for intersection
      if (feature.geometry && (feature.geometry.type === "Polygon" || feature.geometry.type === "MultiPolygon")) {
        let gmlGeometry = "";
        if (feature.geometry.type === "Polygon") {
          gmlGeometry =
            `<gml:Polygon srsName="${srsName}">` +
            `<gml:exterior><gml:LinearRing><gml:posList>${feature.geometry.coordinates[0].map((coord) => `${coord[0]} ${coord[1]}`).join(" ")}</gml:posList></gml:LinearRing></gml:exterior>` +
            // Add interior rings if any
            (feature.geometry.coordinates.length > 1
              ? feature.geometry.coordinates
                  .slice(1)
                  .map(
                    (ring) =>
                      `<gml:interior><gml:LinearRing><gml:posList>${ring.map((coord) => `${coord[0]} ${coord[1]}`).join(" ")}</gml:posList></gml:LinearRing></gml:interior>`,
                  )
                  .join("")
              : "") +
            `</gml:Polygon>`;
        } else if (feature.geometry.type === "MultiPolygon") {
          // MultiPolygon is more complex for direct GML representation in FE 2.0.
          // For simplicity, converting MultiPolygon to multiple Polygon filters.
          // A more robust solution might require creating a gml:MultiSurface.
          gmlGeometry = feature.geometry.coordinates
            .map(
              (polygonCoords) =>
                `<gml:Polygon srsName="${srsName}">` +
                `<gml:exterior><gml:LinearRing><gml:posList>${polygonCoords[0].map((coord) => `${coord[0]} ${coord[1]}`).join(" ")}</gml:posList></gml:LinearRing></gml:exterior>` +
                (polygonCoords.length > 1
                  ? polygonCoords
                      .slice(1)
                      .map(
                        (ring) =>
                          `<gml:interior><gml:LinearRing><gml:posList>${ring.map((coord) => `${coord[0]} ${coord[1]}`).join(" ")}</gml:posList></gml:LinearRing></gml:interior>`,
                      )
                      .join("")
                  : "") +
                `</gml:Polygon>`,
            )
            .join(""); // Joins multiple GML Polygons if MultiPolygon
        }

        // Return an Intersects filter for this feature
        if (gmlGeometry) {
          return (
            `<Intersects>` +
            `<PropertyName>${spatialProperty}</PropertyName>` +
            `${gmlGeometry}` + 
            `</Intersects>`
          );
        }
      }
      return ""; // Skip non-polygon geometries or invalid features
    })
    .filter(Boolean); // Filter out any empty strings from unsupported geometries

  if (intersectionFilters.length === 0) {
    return undefined; // No valid polygons to create exclusion filter for
  }

  // Handle the case where there's only one intersection filter to avoid <Or> with single child
  if (intersectionFilters.length === 1) {
    return `<Not>${intersectionFilters[0]}</Not>`;
  } else {
    // Wrap all intersection filters in an <Or> block
    const orBlock = `<Or>${intersectionFilters.join("")}</Or>`;
    // Wrap the <Or> block in a <Not> to exclude features that intersect these polygons
    return `<Not>${orBlock}</Not>`;
  }
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
