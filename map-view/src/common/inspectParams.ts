/**
 * URL query parameters used to open the map in "inspect single feature" mode,
 * e.g. `/map/?inspect_layer=<overlay identifier>&inspect_id=<feature id>`.
 */
export const INSPECT_LAYER_PARAM = "inspect_layer";
export const INSPECT_ID_PARAM = "inspect_id";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export interface InspectParams {
  /** Overlay layer identifier (WFS TYPENAME) of the inspected feature */
  layer: string;
  /** Primary key of the inspected feature */
  id: string;
}

/**
 * Read inspect mode parameters from a URL query string.
 *
 * @param search Query string, e.g. `window.location.search`
 * @returns Inspect parameters, or null if either parameter is missing or empty
 */
export function getInspectParams(search: string): InspectParams | null {
  const params = new URLSearchParams(search);
  const layer = params.get(INSPECT_LAYER_PARAM)?.trim();
  const id = params.get(INSPECT_ID_PARAM)?.trim();
  if (!layer || !id) {
    return null;
  }
  return { layer, id };
}

/**
 * Check that an inspected feature id is a UUID. The id ends up inside a WFS XML filter,
 * so anything else is rejected instead of being sent to the backend.
 *
 * @param id Feature id from the URL
 * @returns True if the id is a UUID
 */
export function isValidInspectId(id: string): boolean {
  return UUID_PATTERN.test(id);
}

/**
 * Remove the inspect mode parameters from the current URL without reloading the page.
 * Keeps the path (including the language prefix), other query parameters and the hash.
 */
export function clearInspectParams(): void {
  const url = new URL(window.location.href);
  url.searchParams.delete(INSPECT_LAYER_PARAM);
  url.searchParams.delete(INSPECT_ID_PARAM);
  // url.search is "" when no parameters are left, otherwise it includes the leading "?"
  window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
}
