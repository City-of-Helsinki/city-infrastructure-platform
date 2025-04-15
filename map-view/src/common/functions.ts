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

export function buildWFSQuery(identifier: string, filterField?: string, filterValue?: string) {
  let searchParams = new URLSearchParams({
    SERVICE: "WFS",
    VERSION: "2.0.0",
    REQUEST: "GetFeature",
    OUTPUTFORMAT: "geojson",
    TYPENAMES: identifier,
  });

  // Apply filter, if it's defined
  if (filterField !== undefined && filterValue !== undefined && filterValue !== "") {
    // Use simpler query filter if filtered field is ID
    if (filterField === "id") {
      searchParams.set("FILTER", `<Filter><ResourceId rid="${identifier}.${filterValue}"/></Filter>`);
    } else {
      searchParams.set(
        "FILTER",
        "<Filter><PropertyIsLike wildCard='*' singleChar='.' escapeChar='!'>" +
          `<PropertyName>${filterField}</PropertyName><Literal>${filterValue}</Literal>` +
          "</PropertyIsLike></Filter>",
      );
    }
  }

  return searchParams.toString();
}
