import React from "react";
import { Box, Typography, List, ListItem, CircularProgress } from "@mui/material";
import styles from "./OngoingFetchInfo.module.css";
import { useTranslation } from "react-i18next";

/**
 * A React functional component that displays strings from a Set in a
 * top-left corner box using Material-UI components.
 *
 * @param {object} props - The component's properties.
 * @param {Set<string>} props.stringSet - The Set of strings to display.
 */
const OngoingFetchInfo = ({ layerIdentifiers = new Set<string>() }) => {
  const { t } = useTranslation();
  return (
    // The main container for the display box, using Material-UI's Box component.
    // The 'sx' prop is used for styling, similar to inline styles but with theming support.
    <Box className={styles.ongoingFetchInfoContainer}>
      <Box sx={{ mb: 1 }}>
        <Typography variant="h6" component="h2">
          {t("Active data fetches")}:
        </Typography>
      </Box>
      {layerIdentifiers.size > 0 ? (
        <>
          <Box className={styles.centeredSpinner}>
            <CircularProgress size={24} sx={{ color: "primary.main" }} />
          </Box>
          <List dense>
            {/* dense makes the list items smaller */}
            {/* Iterate over the Set and render each string as a Material-UI ListItem. */}
            {Array.from(layerIdentifiers).map((str) => (
              <ListItem key={str} disablePadding>
                <Typography variant="body2">{str}</Typography>
              </ListItem>
            ))}
          </List>
        </>
      ) : (
        <Typography variant="body2" sx={{ fontStyle: "italic", color: "text.secondary" }}>
          {t("No active data fetches")}:
        </Typography>
      )}
    </Box>
  );
};

export default OngoingFetchInfo;
