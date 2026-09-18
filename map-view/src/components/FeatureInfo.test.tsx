// eslint @typescript-eslint/no-unused-vars: 0
import { render } from "@testing-library/react";
import React from "react";
import FeatureInfo from "./FeatureInfo";
import { Feature } from "../models";
import { Point } from "ol/geom";
import { mockMapConfig } from "../api/__mocks__/mock-data";

test("renders feature info", () => {
  const mockFeatures: Feature[] = [
    {
      geometry: { type: "Point", coordinates: [1, 1] },
      geometry_name: "location",
      id_: "overlay-1.20950c38-eb7e-11ea-adc1-0242ac120002",
      getProperties: () => ({
        id: "fcdbbc6f-5903-4574-baa3-fef33a4b0621",
        geometry: new Point([25496040, 6676200, 0]),
        direction: "DIR-1",
        txt: "sample text",
        value: 10,
        additional_information: "",
        content_s: {},
        content_s_rows: [],
        device_type_code: "ABC",
        device_type_description: "Sample description",
        device_type_icon: "",
        device_plan_id: "ABC-123",
        mount_type_description_fi: "",
      }),
      type: "Feature",
    },
  ];
  const { getByText } = render(
    <FeatureInfo
      features={mockFeatures}
      mapConfig={mockMapConfig}
      onClose={() => {}}
      onSelectFeatureShowPlan={(feature = mockFeatures[0]) => new Promise((resolve) => resolve(0))}
      onSelectFeatureHighLight={(feature = mockFeatures[0]) => undefined}
    />,
  );
  const featureInfoTitle = getByText("Overlay 1");
  expect(featureInfoTitle).toBeInTheDocument();
});
