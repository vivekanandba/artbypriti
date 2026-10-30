/**
 * Shared browser helpers for the Playwright specs.
 *
 * `settle` lived in gallery.spec.js until spec 014 added three more specs that need it.
 * It is moved rather than copied: the comment below is the record of a real investigation,
 * and a second copy would drift away from the behaviour it describes.
 */

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
 * the lazy-loading mechanism. That mechanism is asserted separately in gallery.spec.js.
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

/**
 * Promote data-src/data-srcset and let the BROWSER choose from the srcset.
 *
 * Unlike `settle`, this deliberately does not force a particular source: the point of the
 * responsive tests is to observe which candidate the browser picks at a given width, which
 * is the behaviour `sizes` exists to control (specs 006 and 011).
 */
async function settleRespectingSrcset(page) {
  await settle(page);
  // currentSrc is only meaningful once the browser has resolved the srcset for this layout.
  await page.waitForFunction(
    () => {
      const img = document.querySelector("img.gallery-single-img");
      return !img || (img.currentSrc && img.currentSrc.length > 0);
    },
    null,
    { timeout: 30_000 },
  );
}

module.exports = { settle, settleRespectingSrcset };
