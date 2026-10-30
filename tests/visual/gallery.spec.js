// Visual regression over the pages that carry this site's appearance (spec US2).
//
// The site's look comes from a 119-line custom.css that overrides a vendored theme with
// `!important` rules. Nothing else detects when one of those cascades somewhere unintended.
// These baselines record how the site looks today; they do not endorse the design.
const { test, expect } = require("@playwright/test");

// One page per distinct layout. Adding more artwork pages would multiply baselines without
// covering new rendering paths — every artwork page uses the same template.
//
// With one exception, and it is an orientation rather than a layout: the artwork image is
// sized by WIDTH to a 1000px column (spec 011), so a portrait painting and a landscape one
// take different branches of that cap. `/olive/` is landscape and fills the column already;
// every portrait page is the half that spec 011 changed, and when it shipped, not one of them
// had a baseline. `/ganesha-with-lines/` covers that half.
//
// `fullPage` is deliberate per page, not a default. A full-page capture of the 46-image home
// grid is a 6.7 MB PNG, and these baselines are committed: at that size a few redesigns would
// undo the repository slimming this project just did (Principle IV). The listing pages are
// captured at viewport size, which still covers the grid's layout, spacing, and palette,
// while the short pages are captured whole.
const PAGES = [
  { name: "home", path: "/", fullPage: false, why: "album-card grid, the only page using home.html" },
  { name: "artwork", path: "/olive/", fullPage: true, why: "single.html: image, dimensions caption, category link" },
  { name: "artwork-portrait", path: "/ganesha-with-lines/", fullPage: true, why: "single.html with a portrait master: the half the 1000px width cap actually moves" },
  { name: "about", path: "/about/", fullPage: true, why: "prose layout with a portrait resource" },
  { name: "request", path: "/request/", fullPage: true, why: "prose layout, no images" },
  { name: "category", path: "/categories/acrylic-on-canvas/", fullPage: false, why: "taxonomy term listing" },
];

/**
 * Make image loading deterministic before screenshotting.
 *
 * The theme lazy-loads via lazysizes (`data-src` plus a 300ms opacity transition), which
 * only unveils images near the viewport. Measured on the home page: after scrolling the
 * full height and returning to the top, 7 of 46 images still had no `src` — lazysizes had
 * dropped them as out of range. A `fullPage` screenshot then captures blank tiles, and
 * *which* tiles are blank varies run to run. That is precisely the flakiness NFR-002
 * forbids, so this promotes every `data-src` to `src` directly and waits for decode
 * instead of negotiating with the lazy-loader's heuristics.
 *
 * The trade-off is explicit: these screenshots verify layout, colour, and typography, not
 * the lazy-loading mechanism. That mechanism is asserted separately below.
 */
async function settle(page) {
  await page.evaluate(() => {
    for (const img of Array.from(document.images)) {
      const src = img.getAttribute("data-src");
      const srcset = img.getAttribute("data-srcset");
      if (src) img.setAttribute("src", src);
      if (srcset) img.setAttribute("srcset", srcset);
      // custom.css hides `.lazyload` at opacity 0 and only reveals `.lazyloaded`.
      img.className = img.className.replace(/\blazyload(ing)?\b/g, "lazyloaded");
    }
  });

  await page.waitForFunction(
    () => Array.from(document.images).every((img) => img.complete && img.naturalWidth > 0),
    null,
    { timeout: 30_000 },
  );
  await page.waitForLoadState("networkidle");
}

for (const { name, path, fullPage, why } of PAGES) {
  test(`${name} renders unchanged (${why})`, async ({ page }) => {
    const response = await page.goto(path, { waitUntil: "domcontentloaded" });
    expect(response?.status(), `${path} should be served`).toBe(200);

    await settle(page);

    await expect(page).toHaveScreenshot(`${name}.png`, { fullPage });
  });
}

// Guards the invariant that the backend work of 2026-08 established: masters are not
// published, so the lightbox must serve a derived variant. A regression here would quietly
// start shipping 8MB images again — visible in no screenshot.
test("artwork lightbox points at a derived variant, never a master", async ({ page }) => {
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  const src = await page.getAttribute("a.gallery-item", "data-pswp-src");
  expect(src, "lightbox source must be a Hugo-processed variant").toContain("_hu_");
});

// settle() bypasses lazysizes to keep screenshots deterministic, so assert the mechanism is
// still wired up — otherwise a regression that broke lazy loading for real visitors would
// pass every visual test.
test("gallery images are lazy-loading, not eagerly inlined", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  // Every gallery image must ship deferred (data-src). Note we cannot assert the absence of
  // `src`: lazysizes legitimately populates it on above-fold images as soon as it runs, so
  // that check would race the loader rather than test the markup.
  const total = await page.locator("section.galleries img").count();
  const deferred = await page.locator("section.galleries img[data-src]").count();
  expect(total, "home page should render gallery images").toBeGreaterThan(0);
  expect(deferred, "every gallery image should defer loading via data-src").toBe(total);
});
