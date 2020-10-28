import { createStyles, Theme, withStyles, WithStyles } from "@material-ui/core";
import AppBar from "@material-ui/core/AppBar";
import Checkbox from "@material-ui/core/Checkbox";
import FormControl from "@material-ui/core/FormControl";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import FormGroup from "@material-ui/core/FormGroup";
import IconButton from "@material-ui/core/IconButton";
import Radio from "@material-ui/core/Radio";
import RadioGroup from "@material-ui/core/RadioGroup";
import Toolbar from "@material-ui/core/Toolbar";
import Typography from "@material-ui/core/Typography";
import CloseIcon from "@material-ui/icons/Close";
import React from "react";
import Map from "../common/Map";
import { MapConfig } from "../models";

const styles = (theme: Theme) =>
  createStyles({
    title: {
      flexGrow: 1,
    },
    layers: {
      padding: "16px",
    },
  });

interface LayerSwitcherProps extends WithStyles<typeof styles> {
  mapConfig: MapConfig;
  onClose: () => void;
}

interface LayerSwitcherStates {
  visibleBasemap: string;
  visibleOverlays: {
    [identifier: string]: boolean;
  };
}

class LayerSwitcher extends React.Component<LayerSwitcherProps, LayerSwitcherStates> {
  constructor(props: LayerSwitcherProps) {
    super(props);
    const { basemapConfig, overlayConfig } = props.mapConfig;
    const visibleBasemap = basemapConfig.layers.length > 0 ? basemapConfig.layers[0].identifier : "";
    const visibleOverlays: { [identifier: string]: boolean } = {};
    overlayConfig.layers.forEach(({ identifier }) => {
      visibleOverlays[identifier] = false;
    });
    this.state = {
      visibleBasemap,
      visibleOverlays,
    };
  }

  renderBasemapGroup() {
    const { basemapConfig } = this.props.mapConfig;
    const { name, layers } = basemapConfig;
    const { visibleBasemap } = this.state;
    const basemapRadios = layers.map((layer) => (
      <FormControlLabel
        key={layer.identifier}
        control={<Radio />}
        label={layer.name}
        value={layer.identifier}
      ></FormControlLabel>
    ));
    const changeBasemap = (event: React.ChangeEvent<HTMLInputElement>) => {
      const basemap = (event.target as HTMLInputElement).value;
      Map.setVisibleBasemap(basemap);
      this.setState({ visibleBasemap: basemap });
    };
    return (
      <div className="basemap-group">
        <h4>{name}</h4>
        <FormControl component="fieldset">
          <RadioGroup aria-label="basemap" name="basemap" value={visibleBasemap} onChange={changeBasemap}>
            {basemapRadios}
          </RadioGroup>
        </FormControl>
      </div>
    );
  }

  renderOverlayGroup() {
    const { overlayConfig } = this.props.mapConfig;
    const { name, layers } = overlayConfig;
    const { visibleOverlays } = this.state;
    const changeOverlayVisibility = (event: React.ChangeEvent<HTMLInputElement>) => {
      const identifier = event.target.name;
      const checked = event.target.checked;
      visibleOverlays[identifier] = checked;
      Map.setOverlayVisible(identifier, checked);
      this.setState({ visibleOverlays });
    };
    const overlayCheckboxes = layers.map((layer) => (
      <FormControlLabel
        key={layer.identifier}
        control={
          <Checkbox
            checked={visibleOverlays[layer.identifier]}
            onChange={changeOverlayVisibility}
            name={layer.identifier}
          />
        }
        label={layer.name}
      />
    ));
    return (
      <div className="overlay-group">
        <h4>{name}</h4>
        <FormGroup>{overlayCheckboxes}</FormGroup>
      </div>
    );
  }

  render() {
    const { classes, onClose } = this.props;
    return (
      <div className="layer-switcher">
        <AppBar position="static" elevation={0}>
          <Toolbar>
            <Typography variant="h6" color="inherit" className={classes.title}>
              Layers
            </Typography>
            <IconButton color="inherit" aria-label="close" onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
        <div className={classes.layers}>
          {this.renderBasemapGroup()}
          {this.renderOverlayGroup()}
        </div>
      </div>
    );
  }
}

export default withStyles(styles)(LayerSwitcher);
