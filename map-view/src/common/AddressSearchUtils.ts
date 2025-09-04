import { fromLonLat, addCoordinateTransforms, get as getProjection, addProjection, Projection } from "ol/proj";
import proj4 from "proj4";

// Define the EPSG:3879 projection string using proj4's definition function.
// This tells proj4 what the projection is. This must be done before anything else.
proj4.defs(
  "EPSG:3879",
  "+proj=tmerc +lat_0=0 +lon_0=25 +k=1 +x_0=25500000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
);

// Register the proj4 projection with OpenLayers.
addProjection(
  new Projection({
    code: "EPSG:3879",
    units: "m",
  }),
);

// Get the projection objects for both the source (WGS 84) and destination (EPSG:3879).
const wgs84Projection = getProjection("EPSG:4326");
const epsg3879Projection = getProjection("EPSG:3879");

// Check that both projections exist before adding the transform.
if (wgs84Projection && epsg3879Projection) {
  // Add the coordinate transformation between EPSG:4326 and EPSG:3879.
  addCoordinateTransforms(
    wgs84Projection,
    epsg3879Projection,
    // Forward transform from EPSG:4326 to EPSG:3879
    function (coordinate) {
      return proj4("EPSG:4326", "EPSG:3879", coordinate);
    },
    // Inverse transform from EPSG:3879 to EPSG:4326
    function (coordinate) {
      return proj4("EPSG:3879", "EPSG:4326", coordinate);
    },
  );
} else {
  console.error("Failed to get one or both projection objects for coordinate transformation.");
}

/**
 *
 */
export function buildAddressSearchQuery(address: string) {
  return new URLSearchParams({
    q: address,
    type: "address",
    municipality: "helsinki",
    language: getResolvedLanguageCode() || "fi",
  }).toString();
}

interface Location {
  type: string;
  coordinates: [number, number];
}

interface Municipality {
  id: string;
  name: {
    fi: string;
    sv: string;
  };
}

interface Street {
  name: {
    fi: string;
    sv: string;
  };
}

export interface Address {
  object_type: string;
  name: {
    fi: string;
    sv: string;
    en: string;
  };
  number: string;
  number_end: string;
  letter: string;
  modified_at: string;
  municipality: Municipality;
  street: Street;
  location: Location;
}

interface ApiResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Address[];
}

/**
 * Transforms geographic coordinates from WGS 84 (EPSG:4326) to EPSG:3879
 * using the OpenLayers fromLonLat function.
 * * @param {number[]} wgs84Coords - The coordinates in WGS 84 format [longitude, latitude].
 * @returns {number[]} The transformed coordinates in EPSG:3879 format [x, y], only 1 page of results are used.
 */
export function convertToEPSG3879OL(wgs84Coords: [number, number]): [number, number] {
  const transformed = fromLonLat(wgs84Coords, "EPSG:3879");
  return transformed as [number, number];
}

export async function getAddressSearchResults(url: string): Promise<Address[]> {
  console.log("Fetching results from:", url);
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data: ApiResponse = await response.json();
    return data.results || [];
  } catch (error) {
    console.error("Error fetching search results:", error);
    return [];
  }
}

/**
 * Extracts the language code from the URL path.
 * Assumes the language code is the first segment after the domain (e.g., http://localhost:8000/en/map/).
 *
 * @returns {string | undefined} The language code found in the URL, or undefined if not present.
 */
export function getLanguageCodeFromUrl(): string | undefined {
  const pathSegments = window.location.pathname.split("/");
  // The first segment after the root '/' is at index 1.
  const langCode = pathSegments[1];
  return langCode;
}

/**
 * Resolves the language code by first checking the URL and then falling back to the browser settings.
 *
 * @returns {string | undefined} The resolved language code, or undefined if none is found.
 */
export function getResolvedLanguageCode(): string | undefined {
  const urlLang = getLanguageCodeFromUrl();
  if (urlLang) {
    return urlLang;
  }

  const browserLang = getBrowserLanguageCode();
  return browserLang;
}

/**
 * Extracts the primary language code from the user's browser settings.
 * For example, it will return 'en' from 'en-US'.
 *
 * @returns {string | undefined} The language code from the browser, or undefined if not available.
 */
export function getBrowserLanguageCode(): string | undefined {
  // navigator.language returns a string like 'en-US' or 'fi-FI'
  // .split('-')[0] extracts the primary language code (e.g., 'en' or 'fi')
  return navigator.language.split("-")[0];
}

/**
 * Gets the localized name from an Address object based on the resolved language code.
 *
 * @param {Address} address - The Address object containing the name variants.
 * @returns {string | undefined} The name in the resolved language, or undefined if no match is found.
 */
export function getNameFromAddress(address: Address): string | undefined {
  const { name } = address;

  // 1. Get the resolved language code
  const resolvedLang = getResolvedLanguageCode();
  if (resolvedLang && name[resolvedLang as keyof typeof name]) {
    return name[resolvedLang as keyof typeof name];
  }

  // 2. Optional: Fallback to a default language if no match is found
  if (name.en) {
    return name.en;
  }

  return undefined;
}
