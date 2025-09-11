import {
  TextField,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormGroup,
  IconButton,
  Radio,
  RadioGroup,
  Toolbar,
  Typography,
  AppBar,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import CloseIcon from "@mui/icons-material/Close";
import React, { useState } from "react";
import Map from "../common/Map";
import { MapConfig } from "../models";
import { useTranslation } from "react-i18next";
import { getDiffLayerIdentifierFromLayerIdentifier } from "../common/MapUtils";

const StyledAppBar = styled(AppBar)({
  position: "static",
  elevation: 0,
});

const StyledToolbar = styled(Toolbar)({
  minHeight: "auto !important",
});

const StyledTitleTypography = styled(Typography)({
  flexGrow: 1,
});

const StyledLayersDiv = styled("div")({
  padding: "16px",
});

interface LayerSwitcherProps {
  mapConfig: MapConfig;
  onClose: () => void;
  onOverlayToggle: (checked: boolean, diffLayerIdentifier: string) => void;
}

const LayerSwitcher = ({ mapConfig, onClose, onOverlayToggle }: LayerSwitcherProps) => {
  const { t } = useTranslation();
  const { basemapConfig, overlayConfig } = mapConfig;

  const [visibleBasemap, setVisibleBasemap] = useState<string>(
    basemapConfig.layers.length > 0 ? basemapConfig.layers[0].identifier : "",
  );
  const [visibleOverlays, setVisibleOverlays] = useState<{ [identifier: string]: boolean }>(() => {
    const overlays: { [identifier: string]: boolean } = {};
    overlayConfig.layers.forEach(({ identifier }) => {
      overlays[identifier] = false;
    });
    return overlays;
  });
  const [displayRealPlanDifference, setDisplayRealPlanDifference] = useState<boolean>(true);

  const renderBasemapGroup = () => {
    const { name, layers } = basemapConfig;
    const changeBasemap = (event: React.ChangeEvent<HTMLInputElement>) => {
      const basemap = event.target.value;
      Map.setVisibleBasemap(basemap);
      setVisibleBasemap(basemap);
    };

    return (
      <div className="basemap-group">
        <h4>{name}</h4>
        <FormControl component="fieldset">
          <RadioGroup aria-label="basemap" name="basemap" value={visibleBasemap} onChange={changeBasemap}>
            {layers.map((layer) => (
              <FormControlLabel
                key={layer.identifier}
                control={<Radio />}
                label={layer.name}
                value={layer.identifier}
              />
            ))}
          </RadioGroup>
        </FormControl>
      </div>
    );
  };

  const renderOverlayGroup = () => {
    const { name, layers } = overlayConfig;

    const changeOverlayVisibility = (event: React.ChangeEvent<HTMLInputElement>) => {
      const identifier = event.target.name;
      const checked = event.target.checked;
      onOverlayToggle(checked, getDiffLayerIdentifierFromLayerIdentifier(identifier));
      setVisibleOverlays((prev) => ({
        ...prev,
        [identifier]: checked,
      }));
      Map.setOverlayVisible(identifier, checked);
    };

    return (
      <div className="overlay-group">
        <h4>{name}</h4>
        <FormGroup>
          {layers.map((layer) => (
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
          ))}
        </FormGroup>
      </div>
    );
  };

  const renderSettings = () => {
    const changeOverlayVisibility = (event: React.ChangeEvent<HTMLInputElement>) => {
      const checked = event.target.checked;
      Map.setPlanRealDiffVectorLayersVisible(checked);
      setDisplayRealPlanDifference(checked);
    };

    const changeProjectIdFilter = (event: React.ChangeEvent<HTMLInputElement>) => {
      const text = event.target.value || "";
      Map.applyProjectFilters(overlayConfig, text);
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
  };

  return (
    <div className="layer-switcher">
      <StyledAppBar elevation={0}>
        <StyledToolbar>
          <StyledTitleTypography variant="h6" color="inherit">
            {t("Layers")}
          </StyledTitleTypography>
          <IconButton color="inherit" aria-label="close" onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </StyledToolbar>
      </StyledAppBar>
      <StyledLayersDiv>
        {renderBasemapGroup()}
        {renderOverlayGroup()}
        {renderSettings()}
      </StyledLayersDiv>
    </div>
  );
};

export default LayerSwitcher;
