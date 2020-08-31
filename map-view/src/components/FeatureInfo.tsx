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
  });

interface FeatureInfoProps extends WithStyles<typeof styles> {
  features: string[];
  onClose: () => void;
}

interface FeatureInfoStates {
  featureIndex: number;
}

class FeatureInfo extends React.Component<FeatureInfoProps, FeatureInfoStates> {
  constructor(props: FeatureInfoProps) {
    super(props);
    this.state = {
      featureIndex: 0,
    };
  }

  getAdminLink(feature: string) {
    const [featureType, featureId] = feature.split(".");
    return `${APIBaseUrl}/admin/traffic_control/${featureType.replace(/_/g, "")}/${featureId}/change`;
  }

  render() {
    const { features, onClose, classes } = this.props;
    const { featureIndex } = this.state;
    const feature = features[featureIndex];
    const [featureType, featureId] = feature.split(".");

    return (
      <Card className={classes.root}>
        <CardContent>
          <Typography className={classes.title} variant="h5" component="h2">
            {featureType.replace(/_/g, " ")}
          </Typography>
          <Typography color="textSecondary">{featureId}</Typography>
        </CardContent>
        <CardActions>
          <Button onClick={onClose}>Close</Button>
          <Button color="primary" target="_blank" href={this.getAdminLink(feature)}>
            Edit
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

export default withStyles(styles)(FeatureInfo);
