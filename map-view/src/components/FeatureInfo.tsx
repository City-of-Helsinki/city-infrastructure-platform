import { createStyles, Theme, withStyles, WithStyles } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import Typography from "@material-ui/core/Typography";
import NavigateBefore from "@material-ui/icons/NavigateBefore";
import NavigateNext from "@material-ui/icons/NavigateNext";
import React from "react";
import { APIBaseUrl } from "../consts";
import { Feature } from "../models";
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
  onSelectFeature: (feature: Feature) => Promise<any>;
  onClose: () => void;
}

interface FeatureInfoState {
  featureIndex: number;
  realPlanDistance?: number;
}

class FeatureInfo extends React.Component<FeatureInfoProps, FeatureInfoState> {
  constructor(props: FeatureInfoProps) {
    super(props);
    this.state = {
      featureIndex: 0,
      realPlanDistance: undefined,
    };
  }

  UNSAFE_componentWillReceiveProps() {
    this.setState({ featureIndex: 0, realPlanDistance: undefined });
  }

  getAdminLink(feature: Feature) {
    const app_name = feature["app_name"];
    const fid = feature["id_"];
    const featureType = fid.split(".")[0];
    const featureId = feature.getProperties().id;
    return `${APIBaseUrl}/admin/${app_name}/${featureType.replace(/_/g, "")}/${featureId}/change`;
  }

  render() {
    const { features, classes, onSelectFeature, onClose, t } = this.props;
    const { featureIndex } = this.state;
    const feature = features[featureIndex];
    const fid = feature["id_"];
    const featureType = fid.split(".")[0];
    const { id, value, txt, direction, device_type_code } = feature.getProperties();
    const deviceTypeText = value ? `${device_type_code} (${value})` : `${device_type_code}`;

    if (this.state.realPlanDistance === undefined) {
      onSelectFeature(feature).then((distance: number) => this.setState({ realPlanDistance: distance }));
    }

    return (
      <Card className={classes.root}>
        <CardContent>
          <Typography className={classes.title} variant="h5" component="h2">
            {t(`featureInfoTitle.${featureType}`)}
          </Typography>
          <Typography className={classes.content} variant="body1" component="p">
            <b>Id</b>: {id}
            <br />
            <b>{t("Device type")}</b>: {deviceTypeText}
            <br />
            <b>{t("Direction")}</b>: {direction}
            <br />
            <b>{t("Additional info")}</b>: {txt}
            {feature.getProperties().device_plan_id && (
              <>
                <br />
                <b>{t("Distance")}</b>: {this.state.realPlanDistance} m
              </>
            )}
          </Typography>
        </CardContent>
        <CardActions>
          <Button onClick={onClose}>{t("close")}</Button>
          <Button color="primary" target="_blank" href={this.getAdminLink(feature)}>
            {t("edit")}
          </Button>
          <div className={classes.spacer} />
          <Typography color="textSecondary">
            {featureIndex + 1} / {features.length}
          </Typography>
          <IconButton
            color="primary"
            disabled={featureIndex === 0}
            onClick={() => this.setState({ featureIndex: featureIndex - 1 })}
          >
            <NavigateBefore />
          </IconButton>
          <IconButton
            color="primary"
            disabled={featureIndex === features.length - 1}
            onClick={() => this.setState({ featureIndex: featureIndex + 1 })}
          >
            <NavigateNext />
          </IconButton>
        </CardActions>
      </Card>
    );
  }
}

export default withTranslation()(withStyles(styles)(FeatureInfo));
