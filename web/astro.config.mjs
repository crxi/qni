import { defineConfig } from "astro/config";
import yaml from "@rollup/plugin-yaml";
import sitemap from "@astrojs/sitemap";

// Deployed to Cloudflare Pages at https://qni.pages.dev, served from the
// root. `site` drives absolute URLs (sitemap, og:url); `base` is "/".
// (The old GitHub Pages deployment is now just a static redirect to
// qni.pages.dev, so no subpath build is needed.)
export default defineConfig({
  site: "https://qni.pages.dev",
  base: "/",
  integrations: [sitemap()],
  vite: {
    plugins: [yaml()],
    server: {
      allowedHosts: [".trycloudflare.com"],
    },
  },
  build: {
    inlineStylesheets: "always",
  },
});
