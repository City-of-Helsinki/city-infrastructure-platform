import { Drawer } from "@material-ui/core";
import Fab from "@material-ui/core/Fab";
import { createStyles, Theme, WithStyles, withStyles } from "@material-ui/core/styles";
import LayersIcon from "@material-ui/icons/Layers";
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
      <div className="App">
        <div id={this.mapId}></div>
        {features.length > 0 && <FeatureInfo features={features} onClose={() => this.setState({ features: [] })} />}
        <Fab size="medium" color="primary" onClick={() => this.setState({ open: !open })} className={classes.mapButton}>
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
          {mapConfig && <LayerSwitcher mapConfig={mapConfig} onClose={() => this.setState({ open: false })} />}
        </Drawer>
      </div>
    );
  }
}

export default withStyles(styles)(App);
