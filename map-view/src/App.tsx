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

  useEffect(() => {
    const mapId = "map";
    MapConfigAPI.getMapConfig().then(async (config: MapConfig) => {
      setMapConfig(config);

      // Try to load icon settings from localStorage
      const savedScale = localStorage.getItem("mapview_icon_scale");
      const savedType = localStorage.getItem("mapview_icon_type");
      const savedSize = localStorage.getItem("mapview_icon_size");

      // Parse and validate saved values
      const scale = savedScale ? Number.parseFloat(savedScale) : config.icon_scale;
      const type = savedType || config.icon_type;
      const size = savedSize ? Number.parseInt(savedSize, 10) : config.icon_size;

      // Validate ranges and allowed values
      const validScale = !Number.isNaN(scale) && scale >= 0.01 && scale <= 2 ? scale : config.icon_scale;
      const validType = type === "svg" || type === "png" ? type : config.icon_type;
      const validSize = [32, 64, 128, 256].includes(size) ? (size as IconSize) : (config.icon_size as IconSize);

      setIconScale(validScale);
      setIconType(validType);
      setIconSize(validSize);

      await Map.initialize(mapId, config);

      // Apply loaded settings to map after initialization
      Map.updateIconSettings(validScale, validType, validSize);

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
    localStorage.setItem("mapview_icon_scale", scale.toString());
    Map.updateIconSettings(scale, iconType, iconSize);
  };

  const handleIconTypeChange = (type: string) => {
    setIconType(type);
    localStorage.setItem("mapview_icon_type", type);
    Map.updateIconSettings(iconScale, type, iconSize);
  };

  const handleIconSizeChange = (size: IconSize) => {
    setIconSize(size);
    localStorage.setItem("mapview_icon_size", size.toString());
    Map.updateIconSettings(iconScale, iconType, size);
  };

  const handleResetIconSettings = () => {
    if (!mapConfig) return;
    localStorage.removeItem("mapview_icon_scale");
    localStorage.removeItem("mapview_icon_type");
    localStorage.removeItem("mapview_icon_size");
    setIconScale(mapConfig.icon_scale);
    setIconType(mapConfig.icon_type);
    setIconSize(mapConfig.icon_size as IconSize);
    Map.updateIconSettings(mapConfig.icon_scale, mapConfig.icon_type, mapConfig.icon_size as IconSize);
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
              onIconScaleChange={handleIconScaleChange}
              onIconTypeChange={handleIconTypeChange}
              onIconSizeChange={handleIconSizeChange}
              onResetIconSettings={handleResetIconSettings}
            />
          )}
        </StyledDrawer>
      </div>
    </React.StrictMode>
  );
};

export default App;
