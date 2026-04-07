import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    target: "es2015",
    cssTarget: "chrome61",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          hls: ["hls.js"],
          webauthn: ["@simplewebauthn/browser"],
        },
      },
    },
  },
});
