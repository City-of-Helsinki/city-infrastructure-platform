import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import eslint from "vite-plugin-eslint";

export default defineConfig(() => {
  return {
    build: {
      outDir: "build",
      assetsDir: "static",
    },
    plugins: [react(), eslint()],
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "src/setupTests.js",
    },
  };
});
