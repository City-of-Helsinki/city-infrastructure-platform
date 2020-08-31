import { mockMapConfig } from "./mock-data";

export const getMapConfig = jest.fn().mockReturnValue(Promise.resolve(mockMapConfig));
const mockMapConfigAPI = {
  getMapConfig,
};

export default mockMapConfigAPI;
