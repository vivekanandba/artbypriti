// What a visitor actually does, rather than what a page contains (spec 014, US3).
//
// The suite checked pages. The lightbox -- supposedly the only real interactivity on this
// site -- was asserted to POINT AT a derived variant and had never been opened by a test.
// The 404 page had no test of any kind.
const { test, expect } = require("@playwright/test");
const { settle } = require("./helpers");

// CHARACTERISATION, not endorsement. Writing the "open the lightbox" test is what found that
// there is no lightbox to open:
//
//   themes/gallery/assets/js/lightbox.js initialises only `if (document.getElementById(
//   "gallery"))`. That #gallery div lives in the LISTING branch of
//   layouts/partials/gallery.html -- the branch CLAUDE.md already records as never
//   rendering, because the home page uses the theme's home.html -> album-card.html.
//
// Measured on the built site: 0 pages contain #gallery, 0 .pswp roots are ever created, and
// clicking a painting NAVIGATES to the raw JPEG. PhotoSwipe (~94KB of main.js, ~5.3KB of
// CSS) ships to every visitor and never runs. See docs/incidents.md.
//
// These tests therefore guard the invariant that actually holds today -- a click must never
// reach an 8MB master -- and record the dead lightbox, so that fixing it is a deliberate,
// visible change rather than a surprise. If someone wires the lightbox up, the second test
// fails and should be rewritten to assert the real thing.

test("clicking a painting goes to a derived variant, never a full-resolution master", async ({ page }) => {
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  await settle(page);

  const href = await page.getAttribute("a.gallery-item", "href");
  expect(href, "the painting should link somewhere").toBeTruthy();

  await page.click("a.gallery-item");
  await page.waitForLoadState("domcontentloaded");

  const landed = new URL(page.url()).pathname;
  expect(landed, "a click must land on a Hugo-derived variant, not a master").toContain("_hu_");
  expect(landed, "the 8MB master must never be reachable by a click").not.toBe("/olive/Olive.jpg");
});

test("the lightbox does not initialise (recorded state, not a desired one)", async ({ page }) => {
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  await settle(page);
  await page.waitForTimeout(500);

  const state = await page.evaluate(() => ({
    galleryDiv: !!document.getElementById("gallery"),
    pswpRoots: document.querySelectorAll(".pswp").length,
  }));

  expect(
    state.galleryDiv,
    "#gallery now exists -- the lightbox may work; rewrite this test to assert that it opens",
  ).toBe(false);
  expect(state.pswpRoots, "no PhotoSwipe root is created, because it never initialises").toBe(0);
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
