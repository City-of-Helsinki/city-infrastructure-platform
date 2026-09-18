import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";
import { defineConfig } from "eslint/config";

export default defineConfig({
  files: ["**/*.{js,mjs,cjs,ts,mts,cts,jsx,tsx}"],
  ignores: ["build/**"],
  plugins: { js },
  extends: ["js/recommended", tseslint.configs.recommended, pluginReact.configs.flat.recommended],
  languageOptions: {
    globals: globals.browser,
  },
  rules: {
    "@typescript-eslint/no-explicit-any": 1, // Set to warning
    "@typescript-eslint/no-unused-vars": 1, // Set to warning
  },
  settings: {
    react: {
      version: "19",
    },
  },
});
