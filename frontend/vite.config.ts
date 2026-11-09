import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, /api is proxied to the local backend (uvicorn on port 8000).
// In production, nginx does the same (see nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
