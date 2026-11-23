import { Alert, Box, Button, IconButton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import React from "react";
import { useTranslation } from "react-i18next";
import styles from "./InspectBanner.module.css";

export type InspectStatus = "found" | "notFound";

interface InspectBannerProps {
  status: InspectStatus;
  /** Display name of the inspected feature's layer */
  layerName: string;
  /** Leave inspect mode and show the inspected feature's layer */
  onShowLayer: () => void;
  /** Leave inspect mode without changing layers */
  onClose: () => void;
}

/**
 * Banner shown at the top of the map when a single feature is inspected (map opened from a Django admin edit page)
 */
const InspectBanner = ({ status, layerName, onShowLayer, onClose }: InspectBannerProps) => {
  const { t } = useTranslation();
  const found = status === "found";

  return (
    <Box className={styles.inspectBannerContainer}>
      <Alert
        severity={found ? "info" : "warning"}
        action={
          <>
            {found && (
              <Button color="inherit" size="small" onClick={onShowLayer}>
                {t("Show all features in this layer")}
              </Button>
            )}
            <IconButton color="inherit" size="small" aria-label={t("close")} onClick={onClose}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </>
        }
      >
        {found ? (
          <>
            {t("Inspecting a single feature")}: <b>{layerName}</b>
          </>
        ) : (
          t("Inspected feature not found")
        )}
      </Alert>
    </Box>
  );
};

export default InspectBanner;
