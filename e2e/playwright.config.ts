import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: "http://localhost:12000",
    headless: true,
    navigationTimeout: 15_000,
    // Don't block on external CDN resources (fonts, icons)
    launchOptions: {
      args: ["--disable-web-security"],
    },
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
