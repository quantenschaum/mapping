import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: {
    minify: "terser",
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
  },
  server: {
    // https: true,
    allowedHosts: true,
    headers: { "Cache-Control": "no-cache, no-store, must-revalidate" },
    proxy: {
      "/tiles": {
        target: "http://nas:5000",
        changeOrigin: true,
      },
    },
  },
});
