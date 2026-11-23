const mockInitialize = vi.fn();
const mockRegisterFeatureInfoCallback = vi.fn();
const mockRegisterOngoingFeatureFetchesCallback = vi.fn();
const mockSetVisibleBasemap = vi.fn();
const mockSetOverlayVisible = vi.fn();
const mockUpdateIconSettings = vi.fn();
const mockSetRealPlanDistanceThreshold = vi.fn();
const mockInspectFeature = vi.fn().mockResolvedValue(null);
const mockExitInspectMode = vi.fn();
const mockClearPlanRealDiffVectorLayer = vi.fn();
const mockGetVisibleLayers = vi.fn().mockReturnValue({});
const mockGetHighlightFeatureType = vi.fn();
const mockClearHighlightLayer = vi.fn();
const mockClearPlanOfRealVectorLayer = vi.fn();
const mockShowPlanOfRealDevice = vi.fn().mockResolvedValue(undefined);
const mockHighlightFeature = vi.fn();
const mockMap = {
  initialize: mockInitialize,
  registerFeatureInfoCallback: mockRegisterFeatureInfoCallback,
  registerOngoingFeatureFetchesCallback: mockRegisterOngoingFeatureFetchesCallback,
  setVisibleBasemap: mockSetVisibleBasemap,
  setOverlayVisible: mockSetOverlayVisible,
  updateIconSettings: mockUpdateIconSettings,
  setRealPlanDistanceThreshold: mockSetRealPlanDistanceThreshold,
  inspectFeature: mockInspectFeature,
  exitInspectMode: mockExitInspectMode,
  clearPlanRealDiffVectorLayer: mockClearPlanRealDiffVectorLayer,
  getVisibleLayers: mockGetVisibleLayers,
  getHighlightFeatureType: mockGetHighlightFeatureType,
  clearHighlightLayer: mockClearHighlightLayer,
  clearPlanOfRealVectorLayer: mockClearPlanOfRealVectorLayer,
  showPlanOfRealDevice: mockShowPlanOfRealDevice,
  highlightFeature: mockHighlightFeature,
};

export default mockMap;
