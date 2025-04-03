import { Drawer } from "@mui/material";
import Fab from "@mui/material/Fab";
import { Theme } from "@mui/material/styles";
import { createStyles, withStyles, WithStyles } from "@mui/styles";
import LayersIcon from "@mui/icons-material/Layers";
import "ol/ol.css";
import React from "react";
import MapConfigAPI from "./api/MapConfigAPI";
import "./App.css";
import LayerSwitcher from "./components/LayerSwitcher";
import FeatureInfo from "./components/FeatureInfo";
import Map from "./common/Map";
import { Feature, MapConfig } from "./models";

const drawWidth = "400px";

const styles = (theme: Theme) =>
  createStyles({
    mapButton: {
      position: "absolute",
      right: "16px",
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
  mapConfig: MapConfig | null;
  features: Feature[];
}

class App extends React.Component<AppProps, AppState> {
  mapId = "map";

  constructor(props: AppProps) {
    super(props);
    this.state = {
      open: false,
      mapConfig: null,
      features: [],
    };
  }

  componentDidMount() {
    MapConfigAPI.getMapConfig().then((mapConfig) => {
      this.setState({
        mapConfig,
      });
      Map.initialize(this.mapId, mapConfig);
      Map.registerFeatureInfoCallback((features: Feature[]) => this.setState({ features }));
    });
  }

  render() {
    const { classes } = this.props;
    const { open, mapConfig, features } = this.state;
    return (
      <React.StrictMode>
        <div className="App">
          <div id={this.mapId} />
          {features.length > 0 && mapConfig && (
            <FeatureInfo
              features={features}
              onSelectFeature={(feature: Feature) => Map.showPlanOfRealDevice(feature, mapConfig)}
              onClose={() => {
                this.setState({ features: [] });
                Map.clearExtraVectorLayer();
              }}
            />
          )}
          <Fab
            size="medium"
            color="primary"
            onClick={() => this.setState({ open: !open })}
            className={classes.mapButton}
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
                onOverlayToggle={(checked) => {
                  if (!checked) {
                    this.setState({ features: [] });
                    Map.clearExtraVectorLayer();
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
