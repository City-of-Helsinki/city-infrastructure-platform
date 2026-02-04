const mockInitialize = vi.fn();
const mockRegisterFeatureInfoCallback = vi.fn();
const mockRegisterOngoingFeatureFetchesCallback = vi.fn();
const mockSetVisibleBasemap = vi.fn();
const mockSetOverlayVisible = vi.fn();
const mockUpdateIconSettings = vi.fn();
const mockMap = {
  initialize: mockInitialize,
  registerFeatureInfoCallback: mockRegisterFeatureInfoCallback,
  registerOngoingFeatureFetchesCallback: mockRegisterOngoingFeatureFetchesCallback,
  setVisibleBasemap: mockSetVisibleBasemap,
  setOverlayVisible: mockSetOverlayVisible,
  updateIconSettings: mockUpdateIconSettings,
};

export default mockMap;
