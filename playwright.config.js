// Visual regression config (spec FR-005, FR-006).
//
// Always run this through `make visual`, which executes it inside the pinned
// mcr.microsoft.com/playwright:v1.62.1-noble container. Screenshots are only comparable
// when font rendering is identical, so the container is not a convenience — it is what
// makes CI and a developer machine agree (spec: US2 acceptance scenario 4).
const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests/visual",
  // A screenshot difference is a real failure; retrying would only mask flakiness (NFR-002).
  retries: 0,
  workers: 1,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  outputDir: "./test-results",
  timeout: 60_000,
  expect: {
    toHaveScreenshot: {
      // `threshold` is pixelmatch's per-pixel YIQ tolerance as a fraction of a ~35215 max.
      // Playwright's default of 0.2 permits a delta of ~7043 per pixel, which is far more
      // than a human notices: shifting the site background from #f4efe0 to #e8dcc0 computes
      // to a delta of only ~193 and passed 7/7 tests at the default. Verified, not assumed.
      //
      // So sensitivity comes from `threshold: 0` — any non-identical pixel counts — and
      // tolerance comes from maxDiffPixelRatio, which still allows 1% of pixels to differ.
      // This is safe because the pinned container makes rendering deterministic; both
      // directions are covered by tests/README.md's calibration check.
      threshold: 0,
      maxDiffPixelRatio: 0.01,
      animations: "disabled",
      caret: "hide",
      scale: "css",
    },
  },
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:1414",
    viewport: { width: 1280, height: 900 },
    deviceScaleFactor: 1,
    // Force a stable colour scheme: custom.css commits to a light cream palette, but the
    // theme also ships dark-mode rules that would otherwise depend on the runner.
    colorScheme: "light",
    timezoneId: "UTC",
    locale: "en-US",
    // No service worker in the screenshot specs: a worker makes what is on screen depend on
    // what a previous test cached (gadjoy #41, folio #73). pwa.spec.js opts back in.
    serviceWorkers: "block",
  },
  // Serves the already-built site. `make visual` builds it first; failing fast here beats
  // screenshotting a stale public/.
  webServer: {
    command: "python3 -m http.server 1414 --bind 127.0.0.1 --directory public",
    url: "http://127.0.0.1:1414/index.html",
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
