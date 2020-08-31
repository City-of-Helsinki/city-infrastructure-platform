import { render } from "@testing-library/react";
import React from "react";
import FeatureInfo from "./FeatureInfo";

test("renders feature info", () => {
  const mockFeatures = ["test_feature_class.20950c38-eb7e-11ea-adc1-0242ac120002"];
  const { getByText } = render(<FeatureInfo features={mockFeatures} onClose={() => {}} />);
  const featureClass = getByText(/Test Feature Class/i);
  expect(featureClass).toBeInTheDocument();
});
