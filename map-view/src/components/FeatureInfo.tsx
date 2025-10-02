import { Button, Card, CardActions, CardContent, IconButton, Typography, Divider } from "@mui/material";
import { styled } from "@mui/material/styles";
import NavigateBefore from "@mui/icons-material/NavigateBefore";
import NavigateNext from "@mui/icons-material/NavigateNext";
import CloseIcon from "@mui/icons-material/Close";
import React, { useState, useEffect, useCallback } from "react";
import { APIBaseUrl } from "../consts";
import { Feature, FeatureProperties, MapConfig } from "../models";
import { useTranslation } from "react-i18next";
import { getFeatureAppName, getFeatureLayerExtraInfoFields, getFeatureLayerName } from "../common/MapUtils";

const StyledCard = styled(Card)(() => ({
  position: "absolute",
  bottom: "8px",
  left: 0,
  right: 0,
  marginLeft: "auto",
  marginRight: "auto",
  width: "480px",
}));

const TitleTypography = styled(Typography)(() => ({
  textTransform: "capitalize",
}));

const ContentTypography = styled(Typography)(() => ({
  marginTop: "10px",
}));

const Spacer = styled("div")(() => ({
  flexGrow: 1,
}));

interface FeatureInfoProps {
  features: Feature[];
  mapConfig: MapConfig;
  onSelectFeatureShowPlan: (feature: Feature) => Promise<any>;
  onSelectFeatureHighLight: (feature: Feature) => void;
  onClose: () => void;
}

const FeatureInfo = ({
  features,
  mapConfig,
  onSelectFeatureShowPlan,
  onSelectFeatureHighLight,
  onClose,
}: FeatureInfoProps) => {
  const [featureIndex, setFeatureIndex] = useState<number>(0);
  const [realPlanDistance, setRealPlanDistance] = useState<number | undefined>(undefined);
  const { t } = useTranslation();

  // Reset state when features prop changes
  useEffect(() => {
    // Check if the current index is out of bounds for the new features array
    if (featureIndex >= features.length && features.length > 0) {
      // If out of bounds, reset to 0
      setFeatureIndex(0);
    } else if (features.length === 0) {
      // If features is empty, reset index and distance
      setFeatureIndex(0);
      setRealPlanDistance(undefined);
    }
  }, [features, featureIndex]);

  const runOnSelectFeature = useCallback(
    (index: number) => {
      const feature = features[index];
      if (!feature) {
        console.warn(`Attempted to select feature at invalid index ${index}. Skipping.`);
        return;
      }
      onSelectFeatureShowPlan(feature).then((distance: number) => distance && setRealPlanDistance(distance));
      onSelectFeatureHighLight(feature);
    },
    [features, onSelectFeatureShowPlan, onSelectFeatureHighLight, setRealPlanDistance],
  );

  const setFeatureIndexAndRunSelect = (index: number) => {
    setFeatureIndex(index);
    runOnSelectFeature(index);
  };

  // Run on initial render or when the featureIndex changes
  useEffect(() => {
    if (features.length > 0 && realPlanDistance === undefined) {
      runOnSelectFeature(featureIndex);
    }
  }, [features, featureIndex, realPlanDistance, runOnSelectFeature]);

  const getFeatureType = (feature: Feature) => {
    const fid = feature["id_"];
    return fid.split(".")[0];
  };

  const getFeatureTypeEditName = (featureType: string, featureTypeEditMapping: Record<string, string>) => {
    return featureTypeEditMapping[featureType] || featureType;
  };

  const getAdminLink = (feature: Feature, featureTypeEditMapping: Record<string, string>) => {
    const app_name = getFeatureAppName(feature, mapConfig.overlayConfig);
    const featureTypeEditName = getFeatureTypeEditName(getFeatureType(feature), featureTypeEditMapping);
    const featureId = feature.getProperties().id;
    return `${APIBaseUrl}/admin/${app_name}/${featureTypeEditName.replace(/_/g, "")}/${featureId}/change`;
  };

  const getFeatureInfoTitle = (feature: Feature) => {
    return getFeatureLayerName(feature, mapConfig.overlayConfig);
  };

  const renderCommonFields = (feature: Feature) => {
    const {
      id,
      value,
      txt,
      direction,
      device_type_code,
      device_type_description,
      mount_type_description_fi,
      content_s,
      additional_information,
    } = feature.getProperties();
    const deviceTypeText = `${device_type_code} - ${device_type_description}${value ? ` (${value})` : ""}`;
    const additionalInfoText = txt || additional_information;

    return (
      <>
        <b>Id</b>: {id}
        {device_type_code && (
          <>
            <br />
            <b>{t("Device type")}</b>: {deviceTypeText}
          </>
        )}
        {mount_type_description_fi && !device_type_code && (
          <>
            <br />
            <b>{t("Mount type")}</b>: {mount_type_description_fi}
          </>
        )}
        {direction && (
          <>
            <br />
            <b>{t("Direction")}</b>: {direction}
          </>
        )}
        {additionalInfoText && (
          <>
            <br />
            <b>{t("Additional info")}</b>: {additionalInfoText}
          </>
        )}
        {content_s && (
          <>
            <br />
            <b>{t("Content Schema")}</b>: {JSON.stringify(content_s)}
          </>
        )}
        {feature.getProperties().device_plan_id && (
          <>
            <br />
            <b>{t("Distance to plan")}</b>: {realPlanDistance} m
          </>
        )}
      </>
    );
  };

  const renderFeatureSpecificFields = (feature: Feature, mapConfig: MapConfig) => {
    const extra_fields = getFeatureLayerExtraInfoFields(feature, mapConfig.overlayConfig);
    if (extra_fields) {
      return (
        <>
          {Object.entries(extra_fields)
            .sort((a, b) => {
              return a[1].order - b[1].order || a[1].title.localeCompare(b[1].title);
            })
            .map(([key, value]) => (
              <React.Fragment key={key}>
                <br />
                <b>{value.title}</b>: {JSON.stringify(feature.getProperties()[key as keyof FeatureProperties])}{" "}
              </React.Fragment>
            ))}
        </>
      );
    } else {
      return <></>;
    }
  };

  if (!features || features.length === 0) {
    return null;
  }

  const feature = features[featureIndex] || features[0];

  return (
    <StyledCard>
      <CardContent>
        <TitleTypography variant="h5" as="h2">
          {getFeatureInfoTitle(feature)}
          <IconButton onClick={onClose} sx={{ float: "right" }}>
            <CloseIcon />
          </IconButton>
        </TitleTypography>
        <Divider sx={{ my: 1 }} />
        <ContentTypography variant="body1" as="p">
          {renderCommonFields(feature)}
        </ContentTypography>
        <ContentTypography variant="body1" as="p">
          {renderFeatureSpecificFields(feature, mapConfig)}
        </ContentTypography>
      </CardContent>
      <CardActions>
        <Button onClick={onClose}>{t("close")}</Button>
        <Button color="primary" target="_blank" href={getAdminLink(feature, mapConfig.featureTypeEditNameMapping)}>
          {t("edit")}
        </Button>
        <Spacer />
        <Typography color="textSecondary">
          {featureIndex + 1} / {features.length}
        </Typography>
        <IconButton
          color="primary"
          disabled={featureIndex === 0}
          onClick={() => setFeatureIndexAndRunSelect(featureIndex - 1)}
        >
          <NavigateBefore />
        </IconButton>
        <IconButton
          color="primary"
          disabled={featureIndex === features.length - 1}
          onClick={() => setFeatureIndexAndRunSelect(featureIndex + 1)}
        >
          <NavigateNext />
        </IconButton>
      </CardActions>
    </StyledCard>
  );
};

export default FeatureInfo;
