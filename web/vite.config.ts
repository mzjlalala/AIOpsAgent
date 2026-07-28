import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/ops": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/incident": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/workflows": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
