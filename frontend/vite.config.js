import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const pkg = JSON.parse(
  readFileSync(fileURLToPath(new URL("./package.json", import.meta.url)), "utf-8")
);

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    target: "es2015",
    cssTarget: "chrome61",
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // vite 8's rolldown bundler requires manualChunks as a function,
        // not the rollup-era object-of-arrays form.
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          if (id.includes("/react/") || id.includes("/react-dom/")) return "vendor";
          if (id.includes("/hls.js/")) return "hls";
          if (id.includes("/@simplewebauthn/browser/")) return "webauthn";
          if (id.includes("/maplibre-gl/")) return "maplibre";
        },
      },
    },
  },
});
