const mockInitialize = vi.fn();
const mockRegisterFeatureInfoCallback = vi.fn();
const mockSetVisibleBasemap = vi.fn();
const mockSetOverlayVisible = vi.fn();
const mockMap = {
  initialize: mockInitialize,
  registerFeatureInfoCallback: mockRegisterFeatureInfoCallback,
  setVisibleBasemap: mockSetVisibleBasemap,
  setOverlayVisible: mockSetOverlayVisible,
};

export default mockMap;
