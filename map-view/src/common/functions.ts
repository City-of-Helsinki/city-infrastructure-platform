import { Extent } from "ol/extent";
import { Feature } from "../models";
import { FeatureLike } from "ol/Feature";

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

export function buildWFSQuery(identifier: string, filterField?: string, filterValue?: string, bbox?: Extent) {
  let searchParams = new URLSearchParams({
    SERVICE: "WFS",
    VERSION: "2.0.0",
    REQUEST: "GetFeature",
    OUTPUTFORMAT: "geojson",
    TYPENAMES: identifier,
  });
  // Apply filters, if it's defined
  //const combinedFilterStr = getCombinedFilter(getFilterFieldFilterStr(identifier, filterField, filterValue), getBboxFilterStr(bbox));
  const combinedFilterStr = getCombinedFilter(getFilterFieldFilterStr("additionalsignreal", filterField, filterValue), getBboxFilterStr(bbox));
  if (combinedFilterStr) {
    searchParams.set("FILTER", combinedFilterStr);
  }
  console.log("JF combined filter", combinedFilterStr);
  return searchParams.toString();
}

function getFilterFieldFilterStr(identifier: string, filterField?: string, filterValue?: string) {
  return undefined // JF HÄKHÄK bbox testiä varten eikä tuo project filteri muutenkaan toimi
  if (filterField !== undefined && filterValue !== undefined && filterValue !== "") {
    if (filterField === "id") {
      return '<ResourceId rid="${identifier}.${filterValue}"/>'
    } else {
      return "<PropertyIsLike wildCard='*' singleChar='.' escapeChar='!'>" +
          `<PropertyName>${filterField}</PropertyName><Literal>${filterValue}</Literal>` +
          "</PropertyIsLike>"
    }
  }
}

function getBboxFilterStr(bbox?: Extent) {
  console.log("JF bbox", bbox)
  if (bbox) {
    return `<BBOX><PropertyName>location</PropertyName>` +
      `<gml:Envelope srsName="urn:ogc:def:crs:EPSG::3879">` +
      `<gml:lowerCorner>${bbox[0]} ${bbox[1]}</gml:lowerCorner>` +
      `<gml:upperCorner>${bbox[2]} ${bbox[3]}</gml:upperCorner>` +
      `</gml:Envelope></BBOX>`
  }
}

function getCombinedFilter(filterFieldFilterStr?: string, bboxFilterStr?: string) {
  // todo bbox filter
  const filters = []
  if (filterFieldFilterStr) {
    filters.push(filterFieldFilterStr)
  }
  if (bboxFilterStr) {
    filters.push(bboxFilterStr)
  }
  const filterContent = filters.join("");
  const startTag = filters.length > 1 ? "<Filter><And>" : "<Filter>"
  const endTag = filters.length > 1 ? "</And></Filter>" : "</Filter>"

  if (filterContent) {
    return `${startTag}${filterContent}${endTag}`
  }
}

