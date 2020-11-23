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
  onSelectFeature: (feature: Feature) => void;
  onClose: () => void;
}

interface FeatureInfoState {
  featureIndex: number;
}

class FeatureInfo extends React.Component<FeatureInfoProps, FeatureInfoState> {
  constructor(props: FeatureInfoProps) {
    super(props);
    this.state = {
      featureIndex: 0,
    };
  }

  UNSAFE_componentWillReceiveProps() {
    this.setState({ featureIndex: 0 });
  }

  getAdminLink(feature: Feature) {
    const fid = feature["id"];
    const featureType = fid.split(".")[0];
    const featureId = feature["properties"]["id"];
    return `${APIBaseUrl}/admin/traffic_control/${featureType.replace(/_/g, "")}/${featureId}/change`;
  }

  render() {
    const { features, classes, onSelectFeature, onClose, t } = this.props;
    const { featureIndex } = this.state;
    const feature = features[featureIndex];
    onSelectFeature(feature);
    const fid = feature["id"];
    const featureType = fid.split(".")[0];
    const { id, value, txt, direction, device_type_code, device_type_description } = feature["properties"];
    const deviceTypeText = value
      ? `${device_type_code} - ${device_type_description} (${value})`
      : `${device_type_code} - ${device_type_description}`;

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
          </Typography>
        </CardContent>
        <CardActions>
          <Button onClick={onClose}>{t("close")}</Button>
          <Button color="primary" target="_blank" href={this.getAdminLink(feature)}>
            {t("edit")}
          </Button>
          <div className={classes.spacer}></div>
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
