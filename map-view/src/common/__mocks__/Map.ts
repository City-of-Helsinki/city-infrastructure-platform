const mockInitialize = jest.fn();
const mockRegisterFeatureInfoCallback = jest.fn();
const mockSetVisibleBasemap = jest.fn();
const mockSetOverlayVisible = jest.fn();
const mockMap = {
  initialize: mockInitialize,
  registerFeatureInfoCallback: mockRegisterFeatureInfoCallback,
  setVisibleBasemap: mockSetVisibleBasemap,
  setOverlayVisible: mockSetOverlayVisible,
};

export default mockMap;
