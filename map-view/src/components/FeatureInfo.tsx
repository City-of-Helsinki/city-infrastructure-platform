import { Theme } from "@mui/material";
import { createStyles, withStyles, WithStyles } from "@mui/styles";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardActions from "@mui/material/CardActions";
import CardContent from "@mui/material/CardContent";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import NavigateBefore from "@mui/icons-material/NavigateBefore";
import NavigateNext from "@mui/icons-material/NavigateNext";
import React from "react";
import { APIBaseUrl } from "../consts";
import { Feature, MapConfig } from "../models";
import { withTranslation, WithTranslation } from "react-i18next";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      position: "absolute",
      bottom: "8px",
      left: 0,
      right: 0,
      marginLeft: "auto",
      marginRight: "auto",
      width: "480px",
    },
    title: {
      textTransform: "capitalize",
    },
    spacer: {
      flexGrow: 1,
    },
    content: {
      marginTop: "10px",
    },
  });

interface FeatureInfoProps extends WithStyles<typeof styles>, WithTranslation {
  features: Feature[];
  mapConfig: MapConfig;
  onSelectFeature: (feature: Feature) => Promise<any>;
  onClose: () => void;
}

interface FeatureInfoState {
  featureIndex: number;
  realPlanDistance?: number;
  features: Feature[];
}

class FeatureInfo extends React.Component<FeatureInfoProps, FeatureInfoState> {
  constructor(props: FeatureInfoProps) {
    super(props);
    this.state = {
      featureIndex: 0,
      realPlanDistance: undefined,
      features: props.features,
    };
  }

  static getDerivedStateFromProps(props: FeatureInfoProps, state: FeatureInfoState) {
    if (props.features !== state.features) {
      return { featureIndex: 0, realPlanDistance: undefined, features: props.features };
    }
    return null;
  }

  getFeatureType(feature: Feature) {
    const fid = feature["id_"];
    return fid.split(".")[0];
  }

  getFeatureTypeEditName(featureType: string, featureTypeEditMapping: Record<string, string>) {
    return featureTypeEditMapping[featureType] || featureType;
  }

  getAdminLink(feature: Feature, featureTypeEditMapping: Record<string, string>) {
    const app_name = feature["app_name"];
    const featureTypeEditName = this.getFeatureTypeEditName(this.getFeatureType(feature), featureTypeEditMapping);
    const featureId = feature.getProperties().id;
    return `${APIBaseUrl}/admin/${app_name}/${featureTypeEditName.replace(/_/g, "")}/${featureId}/change`;
  }

  runOnSelectFeature(featureIndex: number) {
    const { features, onSelectFeature } = this.props;
    const feature = features[featureIndex];
    onSelectFeature(feature).then((distance: number) => this.setState({ realPlanDistance: distance }));
  }

  setFeatureIndex(featureIndex: number) {
    this.setState({ featureIndex: featureIndex });
    this.runOnSelectFeature(featureIndex);
  }

  render() {
    const { features, classes, onClose, t, mapConfig } = this.props;
    const { featureIndex } = this.state;
    const feature = features[featureIndex];

    const fid = feature["id_"];
    const featureType = fid.split(".")[0];
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

    // Only run when distance is undefined (don't spam requests)
    if (this.state.realPlanDistance === undefined) {
      this.runOnSelectFeature(featureIndex);
    }

    return (
      <Card className={classes.root}>
        <CardContent>
          <Typography className={classes.title} variant="h5" component="h2">
            {t(`featureInfoTitle.${featureType}`)}
          </Typography>
          <Typography className={classes.content} variant="body1" component="p">
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
            <br />
            <b>{t("Additional info")}</b>: {txt || additional_information}
            {content_s && (
              <>
                <br />
                <b>{t("Content Schema")}</b>: {JSON.stringify(content_s)}
              </>
            )}
            {feature.getProperties().device_plan_id && (
              <>
                <br />
                <b>{t("Distance to plan")}</b>: {this.state.realPlanDistance} m
              </>
            )}
          </Typography>
        </CardContent>
        <CardActions>
          <Button onClick={onClose}>{t("close")}</Button>
          <Button
            color="primary"
            target="_blank"
            href={this.getAdminLink(feature, mapConfig.featureTypeEditNameMapping)}
          >
            {t("edit")}
          </Button>
          <div className={classes.spacer} />
          <Typography color="textSecondary">
            {featureIndex + 1} / {features.length}
          </Typography>
          <IconButton
            color="primary"
            disabled={featureIndex === 0}
            onClick={() => this.setFeatureIndex(featureIndex - 1)}
          >
            <NavigateBefore />
          </IconButton>
          <IconButton
            color="primary"
            disabled={featureIndex === features.length - 1}
            onClick={() => this.setFeatureIndex(featureIndex + 1)}
          >
            <NavigateNext />
          </IconButton>
        </CardActions>
      </Card>
    );
  }
}

export default withTranslation()(withStyles(styles)(FeatureInfo));
