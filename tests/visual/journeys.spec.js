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

test("a visitor pressing Escape always gets out, however early they press", async ({ page }) => {
  // The property, stated the way a visitor would: press Escape and you escape, promptly.
  //
  // PhotoSwipe swallows Escape while its ~333ms open animation runs (reproduced outside the
  // test runner; docs/incidents.md #14). An earlier version of this test pressed once early,
  // once after settling, and asserted the second press closed it -- and that was FLAKY: it
  // passed twice and failed once in a full-suite run. Whether any single press lands depends on
  // exactly where the animation is, which is not a property worth asserting and not one that
  // holds (CON-VER-008: a test that fails only sometimes is a suite defect, not noise).
  //
  // So this asserts the guarantee that does hold and does matter: a visitor pressing Escape --
  // starting as early as possible, repeating as a real person would -- is out within seconds.
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  await settle(page);
  await page.click("a.gallery-item");

  // Deliberately as early as the UI allows, before the animation settles.
  await page.waitForFunction(
    () => document.querySelector(".pswp")?.classList.contains("pswp--ui-visible"),
    null,
    { timeout: 10_000 },
  );

  const deadline = Date.now() + 8_000;
  let presses = 0;
  while (Date.now() < deadline) {
    if ((await page.locator(".pswp").count()) === 0) break;
    await page.keyboard.press("Escape");
    presses += 1;
    await page.waitForTimeout(400);
  }

  await expect(
    page.locator(".pswp"),
    `the visitor must be able to dismiss the lightbox (gave up after ${presses} presses)`,
  ).toHaveCount(0, { timeout: 2_000 });

  const scrollLocked = await page.evaluate(
    () => getComputedStyle(document.body).overflow === "hidden",
  );
  expect(scrollLocked, "and the page must not be left scroll-locked").toBe(false);
});

test("the lightbox caption shows the painting's dimensions", async ({ page }) => {
  // FR-003, and the assertion that was missing when spec 016 shipped: the markup carried
  // data-pswp-caption correctly all along, but the caption plugin defaults to the image's alt
  // -- the TITLE here -- so the deployed lightbox read "Olive" instead of "(15 cm X 15 cm)".
  // The spec claimed this worked; nothing checked it. Found by looking at the live site.
  await page.goto("/olive/", { waitUntil: "domcontentloaded" });
  await settle(page);

  const declared = await page.getAttribute("a.gallery-item", "data-pswp-caption");
  expect(declared, "this fixture needs a painting with dimensions").toBeTruthy();

  await page.click("a.gallery-item");
  await expect(page.locator(".pswp").first()).toBeVisible({ timeout: 10_000 });
  await lightboxSettled(page);

  const caption = page.locator(".pswp__dynamic-caption, .pswp__custom-caption").first();
  await expect(caption, "the caption should render").toBeVisible({ timeout: 10_000 });
  await expect(caption, "it should show the dimensions, not the title").toHaveText(declared);
});

test("a painting with no dimensions falls back to its title rather than an empty bar", async ({ page }) => {
  // Three paintings have no dimensions yet (docs/artist-requests.md). Empty is worse than the
  // title, and this asserts the fallback so a future caption change cannot silently blank them.
  await page.goto("/peace-stool/", { waitUntil: "domcontentloaded" });
  await settle(page);

  const declared = await page.getAttribute("a.gallery-item", "data-pswp-caption");
  expect((declared || "").trim(), "this fixture needs a painting WITHOUT dimensions").toBe("");

  await page.click("a.gallery-item");
  await expect(page.locator(".pswp").first()).toBeVisible({ timeout: 10_000 });
  await lightboxSettled(page);

  const caption = page.locator(".pswp__dynamic-caption, .pswp__custom-caption").first();
  await expect(caption, "it should fall back to the title").toHaveText("Peace Stool");
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
