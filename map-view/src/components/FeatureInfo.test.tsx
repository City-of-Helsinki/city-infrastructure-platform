import { render } from "@testing-library/react";
import React from "react";
import FeatureInfo from "./FeatureInfo";
import { Feature } from "../models";

test("renders feature info", () => {
  const mockFeatures: Feature[] = [
    {
      geometry: { type: "Point", coordinates: [1, 1] },
      geometry_name: "location",
      id: "traffic_sign_real.20950c38-eb7e-11ea-adc1-0242ac120002",
      properties: {
        id: "fcdbbc6f-5903-4574-baa3-fef33a4b0621",
        direction: "DIR-1",
        txt: "sample text",
        value: 10,
        device_type_code: "ABC",
        device_type_description: "Sample description",
      },
      type: "Feature",
    },
  ];
  const { getByText } = render(
    <FeatureInfo features={mockFeatures} onSelectFeature={(feature: Feature) => {}} onClose={() => {}} />
  );
  const featureInfoTitle = getByText(/traffic_sign_real/i);
  expect(featureInfoTitle).toBeInTheDocument();
});
