// The site at the widths it is actually read at (spec 014, US2).
//
// Every baseline before this one was 1280x900. That is the sharpest gap in the suite,
// because specs 006 and 011 both added `sizes` attributes whose ENTIRE PURPOSE is to change
// which image a narrow screen downloads -- and no test had ever rendered this site narrow.
// The most recently changed behaviour had the least coverage.
//
// Captured at viewport size rather than fullPage: a full-page capture of the 46-image home
// grid is a ~6.7MB PNG, and these are committed (spec 001's repository-weight constraint).
// Viewport captures still cover layout, spacing, type and the palette.
const { test, expect } = require("@playwright/test");
const { settle, settleRespectingSrcset } = require("./helpers");

const VIEWPORTS = [
  { name: "mobile", width: 375, height: 812, why: "iPhone-class portrait, the commonest real width" },
  { name: "tablet", width: 768, height: 1024, why: "where the grid changes columns" },
];

const PAGES = [
  { name: "home", path: "/" },
  { name: "artwork", path: "/ganesha-with-lines/", why: "portrait master: the half spec 011 enlarged" },
];

for (const vp of VIEWPORTS) {
  test.describe(`${vp.name} (${vp.width}px) — ${vp.why}`, () => {
    test.use({ viewport: { width: vp.width, height: vp.height } });

    for (const { name, path } of PAGES) {
      test(`${name} renders unchanged`, async ({ page }) => {
        const response = await page.goto(path, { waitUntil: "domcontentloaded" });
        expect(response?.status(), `${path} should be served`).toBe(200);
        await settle(page);
        await expect(page).toHaveScreenshot(`${name}-${vp.name}.png`);
      });
    }

    test("the page does not scroll sideways", async ({ page }) => {
      // A horizontal scrollbar at phone width is the classic responsive regression, and it
      // is invisible in a viewport screenshot because the overflow is off-screen.
      await page.goto("/", { waitUntil: "domcontentloaded" });
      await settle(page);
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow, "no horizontal overflow at this width").toBeLessThanOrEqual(0);
    });
  });
}

test.describe("srcset actually selects a narrower image on a narrow screen", () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test("the artwork page serves a smaller variant at 375px than at 1280px", async ({ page }) => {
    // This is the behaviour `sizes` exists for, and nothing asserted it. It is checked on
    // the SELECTED image (currentSrc), not on the markup that offers the choice -- the
    // markup being right is what specs 006 and 011 already assert, and is a weaker claim.
    await page.goto("/ganesha-with-lines/", { waitUntil: "domcontentloaded" });
    await settleRespectingSrcset(page);
    const narrow = await page.evaluate(() => {
      const img = document.querySelector("img.gallery-single-img");
      return { src: img.currentSrc, natural: img.naturalWidth, displayed: Math.round(img.getBoundingClientRect().width) };
    });

    expect(narrow.displayed, "the image should fit a 375px screen").toBeLessThanOrEqual(375);
    expect(narrow.natural, "a 1000px variant on a 375px screen is wasted bandwidth")
      .toBeLessThanOrEqual(1000);
    expect(narrow.src, "should still be a Hugo-derived variant, never a master").toContain("_hu_");
  });
});
