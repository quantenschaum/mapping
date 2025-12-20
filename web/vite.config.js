import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "freenauticalchart",
        short_name: "QMAP",
        description: "free nautical chart based on open data",
        start_url: "/",
        display: "standalone",
        background_color: "#F9ECC0",
        theme_color: "#3a65ff",
        orientation: "any",
        icons: [
          {
            src: "icon1.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "icon1m.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "maskable",
          },
          {
            src: "icon5.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "icon5m.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
          {
            src: "icon.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any",
          },
        ],
      },
      workbox: {
        navigateFallback: "/index.html",
        navigateFallbackAllowlist: [/^\/$/],
        ignoreURLParametersMatching: [/.*/],
        // maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        runtimeCaching: [
          {
            urlPattern:
              /\/download.*(html|js|xml|webp|png|svg|jpe?g|json|css|\/)$/,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "assets",
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 7 * 24 * 3600, // 7 days
              },
            },
          },
          {
            urlPattern: /\/(tides|forecast|wattsegler)\//,
            handler: "NetworkFirst",
            options: {
              cacheName: "tides",
              networkTimeoutSeconds: 10,
              expiration: {
                maxEntries: 1000,
                maxAgeSeconds: 7 * 24 * 3600,
              },
            },
          },
          {
            urlPattern: /\.(webp|pbf|json)$/,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "tiles",
              expiration: {
                maxEntries: 20000,
                maxAgeSeconds: 7 * 24 * 3600,
                purgeOnQuotaError: true,
              },
            },
          },
        ],
      },
    }),
  ],
  build: {
    minify: "terser",
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
  },
  optimizeDeps: {
    exclude: ["leaflet.control.opacity"],
  },
  server: {
    // https: true,
    headers: { "Cache-Control": "no-cache, no-store, must-revalidate" },
    proxy: {
      "^/(qmap-de|qmap-nl|download|bfs|nfs)/.*": {
        target: "https://freenauticalchart.net",
        changeOrigin: true,
      },
      "^.*\.pmtiles$": {
        target: "https://freenauticalchart.net",
        changeOrigin: true,
      },
      "^/updated$": {
        target: "https://freenauticalchart.net",
        changeOrigin: true,
      },
      "/tides/de": {
        target: "https://gezeiten.bsh.de",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/tides\/de/, ""),
      },
      "/forecast/de": {
        target: "https://wasserstand-nordsee.bsh.de",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/forecast\/de/, ""),
      },
      "/forecast/balt": {
        target: "https://www2.bsh.de",
        changeOrigin: true,
        rewrite: (path) =>
          path.replace(
            /^\/forecast\/balt/,
            "/aktdat/wvd/ostsee/pegelkurve/de/figures",
          ),
      },
      "/tides/nl": {
        target: "https://waterinfo.rws.nl",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/tides\/nl/, ""),
      },
      "/tides/uk": {
        target: "https://easytide.admiralty.co.uk/Home/",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/tides\/uk/, ""),
      },
      "/tides/fr": {
        target: "https://services.data.shom.fr",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/tides\/fr/, ""),
        configure: (proxy, options) => {
          proxy.on("proxyReq", (proxyReq, req, res) => {
            proxyReq.setHeader("Referer", "https://maree.shom.fr/");
          });
        },
      },
      "/wattsegler": {
        target: "https://www.wattsegler.de",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/wattsegler/, ""),
      },
      "/brightsky": {
        target: "https://api.brightsky.dev",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/brightsky/, ""),
      },
    },
  },
});
