import { Drawer } from "@mui/material";
import Fab from "@mui/material/Fab";
import { Theme } from "@mui/material/styles";
import { createStyles, withStyles, WithStyles } from "@mui/styles";
import LayersIcon from "@mui/icons-material/Layers";
import SearchIcon from "@mui/icons-material/Search";
import "ol/ol.css";
import React from "react";
import MapConfigAPI from "./api/MapConfigAPI";
import "./App.css";
import LayerSwitcher from "./components/LayerSwitcher";
import FeatureInfo from "./components/FeatureInfo";
import Map from "./common/Map";
import { Feature, MapConfig } from "./models";
import OngoingFetchInfo from "./components/OngoingFetchInfo";
import AddressInput from "./components/AddressInput";
import { Address, convertToEPSG3879OL, getAddressSearchResults, getNameFromAddress } from "./common/AddressSearchUtils";

const drawWidth = "400px";

const styles = (theme: Theme) =>
  createStyles({
    layerSwitcherButton: {
      position: "absolute",
      right: "16px",
      top: "16px",
      color: "white",
    },
    searchButton: {
      position: "absolute",
      left: "50px",
      top: "16px",
      color: "white",
    },
    drawer: {
      width: drawWidth,
    },
    drawerPaper: {
      width: drawWidth,
    },
  });

interface AppProps extends WithStyles<typeof styles> {}

interface AppState {
  open: boolean;
  openAddressSearch: boolean;
  mapConfig: MapConfig | null;
  features: Feature[];
  ongoingFeatureFetches: Set<string>;
  addressSearchResults: Address[];
}

class App extends React.Component<AppProps, AppState> {
  mapId = "map";

  constructor(props: AppProps) {
    super(props);
    this.state = {
      open: false,
      openAddressSearch: false,
      mapConfig: null,
      features: [],
      ongoingFeatureFetches: new Set<string>(),
      addressSearchResults: [],
    };
  }

  componentDidMount() {
    MapConfigAPI.getMapConfig().then((mapConfig) => {
      this.setState({
        mapConfig,
      });
      Map.initialize(this.mapId, mapConfig);
      Map.registerFeatureInfoCallback((features: Feature[]) => this.setState({ features }));
      Map.registerOngoingFeatureFetchesCallback((fetches: Set<string>) =>
        this.setState({ ongoingFeatureFetches: fetches }),
      );
    });
  }

  handleSearch = async (address: string) => {
    const addressSearchResults = await getAddressSearchResults(Map.getAddressSearchUrl(address));
    this.setState({ addressSearchResults });
  };

  clearSearchResults = () => {
    this.setState({ addressSearchResults: [] });
  };

  handleSelect = (result: Address) => {
    if (result?.location?.coordinates) {
      const coordinates = convertToEPSG3879OL(result.location.coordinates);
      Map.clearSelectedAddressLayer();
      Map.markSelectedAddress(coordinates, getNameFromAddress(result) || "Address name not found");
      Map.centerToCoordinates(coordinates);
    } else {
      console.error("No valid coordinates found for selected address.");
    }
    this.setState({ addressSearchResults: [] });
  };

  render() {
    const { classes } = this.props;
    const { open, openAddressSearch, mapConfig, features, ongoingFeatureFetches, addressSearchResults } = this.state;
    return (
      <React.StrictMode>
        <div className="App">
          <div id={this.mapId} />
          {features.length > 0 && mapConfig && (
            <FeatureInfo
              features={features}
              mapConfig={mapConfig}
              onSelectFeatureShowPlan={(feature: Feature) => Map.showPlanOfRealDevice(feature, mapConfig)}
              onSelectFeatureHighLight={(feature: Feature) => Map.highlightFeature(feature, mapConfig)}
              onClose={() => {
                this.setState({ features: [] });
                Map.clearPlanOfRealVectorLayer();
                Map.clearHighlightLayer();
              }}
            />
          )}
          <Fab
            size="medium"
            color="primary"
            onClick={() => {
              Map.showSelectedAddressLayer(!openAddressSearch);
              this.setState({ openAddressSearch: !openAddressSearch });
            }}
            className={classes.searchButton}
          >
            <SearchIcon />
          </Fab>
          <Drawer
            className={classes.drawer}
            variant="persistent"
            anchor="left"
            open={openAddressSearch}
            classes={{
              paper: classes.drawerPaper,
            }}
          >
            <AddressInput
              onClose={() => {
                Map.showSelectedAddressLayer(false);
                this.setState({ openAddressSearch: false });
              }}
              onSearch={this.handleSearch}
              onSelect={this.handleSelect}
              clearResults={this.clearSearchResults}
              results={addressSearchResults}
            />
          </Drawer>
          {ongoingFeatureFetches.size > 0 && (
            <OngoingFetchInfo layerIdentifiers={ongoingFeatureFetches}></OngoingFetchInfo>
          )}
          <Fab
            size="medium"
            color="primary"
            onClick={() => this.setState({ open: !open })}
            className={classes.layerSwitcherButton}
          >
            <LayersIcon />
          </Fab>
          <Drawer
            className={classes.drawer}
            variant="persistent"
            anchor="right"
            open={open}
            classes={{
              paper: classes.drawerPaper,
            }}
          >
            {mapConfig && (
              <LayerSwitcher
                mapConfig={mapConfig}
                onClose={() => this.setState({ open: false })}
                onOverlayToggle={(checked, diffLayerIdentifier) => {
                  if (!checked) {
                    this.setState({ features: [] });
                    Map.clearPlanRealDiffVectorLayer(diffLayerIdentifier);
                  }
                }}
              />
            )}
          </Drawer>
        </div>
      </React.StrictMode>
    );
  }
}

export default withStyles(styles)(App);
