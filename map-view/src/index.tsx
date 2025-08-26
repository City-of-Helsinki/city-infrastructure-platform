import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { StyledEngineProvider } from "@mui/material/styles";
import { I18nextProvider } from "react-i18next";
import i18n from "./i18n";

const container = document.getElementById("root");
const root = createRoot(container!);
root.render(
  <StyledEngineProvider injectFirst>
    <I18nextProvider i18n={i18n}>
      <App />
    </I18nextProvider>
  </StyledEngineProvider>,
);
