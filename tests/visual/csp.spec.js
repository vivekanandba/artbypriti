// The Content-Security-Policy, enforced in a real browser (spec 020).
//
// check-output.py checks the MARKUP against the policy. This checks what markup cannot show:
// JavaScript that injects styles or scripts at runtime -- PhotoSwipe, lazysizes, the menu. A
// blocked inline style fails silently (the element just renders unstyled), so the only honest
// test is to listen for the browser's own `securitypolicyviolation` events while doing what a
// visitor does.
const { test, expect } = require("@playwright/test");

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.__csp = [];
    document.addEventListener("securitypolicyviolation", (e) =>
      window.__csp.push(`${e.violatedDirective} ${e.blockedURI || "inline"} ${(e.sample || "").slice(0, 60)}`),
    );
  });
});

async function scrollThrough(page) {
  // Lazy loading runs as images approach the viewport, so the whole page has to be visited.
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 600) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 50));
    }
  });
  await page.waitForTimeout(300);
}

const violations = (page) => page.evaluate(() => window.__csp);

for (const path of ["/", "/categories/acrylic-on-canvas/", "/about/", "/request/", "/404.html", "/olive/"]) {
  test(`no CSP violation while browsing ${path}`, async ({ page }) => {
    await page.goto(path, { waitUntil: "load" });
    await scrollThrough(page);
    expect(await violations(page)).toEqual([]);
  });
}

test("no CSP violation while using the menu and the lightbox", async ({ page }) => {
  await page.goto("/olive/", { waitUntil: "load" });
  const toggle = page.locator("#menu-toggle");
  if (await toggle.count()) {
    await toggle.click();
    await toggle.click();
  }
  await page.click("a.gallery-item");
  await expect(page.locator(".pswp").first()).toBeVisible({ timeout: 10_000 });
  await page.waitForTimeout(800);
  await page.keyboard.press("Escape");
  await expect(page.locator(".pswp")).toHaveCount(0, { timeout: 10_000 });
  expect(await violations(page)).toEqual([]);
});

test("the policy is actually enforced: an injected inline style is blocked", async ({ page }) => {
  // The listener above has to be capable of hearing something, or every test here passes on
  // silence -- the same trap the axe gate fell into with alt="" (spec 014). This also fails the
  // day someone puts 'unsafe-inline' back into style-src, which is the point.
  await page.goto("/", { waitUntil: "load" });
  await page.evaluate(() => {
    const d = document.createElement("div");
    d.innerHTML = '<p id="csp-probe" style="color: rgb(255, 0, 0)">probe</p>';
    document.body.appendChild(d);
  });
  await page.waitForTimeout(200);

  const applied = await page.evaluate(
    () => getComputedStyle(document.getElementById("csp-probe")).color,
  );
  expect(applied, "the inline style must NOT have been applied").not.toBe("rgb(255, 0, 0)");
  expect((await violations(page)).some((v) => v.startsWith("style-src"))).toBe(true);
});
