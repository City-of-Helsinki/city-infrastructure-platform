import { TextField, Theme } from "@mui/material";
import { createStyles, withStyles, WithStyles } from "@mui/styles";
import AppBar from "@mui/material/AppBar";
import Checkbox from "@mui/material/Checkbox";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import IconButton from "@mui/material/IconButton";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import CloseIcon from "@mui/icons-material/Close";
import React from "react";
import Map from "../common/Map";
import { MapConfig } from "../models";
import { withTranslation, WithTranslation } from "react-i18next";

const styles = (theme: Theme) =>
  createStyles({
    title: {
      flexGrow: 1,
    },
    layers: {
      padding: "16px",
    },
  });

interface LayerSwitcherProps extends WithStyles<typeof styles>, WithTranslation {
  mapConfig: MapConfig;
  onClose: () => void;
  onOverlayToggle: (checked: boolean) => void;
}

interface LayerSwitcherStates {
  visibleBasemap: string;
  visibleOverlays: {
    [identifier: string]: boolean;
  };
  displayRealPlanDifference: boolean;
  projectIdFilter: string;
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
      displayRealPlanDifference: true,
      projectIdFilter: "",
    };
  }

  renderBasemapGroup() {
    const { basemapConfig } = this.props.mapConfig;
    const { name, layers } = basemapConfig;
    const { visibleBasemap } = this.state;
    const basemapRadios = layers.map((layer) => (
      <FormControlLabel key={layer.identifier} control={<Radio />} label={layer.name} value={layer.identifier} />
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
    const { onOverlayToggle } = this.props;
    const { overlayConfig } = this.props.mapConfig;
    const { name, layers } = overlayConfig;
    const { visibleOverlays } = this.state;

    const changeOverlayVisibility = (event: React.ChangeEvent<HTMLInputElement>) => {
      const identifier = event.target.name;
      const checked = event.target.checked;
      onOverlayToggle(checked);
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

  renderSettings() {
    const { t } = this.props;
    const { overlayConfig } = this.props.mapConfig;
    const { displayRealPlanDifference } = this.state;

    const changeOverlayVisibility = (event: React.ChangeEvent<HTMLInputElement>) => {
      const checked: boolean = event.target.checked;
      Map.setExtraVectorLayerVisible(checked);
      this.setState({ displayRealPlanDifference: checked });
    };

    const changeProjectIdFilter = (event: React.ChangeEvent<HTMLInputElement>) => {
      const text: string = event.target.value || "";
      Map.applyProjectFilters(overlayConfig, text);
      this.setState({ projectIdFilter: text });
    };

    return (
      <div className="settings-group">
        <h4>{t("Settings")}</h4>
        <FormGroup>
          <FormControlLabel
            key={"real-plan-difference"}
            control={<Checkbox checked={displayRealPlanDifference} onChange={changeOverlayVisibility} />}
            label={t("Display Plan/Real difference")}
          />
        </FormGroup>
        <FormGroup>
          <TextField
            id="project-id-filter"
            label={t("Filter by Project")}
            variant={"standard"}
            onChange={changeProjectIdFilter}
          />
        </FormGroup>
      </div>
    );
  }

  render() {
    const { classes, onClose, t } = this.props;
    return (
      <div className="layer-switcher">
        <AppBar position="static" elevation={0}>
          <Toolbar>
            <Typography variant="h6" color="inherit" className={classes.title}>
              {t("Layers")}
            </Typography>
            <IconButton color="inherit" aria-label="close" onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
        <div className={classes.layers}>
          {this.renderBasemapGroup()}
          {this.renderOverlayGroup()}
          {this.renderSettings()}
        </div>
      </div>
    );
  }
}

export default withTranslation()(withStyles(styles)(LayerSwitcher));
