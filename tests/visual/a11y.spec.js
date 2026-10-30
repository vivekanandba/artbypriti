// Accessibility, which had zero coverage before spec 014 (US1).
//
// On a site whose product is images, the accessible name of an image is not a nicety -- it
// is the entire experience for a visitor using a screen reader. An `alt` lost in a template
// edit, a control that stops being keyboard-reachable, a contrast regression in custom.css:
// none of it failed anything.
//
// The baseline was MEASURED before this gate was written: 0 violations at WCAG 2.0/2.1
// A + AA across these pages. So the threshold is zero from day one -- there is no backlog to
// negotiate, and this is purely a regression guard.
//
// That a clean result is real, and not a misconfigured tool reporting silence, was checked
// by injecting an <img> with no alt into a real page: axe reported `image-alt`, critical.
// A gate that has never reported anything is not evidence (CON-PROC-005).
const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;
const { settle } = require("./helpers");

// WCAG 2.0 and 2.1, levels A and AA. Not AAA: that is a deliberate design commitment, not a
// defect threshold, and claiming it without the design work behind it would be dishonest.
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

const PAGES = [
  { name: "home", path: "/", why: "the 46-image grid" },
  { name: "artwork", path: "/olive/", why: "single.html: the painting, its caption, its category link" },
  { name: "artwork-portrait", path: "/ganesha-with-lines/", why: "the layout spec 011 changed" },
  { name: "about", path: "/about/", why: "prose plus a portrait image" },
  { name: "request", path: "/request/", why: "prose only — the nearest thing to a form" },
  { name: "category", path: "/categories/acrylic-on-canvas/", why: "taxonomy listing" },
  { name: "404", path: "/404.html", why: "reached by real visitors, tested by nobody" },
];

for (const { name, path, why } of PAGES) {
  test(`${name} has no accessibility violations (${why})`, async ({ page }) => {
    const response = await page.goto(path, { waitUntil: "domcontentloaded" });
    expect(response?.status(), `${path} should be served`).toBe(200);
    // Images must be loaded before axe runs, or image-alt findings depend on lazy-loading
    // timing and the gate becomes intermittent -- exactly the flakiness CON-VER-008 names.
    await settle(page);

    const { violations } = await new AxeBuilder({ page }).withTags(TAGS).analyze();

    // Report what failed and how badly, not just a count: a bare number sends the next
    // reader to re-run the tool to learn anything (CON-REP-001).
    const summary = violations
      .map((v) => `${v.id} (${v.impact}, ${v.nodes.length} node(s)): ${v.help}`)
      .join("\n  ");
    expect(violations.length, `axe violations on ${path}:\n  ${summary}`).toBe(0);
  });
}

// axe is necessary but NOT sufficient here, and proving it red is what showed that:
// emptying the alt on a painting (alt="") passes every WCAG rule, because an empty alt is
// the standard way to mark an image DECORATIVE. That is correct in general and wrong on this
// site, where the image is the entire content of the page. So the accessible name is
// asserted directly, on both surfaces.
test("every painting on the home grid has a non-empty accessible name", async ({ page }) => {
  // The single most important accessible fact on this site, asserted directly rather than
  // trusted to a generic rule: axe's image-alt passes an empty alt="" as "decorative", and
  // a painting is never decorative.
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await settle(page);

  const unnamed = await page.$$eval("section.galleries img", (imgs) =>
    imgs
      .filter((img) => !(img.getAttribute("alt") || "").trim())
      .map((img) => img.getAttribute("data-src") || img.getAttribute("src") || "(unknown)"),
  );

  expect(unnamed, `images with no alt text: ${unnamed.join(", ")}`).toEqual([]);
});

test("the painting on an artwork page has a non-empty accessible name", async ({ page }) => {
  // The one image a visitor came to see. alt="" would pass axe as "decorative" -- verified
  // by planting exactly that and watching the axe gate stay green (spec 014, T0xx).
  for (const path of ["/olive/", "/ganesha-with-lines/"]) {
    await page.goto(path, { waitUntil: "domcontentloaded" });
    await settle(page);
    const alt = await page.getAttribute("img.gallery-single-img", "alt");
    expect((alt || "").trim(), `${path}: the painting needs a real alt, not alt=""`).not.toBe("");
  }
});
