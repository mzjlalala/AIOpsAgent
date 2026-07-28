import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

function sseProxyConfigure(proxy: { on: (event: string, listener: (...args: any[]) => void) => void }) {
  proxy.on("proxyRes", (proxyRes: { headers: Record<string, string | string[] | undefined> }) => {
    if (String(proxyRes.headers["content-type"] || "").includes("text/event-stream")) {
      proxyRes.headers["cache-control"] = "no-cache";
      proxyRes.headers["x-accel-buffering"] = "no";
    }
  });
}

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/ops": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        configure: sseProxyConfigure as never,
      },
      "/chat": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        configure: sseProxyConfigure as never,
      },
      "/incident": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        configure: sseProxyConfigure as never,
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
