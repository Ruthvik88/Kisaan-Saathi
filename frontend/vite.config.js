import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "apple-touch-icon.png"],
      manifest: {
        name: "Kisan Saathi",
        short_name: "Kisan Saathi",
        description:
          "Voice assistant for Indian farmers — ask farming questions in your language",
        theme_color: "#2d5a27",
        background_color: "#fbf9f5",
        display: "standalone",
        orientation: "portrait",
        start_url: "/",
        scope: "/",
        icons: [
          {
            src: "icons/icon-192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "icons/icon-512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            src: "icons/icon-512-maskable.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        runtimeCaching: [
          {
            // Cache ONLY the app shell ("/") with NetworkFirst.
            // Do NOT cache /ask or any backend API endpoint — API
            // responses must always be live, never a stale cached
            // voice answer that would mislead a farmer.
            urlPattern: /^\/$/,
            handler: "NetworkFirst",
            options: {
              cacheName: "app-shell",
            },
          },
        ],
      },
    }),
  ],
});
