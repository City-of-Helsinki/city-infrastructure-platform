import { render } from "@testing-library/react";
import React from "react";
import MapConfigAPI from "./api/MapConfigAPI";
import { mockMapConfig } from "./api/__mocks__/mock-data";
import App from "./App";
import Map from "./common/Map";

jest.mock("./common/Map");
jest.mock("./api/MapConfigAPI");

describe("App", () => {
  beforeEach(() => {
    const addListener = MapConfigAPI.getMapConfig as jest.MockedFunction<typeof MapConfigAPI.getMapConfig>;
    addListener.mockResolvedValue(mockMapConfig);
  });

  it("should initialize map with mock map config", async () => {
    const { findByText } = render(<App />);
    expect(await findByText("Layers")).toBeInTheDocument();
    expect(MapConfigAPI.getMapConfig).toHaveBeenCalled();
    expect(Map.initialize).toHaveBeenCalledWith("map", mockMapConfig);
  });
});
