// The installable app, proven in a real browser (FLEET.md, PWA standard; spec 009).
//
// Until now this site's PWA was only ever checked as markup: scripts/check-output.py follows
// the registration chain through the built files, but nothing had watched a browser actually
// register the worker, name its cache, and serve a page with the network gone. Markup can be
// perfect while the worker never starts — a CSP blocking an inline script did exactly that,
// silently, before spec 010 moved registration out of line.
//
// The screenshot specs block service workers (playwright.config.js); this one allows them.
const { test, expect } = require("@playwright/test");

test.use({ serviceWorkers: "allow" });

// Exactly what scripts/check-output.py accepts: a commit (CI) or a UTC build time (local).
const STAMPED = /^artbypriti-(?:[0-9a-f]{7,40}|[0-9]{14})$/;

test("the worker registers, names a build-stamped cache, and serves the home page offline", async ({ page, context }) => {
  await page.goto("/", { waitUntil: "load" });

  const worker = await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.ready;
    return { scope: reg.scope, script: reg.active && reg.active.scriptURL };
  });
  expect(new URL(worker.script).pathname, "the worker is the site-root sw.js").toBe("/sw.js");
  expect(new URL(worker.scope).pathname, "the worker controls the whole site").toBe("/");

  const caches = await page.evaluate(() => caches.keys());
  expect(caches.filter((name) => STAMPED.test(name)), `caches: ${caches.join(", ")}`).toHaveLength(1);
  expect(caches.filter((name) => name.startsWith("artbypriti-") && !STAMPED.test(name)),
    "no unstamped artbypriti cache survives activation").toEqual([]);

  // Reload once online, under the worker's control, so the page and its stylesheet are cached
  // together; then take the network away.
  await page.reload({ waitUntil: "load" });
  await context.setOffline(true);
  try {
    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(page, "the home page still loads with no network").toHaveTitle(/Art by Priti/);
  } finally {
    await context.setOffline(false);
  }
});
