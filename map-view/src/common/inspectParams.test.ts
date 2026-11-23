import { clearInspectParams, getInspectParams, isValidInspectId } from "./inspectParams";

const featureId = "3a1f0c52-8c2e-4f6d-9b7a-1e2d3c4b5a69";

describe("getInspectParams", () => {
  it("returns layer and id when both are present", () => {
    expect(getInspectParams(`?inspect_layer=trafficsignreal&inspect_id=${featureId}`)).toEqual({
      layer: "trafficsignreal",
      id: featureId,
    });
  });

  it.each([
    ["", "no params"],
    ["?inspect_layer=trafficsignreal", "id missing"],
    [`?inspect_id=${featureId}`, "layer missing"],
    [`?inspect_layer=&inspect_id=${featureId}`, "layer empty"],
    ["?inspect_layer=trafficsignreal&inspect_id=%20", "id blank"],
  ])("returns null for %s (%s)", (search) => {
    expect(getInspectParams(search)).toBeNull();
  });
});

describe("isValidInspectId", () => {
  it("accepts UUIDs", () => {
    expect(isValidInspectId(featureId)).toBe(true);
    expect(isValidInspectId(featureId.toUpperCase())).toBe(true);
  });

  it.each(["123", "not-a-uuid", `${featureId}"/><Foo`])("rejects %s", (id) => {
    expect(isValidInspectId(id)).toBe(false);
  });
});

describe("clearInspectParams", () => {
  afterEach(() => {
    window.history.replaceState(null, "", "/");
  });

  it("removes only the inspect params and keeps path, other params and hash", () => {
    window.history.pushState(null, "", `/fi/map/?foo=bar&inspect_layer=trafficsignreal&inspect_id=${featureId}#x`);
    clearInspectParams();
    expect(window.location.pathname).toBe("/fi/map/");
    expect(window.location.search).toBe("?foo=bar");
    expect(window.location.hash).toBe("#x");
  });

  it("leaves no dangling question mark when only inspect params were present", () => {
    window.history.pushState(null, "", `/sv/map/?inspect_layer=trafficsignreal&inspect_id=${featureId}`);
    clearInspectParams();
    expect(window.location.pathname).toBe("/sv/map/");
    expect(window.location.search).toBe("");
    expect(window.location.href).toBe(`${window.location.origin}/sv/map/`);
  });
});
