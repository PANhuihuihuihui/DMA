import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = process.env.LOCALPILOT_API_URL || "http://127.0.0.1:8790";

export default defineConfig({
  plugins: [react()],
  server: {
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin-allow-popups",
    },
    proxy: {
      "/api/v1": {
        target: apiTarget,
        changeOrigin: true,
        timeout: 120000,
        proxyTimeout: 120000,
      },
    },
  },
});
