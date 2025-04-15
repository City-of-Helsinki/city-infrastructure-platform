import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { StyledEngineProvider } from "@mui/material/styles";

import "./i18n"; // needs to be bundled

const container = document.getElementById("root");
const root = createRoot(container!);
root.render(
  <StyledEngineProvider injectFirst>
    <App />
  </StyledEngineProvider>,
);
