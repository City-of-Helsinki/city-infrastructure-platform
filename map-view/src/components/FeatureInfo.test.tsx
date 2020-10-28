import { render } from "@testing-library/react";
import React from "react";
import FeatureInfo from "./FeatureInfo";
import { Feature } from "../models";

test("renders feature info", () => {
  const mockFeatures: Feature[] = [
    {
      geometry: { type: "Point", coordinates: [1, 1] },
      geometry_name: "location",
      id: "test_feature_class.20950c38-eb7e-11ea-adc1-0242ac120002",
      properties: {
        id: "fcdbbc6f-5903-4574-baa3-fef33a4b0621",
        code: "CODE-1",
        txt: "sample text",
      },
      type: "Feature",
    },
  ];
  const { getByText } = render(<FeatureInfo features={mockFeatures} onClose={() => {}} />);
  const featureClass = getByText(/Test Feature Class/i);
  expect(featureClass).toBeInTheDocument();
});
