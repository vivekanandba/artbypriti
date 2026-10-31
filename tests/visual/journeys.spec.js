// What a visitor actually does, rather than what a page contains (spec 014, US3; spec 016).
//
// The suite checked pages. The lightbox was asserted to POINT AT a derived variant and had never
// been opened by a test. The 404 page had no test of any kind.
const { test, expect } = require("@playwright/test");
const { settle } = require("./helpers");

// The lightbox works as of spec 016. It did not before: themes/.../lightbox.js initialises only
// `if (document.getElementById("gallery"))`, and that div lives in the listing branch of
// gallery.html, which never renders on this site. Measured then: 0 #gallery elements, 0 .pswp
// roots, and a click navigated to the raw JPEG (docs/incidents.md #11).
//
// It is NOT fixed by adding that id -- gallery.js keys off the same one and would force the
// painting into a 288px justified row, which failed five baselines when tried.
// assets/js/artwork-lightbox.js scopes itself to the artwork section instead.
//
// These tests assert the visitor-facing behaviour, so a regression in either direction -- the
// lightbox silently not opening again, or a master becoming reachable -- fails here.

test("clicking a painting opens the lightbox without leaving the page", async ({ page }) => {
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  await settle(page);
  const before = page.url();

  await page.click("a.gallery-item");

  const lightbox = page.locator(".pswp").first();
  await expect(lightbox, "the lightbox should open").toBeVisible({ timeout: 10_000 });
  await expect(
    lightbox.locator("img.pswp__img").first(),
    "it should show the painting",
  ).toBeVisible({ timeout: 10_000 });

  // The whole point: the visitor stays on the artwork page. Before spec 016 this navigated away
  // to a bare JPEG with no navigation and no way back but the browser's Back button.
  expect(page.url(), "a click must not navigate away from the artwork page").toBe(before);
});

test("the enlarged image is a derived variant, never a full-resolution master", async ({ page }) => {
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  await settle(page);
  await page.click("a.gallery-item");

  const shown = page.locator(".pswp img.pswp__img").first();
  await expect(shown).toBeVisible({ timeout: 10_000 });

  const src = await shown.getAttribute("src");
  expect(src, "the lightbox must serve a Hugo-processed variant").toContain("_hu_");
  expect(src, "the 8MB master is not published and must not be reachable").not.toContain(
    "/olive/Olive.jpg",
  );
});

/** Wait until the open animation has finished, by watching the image stop moving.
 *
 * Not a fixed sleep: what matters is that the zoom animation has settled, and geometry
 * stability says that directly. The distinction is load-bearing — see the Escape quirk below.
 */
async function lightboxSettled(page) {
  await page.waitForFunction(
    () => document.querySelector(".pswp")?.classList.contains("pswp--ui-visible"),
    null,
    { timeout: 10_000 },
  );
  await page.waitForFunction(
    () => {
      const img = document.querySelector(".pswp img.pswp__img");
      if (!img) return false;
      const r = img.getBoundingClientRect();
      const key = `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.top)}`;
      const stable = window.__pswpPrev === key;
      window.__pswpPrev = key;
      return stable;
    },
    null,
    { timeout: 10_000, polling: 120 },
  );
}

test("the lightbox closes on Escape and does not trap the page", async ({ page }) => {
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  await settle(page);
  await page.click("a.gallery-item");

  await expect(page.locator(".pswp").first()).toBeVisible({ timeout: 10_000 });
  await lightboxSettled(page);

  // A keyboard user who cannot dismiss it is trapped on the page.
  await page.keyboard.press("Escape");
  // PhotoSwipe REMOVES its root rather than hiding it, so absence is the correct assertion.
  await expect(page.locator(".pswp"), "Escape should close the lightbox").toHaveCount(0, {
    timeout: 10_000,
  });

  const scrollLocked = await page.evaluate(
    () => getComputedStyle(document.body).overflow === "hidden",
  );
  expect(scrollLocked, "the page must not stay scroll-locked after closing").toBe(false);
});

test("Escape pressed mid-animation delays dismissal but never traps the visitor", async ({ page }) => {
  // Measured upstream quirk, recorded rather than wished away (docs/incidents.md #14):
  // PhotoSwipe swallows Escape while the ~333ms open animation is still running, so the
  // lightbox stays open. The question that matters for accessibility is whether the visitor is
  // STUCK — and they are not: a second Escape always closes it. Asserted here so that if an
  // upstream bump ever turns "press twice" into "cannot close", this fails loudly.
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  await settle(page);
  await page.click("a.gallery-item");

  // Deliberately early: as soon as the UI appears, before the animation settles.
  await page.waitForFunction(
    () => document.querySelector(".pswp")?.classList.contains("pswp--ui-visible"),
    null,
    { timeout: 10_000 },
  );
  await page.keyboard.press("Escape");

  // Whether that press lands is timing-dependent and is deliberately not asserted either way.
  // Pressing again immediately does NOT help — measured; the second press is mid-animation
  // too. What is asserted is the property that actually matters: an early press does not put
  // the lightbox into a state it can never leave. Once the animation settles, Escape works.
  await lightboxSettled(page);
  await page.keyboard.press("Escape");
  await expect(
    page.locator(".pswp"),
    "after the animation settles, Escape must always close the lightbox",
  ).toHaveCount(0, { timeout: 10_000 });
});

test("listing pages are untouched by the lightbox module", async ({ page }) => {
  // artwork-lightbox.js is scoped to .gallery-single-centered precisely so it cannot reach the
  // home grid. Asserted, because the previous attempt (id="gallery") did reach it and broke it.
  for (const path of ["/", "/categories/acrylic-on-canvas/"]) {
    await page.goto(path, { waitUntil: "domcontentloaded" });
    await settle(page);
    const roots = await page.evaluate(() => document.querySelectorAll(".pswp").length);
    expect(roots, `${path} should not initialise a lightbox`).toBe(0);
  }
});

test("an unknown URL renders the site's 404 page, not a bare error", async ({ page }) => {
  // GitHub Pages serves 404.html for unmatched paths. The local static server used by this
  // suite does not, so the page itself is fetched directly -- what is under test is that the
  // 404 document is a real site page, which is the part Hugo controls and can regress.
  const response = await page.goto("/404.html", { waitUntil: "domcontentloaded" });
  expect(response?.status()).toBe(200);

  await expect(page.locator("header")).toBeVisible();
  const body = (await page.textContent("body")) || "";
  expect(body.trim().length, "the 404 page should say something").toBeGreaterThan(0);

  // It must be a page, not a stub: the way home has to exist, or a lost visitor stays lost.
  const home = page.locator('a[href="/"], a[href="./"]').first();
  await expect(home, "the 404 page should offer a way back").toHaveCount(1);
});
