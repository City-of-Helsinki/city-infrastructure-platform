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
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  InputLabel,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import CloseIcon from "@mui/icons-material/Close";
import React, { useState } from "react";
import Map from "../common/Map";
import { IconSize, MapConfig } from "../models";
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
  onOverlayToggle: (checked: boolean, diffLayerIdentifier: string, layerIdentifier: string) => void;
  iconScale: number;
  iconType: string;
  iconSize: IconSize;
  onIconScaleChange: (scale: number) => void;
  onIconTypeChange: (type: string) => void;
  onIconSizeChange: (size: IconSize) => void;
  onResetIconSettings: () => void;
}

const LayerSwitcher = ({
  mapConfig,
  onClose,
  onOverlayToggle,
  iconScale,
  iconType,
  iconSize,
  onIconScaleChange,
  onIconTypeChange,
  onIconSizeChange,
  onResetIconSettings,
}: LayerSwitcherProps) => {
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
  const [resetDialogOpen, setResetDialogOpen] = useState<boolean>(false);
  const [iconScaleInput, setIconScaleInput] = useState<string>(iconScale.toString());

  // Sync iconScaleInput with iconScale prop when it changes
  React.useEffect(() => {
    setIconScaleInput(iconScale.toString());
  }, [iconScale]);

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
      setVisibleOverlays((prev) => ({
        ...prev,
        [identifier]: checked,
      }));
      Map.setOverlayVisible(identifier, checked);
      onOverlayToggle(checked, getDiffLayerIdentifierFromLayerIdentifier(identifier), identifier);
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

    const handleIconScaleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      setIconScaleInput(value);

      const numValue = Number.parseFloat(value);
      if (!Number.isNaN(numValue) && numValue >= 0.01 && numValue <= 2) {
        onIconScaleChange(numValue);
      }
    };

    const handleIconScaleBlur = () => {
      const numValue = Number.parseFloat(iconScaleInput);
      if (Number.isNaN(numValue) || numValue < 0.01 || numValue > 2) {
        // Reset to current valid value
        setIconScaleInput(iconScale.toString());
      }
    };

    const handleIconTypeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      onIconTypeChange(event.target.value);
    };

    const handleIconSizeChange = (event: any) => {
      onIconSizeChange(event.target.value as IconSize);
    };

    const handleResetClick = () => {
      setResetDialogOpen(true);
    };

    const handleResetConfirm = () => {
      onResetIconSettings();
      setResetDialogOpen(false);
    };

    const handleResetCancel = () => {
      setResetDialogOpen(false);
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

        <h4>{t("Icon Settings")}</h4>
        <FormGroup>
          <TextField
            id="icon-scale"
            label={t("Icon Scale")}
            variant={"standard"}
            type="number"
            value={iconScaleInput}
            onChange={handleIconScaleChange}
            onBlur={handleIconScaleBlur}
            inputProps={{ min: 0.01, max: 2, step: 0.01 }}
            helperText={t("Range: 0.01 - 2")}
          />
        </FormGroup>

        <FormGroup>
          <Typography variant="body2" style={{ marginTop: "16px", marginBottom: "8px" }}>
            {t("Icon Type")}
          </Typography>
          <RadioGroup value={iconType} onChange={handleIconTypeChange}>
            <FormControlLabel value="svg" control={<Radio />} label="SVG" />
            <FormControlLabel value="png" control={<Radio />} label="PNG" />
          </RadioGroup>
        </FormGroup>

        <FormGroup style={{ marginTop: "16px" }}>
          <FormControl variant="standard" fullWidth>
            <InputLabel id="icon-size-label">{t("Icon Size (PNG)")}</InputLabel>
            <Select labelId="icon-size-label" id="icon-size" value={iconSize} onChange={handleIconSizeChange}>
              <MenuItem value={32}>32</MenuItem>
              <MenuItem value={64}>64</MenuItem>
              <MenuItem value={128}>128</MenuItem>
              <MenuItem value={256}>256</MenuItem>
            </Select>
          </FormControl>
        </FormGroup>

        <FormGroup style={{ marginTop: "16px" }}>
          <Button variant="outlined" color="primary" onClick={handleResetClick}>
            {t("Reset to Defaults")}
          </Button>
        </FormGroup>

        <Dialog
          open={resetDialogOpen}
          onClose={handleResetCancel}
          aria-labelledby="reset-dialog-title"
          aria-describedby="reset-dialog-description"
        >
          <DialogTitle id="reset-dialog-title">{t("Reset Icon Settings")}</DialogTitle>
          <DialogContent>
            <DialogContentText id="reset-dialog-description">
              {t("Are you sure you want to reset all icon settings to their default values from the server?")}
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleResetCancel} color="primary">
              {t("Cancel")}
            </Button>
            <Button onClick={handleResetConfirm} color="primary" autoFocus>
              {t("Reset")}
            </Button>
          </DialogActions>
        </Dialog>
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
