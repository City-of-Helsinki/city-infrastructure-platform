import { Drawer, Fab } from "@mui/material";
import { styled } from "@mui/material/styles";
import LayersIcon from "@mui/icons-material/Layers";
import SearchIcon from "@mui/icons-material/Search";
import "ol/ol.css";
import React, { useEffect, useState } from "react";
import MapConfigAPI from "./api/MapConfigAPI";
import "./App.css";
import LayerSwitcher from "./components/LayerSwitcher";
import FeatureInfo from "./components/FeatureInfo";
import Map from "./common/Map";
import { Feature, IconSize, MapConfig } from "./models";
import OngoingFetchInfo from "./components/OngoingFetchInfo";
import AddressInput from "./components/AddressInput";
import { Address, convertToEPSG3879OL, getAddressSearchResults, getNameFromAddress } from "./common/AddressSearchUtils";
import { getFeatureType } from "./common/MapUtils";

const drawerWidth = "400px";

const ICON_SCALE_STORAGE_KEY = "mapview_icon_scale";
const ICON_TYPE_STORAGE_KEY = "mapview_icon_type";
const ICON_SIZE_STORAGE_KEY = "mapview_icon_size";
const REAL_PLAN_DISTANCE_THRESHOLD_STORAGE_KEY = "real_plan_distance_threshold";

const StyledSearchFab = styled(Fab)(() => ({
  position: "absolute",
  left: "50px",
  top: "16px",
  color: "white",
}));

const StyledLayersFab = styled(Fab)(() => ({
  position: "absolute",
  right: "16px",
  top: "16px",
  color: "white",
}));

const StyledDrawer = styled(Drawer)(() => ({
  width: drawerWidth,
  flexShrink: 0,
  "& .MuiDrawer-paper": {
    width: drawerWidth,
    boxSizing: "border-box",
  },
}));

const App = () => {
  const [open, setOpen] = useState<boolean>(false);
  const [openAddressSearch, setOpenAddressSearch] = useState<boolean>(false);
  const [mapConfig, setMapConfig] = useState<MapConfig | null>(null);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [ongoingFeatureFetches, setOngoingFeatureFetches] = useState<Set<string>>(new Set());
  const [addressSearchResults, setAddressSearchResults] = useState<Address[]>([]);
  const [iconScale, setIconScale] = useState<number>(0.1);
  const [iconType, setIconType] = useState<string>("svg");
  const [iconSize, setIconSize] = useState<IconSize>(128);
  const [realPlanDistanceThreshold, setRealPlanDistanceThreshold] = useState<number>(0);

  useEffect(() => {
    const mapId = "map";
    MapConfigAPI.getMapConfig().then(async (config: MapConfig) => {
      setMapConfig(config);

      // Try to load icon / threshold settings from localStorage
      const savedScale = localStorage.getItem(ICON_SCALE_STORAGE_KEY);
      const savedType = localStorage.getItem(ICON_TYPE_STORAGE_KEY);
      const savedSize = localStorage.getItem(ICON_SIZE_STORAGE_KEY);
      const savedThreshold = localStorage.getItem(REAL_PLAN_DISTANCE_THRESHOLD_STORAGE_KEY);

      // Parse and validate saved values
      const scale = savedScale ? Number.parseFloat(savedScale) : config.icon_scale;
      const type = savedType || config.icon_type;
      const size = savedSize ? Number.parseInt(savedSize, 10) : config.icon_size;
      const threshold = savedThreshold ? Number.parseFloat(savedThreshold) : 1;

      // Validate ranges and allowed values
      const validScale = !Number.isNaN(scale) && scale >= 0.01 && scale <= 2 ? scale : config.icon_scale;
      const validType = type === "svg" || type === "png" ? type : config.icon_type;
      const validSize = [32, 64, 128, 256].includes(size) ? (size as IconSize) : (config.icon_size as IconSize);
      const validThreshold = !Number.isNaN(threshold) && threshold >= 1 && threshold <= 2000 ? threshold : 1;

      setIconScale(validScale);
      setIconType(validType);
      setIconSize(validSize);
      setRealPlanDistanceThreshold(validThreshold);

      await Map.initialize(mapId, config);

      // Apply loaded settings to map after initialization
      Map.updateIconSettings(validScale, validType, validSize);
      Map.setRealPlanDistanceThreshold(validThreshold);
      Map.registerFeatureInfoCallback((newFeatures: Feature[]) => setFeatures(newFeatures));
      Map.registerOngoingFeatureFetchesCallback((fetches: Set<string>) => {
        setOngoingFeatureFetches(new Set(fetches));
      });
    });
  }, []);

  const handleSearch = async (address: string) => {
    const results: Address[] = await getAddressSearchResults(Map.getAddressSearchUrl(address));
    setAddressSearchResults(results);
  };

  const clearSearchResults = () => {
    setAddressSearchResults([]);
  };

  const handleSelect = (result: Address) => {
    if (result?.location?.coordinates) {
      const coordinates = convertToEPSG3879OL(result.location.coordinates);
      Map.clearSelectedAddressLayer();
      Map.markSelectedAddress(coordinates, getNameFromAddress(result) || "Address name not found");
      Map.centerToCoordinates(coordinates);
    } else {
      console.error("No valid coordinates found for selected address.");
    }
    setAddressSearchResults([]);
  };

  const removeFeatures = (removeLayerIdentifier: string) => {
    if (features.length === 0) {
      // Do nothing as there is nothing to remove
      return;
    }
    setFeatures(features.filter((feature) => getFeatureType(feature) !== removeLayerIdentifier));
  };

  const handleIconScaleChange = (scale: number) => {
    setIconScale(scale);
    localStorage.setItem(ICON_SCALE_STORAGE_KEY, scale.toString());
    Map.updateIconSettings(scale, iconType, iconSize);
  };

  const handleIconTypeChange = (type: string) => {
    setIconType(type);
    localStorage.setItem(ICON_TYPE_STORAGE_KEY, type);
    Map.updateIconSettings(iconScale, type, iconSize);
  };

  const handleIconSizeChange = (size: IconSize) => {
    setIconSize(size);
    localStorage.setItem(ICON_SIZE_STORAGE_KEY, size.toString());
    Map.updateIconSettings(iconScale, iconType, size);
  };

  const handleRealPlanDistanceThresholdChange = (threshold: number) => {
    setRealPlanDistanceThreshold(threshold);
    localStorage.setItem(REAL_PLAN_DISTANCE_THRESHOLD_STORAGE_KEY, threshold.toString());
    Map.setRealPlanDistanceThreshold(threshold);
  };

  const handleResetSettings = () => {
    if (!mapConfig) return;
    localStorage.removeItem(ICON_SCALE_STORAGE_KEY);
    localStorage.removeItem(ICON_TYPE_STORAGE_KEY);
    localStorage.removeItem(ICON_SIZE_STORAGE_KEY);
    localStorage.removeItem(REAL_PLAN_DISTANCE_THRESHOLD_STORAGE_KEY);
    setIconScale(mapConfig.icon_scale);
    setIconType(mapConfig.icon_type);
    setIconSize(mapConfig.icon_size as IconSize);
    setRealPlanDistanceThreshold(mapConfig.realPlanDistanceThreshold);
    Map.updateIconSettings(mapConfig.icon_scale, mapConfig.icon_type, mapConfig.icon_size as IconSize);
    Map.setRealPlanDistanceThreshold(1);
  };

  return (
    <React.StrictMode>
      <div className="App">
        <div id="map" />
        {features.length > 0 && mapConfig && (
          <FeatureInfo
            features={features}
            mapConfig={mapConfig}
            onSelectFeatureShowPlan={(feature: Feature) => Map.showPlanOfRealDevice(feature, mapConfig)}
            onSelectFeatureHighLight={(feature: Feature) => Map.highlightFeature(feature, mapConfig)}
            onClose={() => {
              setFeatures([]);
              Map.clearPlanOfRealVectorLayer();
              Map.clearHighlightLayer();
            }}
          />
        )}
        <StyledSearchFab
          size="medium"
          color="primary"
          onClick={() => {
            Map.showSelectedAddressLayer(!openAddressSearch);
            setOpenAddressSearch(!openAddressSearch);
          }}
        >
          <SearchIcon />
        </StyledSearchFab>
        <StyledDrawer variant="persistent" anchor="left" open={openAddressSearch}>
          <AddressInput
            onClose={() => {
              Map.showSelectedAddressLayer(false);
              setOpenAddressSearch(false);
            }}
            onSearch={handleSearch}
            onSelect={handleSelect}
            clearResults={clearSearchResults}
            results={addressSearchResults}
          />
        </StyledDrawer>
        {ongoingFeatureFetches.size > 0 && (
          <OngoingFetchInfo layerIdentifiers={ongoingFeatureFetches}></OngoingFetchInfo>
        )}
        <StyledLayersFab size="medium" color="primary" onClick={() => setOpen(!open)}>
          <LayersIcon />
        </StyledLayersFab>
        <StyledDrawer variant="persistent" anchor="right" open={open}>
          {mapConfig && (
            <LayerSwitcher
              mapConfig={mapConfig}
              onClose={() => setOpen(false)}
              onOverlayToggle={(checked: boolean, diffLayerIdentifier: string, layerIdentifier: string) => {
                if (!checked) {
                  removeFeatures(layerIdentifier);
                  Map.clearPlanRealDiffVectorLayer(diffLayerIdentifier);
                  if (
                    Object.keys(Map.getVisibleLayers()).length === 0 ||
                    Map.getHighlightFeatureType() === layerIdentifier
                  ) {
                    Map.clearHighlightLayer();
                  }
                }
              }}
              iconScale={iconScale}
              iconType={iconType}
              iconSize={iconSize}
              realPlanDistanceThreshold={realPlanDistanceThreshold}
              onRealPlanDistanceThresholdChange={handleRealPlanDistanceThresholdChange}
              onIconScaleChange={handleIconScaleChange}
              onIconTypeChange={handleIconTypeChange}
              onIconSizeChange={handleIconSizeChange}
              onResetIconSettings={handleResetSettings}
            />
          )}
        </StyledDrawer>
      </div>
    </React.StrictMode>
  );
};

export default App;
