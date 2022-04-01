export function calculateDistance(location1: number[], location2: number[]) {
  // Calculate distance between two points using Pythagorean theorem
  const distance = Math.sqrt(
    (location1[0] - location2[0]) * (location1[0] - location2[0]) +
      (location1[1] - location2[1]) * (location1[1] - location2[1])
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
  if (filterField !== undefined && filterValue !== undefined) {
    // Use simpler query filter if filtered field is ID
    if (filterField === "id") {
      searchParams.set("FILTER", `<Filter><ResourceId rid="${identifier}.${filterValue}"/></Filter>`);
    } else {
      searchParams.set(
        "FILTER",
        "<Filter><PropertyIsLike wildCard='*' singleChar='.' escapeChar='!'>" +
          `<PropertyName>${filterField}</PropertyName><Literal>${filterValue}</Literal>` +
          "</PropertyIsLike></Filter>"
      );
    }
  }

  return searchParams.toString();
}
