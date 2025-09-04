import React, { useState } from "react";
import {
  TextField,
  Container,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  AppBar,
  Toolbar,
  IconButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import styles from "./AddressInput.module.css";
import { Address, getNameFromAddress } from "../common/AddressSearchUtils";
import { useTranslation } from "react-i18next";

interface AddressInputProps {
  readonly onSearch: (address: string) => void;
  readonly onSelect: (result: Address) => void;
  readonly onClose: () => void;
  readonly clearResults: () => void;
  readonly results: Address[];
}

function AddressInput({ onSearch, onSelect, onClose, clearResults, results }: AddressInputProps) {
  const { t } = useTranslation();
  const [address, setAddress] = useState<string | undefined>("");
  const [open, setOpen] = useState<boolean>(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setAddress(value);
    setSelectedIndex(-1);
    setOpen(true);
    // Only call onSearch if the length of the input value is 3 or more
    if (value.length >= 3) {
      onSearch(value);
    } else {
      clearResults();
    }
  };

  const handleSelect = (result: Address) => {
    setAddress(getNameFromAddress(result));
    onSelect(result);
    setOpen(false);
  };

  const handleFocus = () => {
    setOpen(true);
  };

  const handleBlur = () => {
    setTimeout(() => {
      setOpen(false);
    }, 200); // Small delay to allow click to register
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSelectedIndex((prevIndex) => Math.min(prevIndex + 1, results.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setSelectedIndex((prevIndex) => Math.max(prevIndex - 1, -1));
    } else if (event.key === "Enter" && selectedIndex >= 0) {
      event.preventDefault();
      handleSelect(results[selectedIndex]);
    } else if (event.key === "Tab") {
      // If there are results, prevent default behavior and focus the first list item
      if (results.length > 0) {
        event.preventDefault();
        setSelectedIndex(0); // Focus on the first itemkey=
      }
    }
  };

  return (
    <div>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Typography variant="h6" color="inherit">
            {t("Address search")}
          </Typography>
          <IconButton color="inherit" aria-label="close" onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Container className={styles.addressInputContainer}>
        <Box className="space-y-4">
          <TextField
            id="search-input"
            label={t("Address")}
            variant="outlined"
            fullWidth
            value={address}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={t("e.g. Vaasankatu 20")}
            className="rounded-lg"
          />
          {results.length > 0 && open && (
            <List dense>
              {results.map((result, index) => (
                <ListItem
                  key={result.name.en}
                  onClick={() => handleSelect(result)}
                  sx={{
                    cursor: "pointer",
                    backgroundColor: index === selectedIndex ? "#e0e0e0" : "transparent",
                  }}
                >
                  <ListItemText primary={getNameFromAddress(result)} />
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      </Container>
    </div>
  );
}

export default AddressInput;
