# Implementation Plan: Test What the Suite Still Cannot See

**Spec**: [spec.md](./spec.md) · **Branch**: `014-wider-testing` · **Created**: 2026-10-30

## Approach

Four independent gaps, four small additions. Nothing here changes the site; the only production
edit is a URL-scheme guard in a developer healthcheck script.

| Gap | Addition |
| --- | --- |
| No accessibility coverage | `tests/visual/a11y.spec.js` — axe-core at WCAG 2.0/2.1 A + AA |
| Only ever tested at 1280px | `tests/visual/responsive.spec.js` — 375 px and 768 px baselines |
| Pages tested, journeys not | `tests/visual/journeys.spec.js` — the click-through and the 404 page |
| The gates' own code unchecked | `make lint` — shellcheck + bandit, both in CI |

`settle()` moves from `gallery.spec.js` into `tests/visual/helpers.js`. It is **moved, not
copied**: its comment records a real investigation into lazysizes dropping 7 of 46 images, and a
second copy would drift from the behaviour it describes.

## Everything was measured before it was specified

The thresholds in this spec are not aspirations; each one is where the code already is.

| Probe | Result | Consequence |
| --- | --- | --- |
| axe, 6 pages | **0 violations** | Gate set at zero — no backlog to negotiate |
| axe self-test (inject missing `alt`) | detected, critical | The zero is real, not a misconfigured tool |
| shellcheck, strictest, 5 files | **0 findings** | Gate set at `--severity=style` |
| shellcheck on a planted `rm -rf $DIR/build` | exit 1, SC2086 | The tool works |
| bandit, `scripts/` + `tests/` | 1 Medium, 224 Low | Gate at medium+; the Medium gets **fixed** |

## Why bandit gates at medium and above

The 224 Low findings are `assert` in the test suite — where asserting *is* the test — and
`subprocess` calls built from literal argv with no shell. Gating on Low would mean writing an
allowlist 224 entries long, and nobody reads an allowlist that long; it would become a blanket.

The single Medium is real and is fixed rather than filtered: `check-live.py` took a URL from argv
and handed it straight to `urlopen`, which will happily serve `file:///etc/passwd` — a tool whose
job is "fetch this and show me what came back" would read local files on request (B310, CWE-22).
The scheme is now validated. The `# nosec` that remains sits on one line and exists **only**
because bandit blacklists the call itself and cannot see a runtime guard — the hole was closed
first, then the message silenced.

## Why both linters run in containers

Neither is installed on this machine, and bandit 1.9.2 requires **Python ≥ 3.10** while the
self-hosted runners are Ubuntu 20.04 with python3 3.8. Checked before writing the CI step rather
than discovered from a red build (`CON-VER-004`). Both are pinned, and `make lint` runs the
*identical* command CI runs, so "passes locally" and "passes in CI" mean the same thing.

## What writing the tests found

Two findings that no amount of reading would have produced, which is the argument for this spec.

### The lightbox never initialises, anywhere

`themes/gallery/assets/js/lightbox.js` starts with `if (document.getElementById("gallery"))`. That
`#gallery` div lives in the **listing branch** of `layouts/partials/gallery.html` — the branch
`CLAUDE.md` already records as never rendering, because the home page uses the theme's
`home.html` → `album-card.html`.

Measured on the built site: **0** pages contain `#gallery`, **0** `.pswp` roots are ever created,
and clicking a painting **navigates to the raw JPEG**. PhotoSwipe — roughly **94 KB** of
`main.js` and **5.3 KB** of CSS — ships to every visitor and never runs.

This is a known fact's unrecorded consequence, not a new bug. Fixing it is a **design decision**
(restore the lightbox, or drop the dead bundle?) and belongs to the artist and owner, not to a
testing change. So the tests characterise the behaviour that actually holds — a click must never
reach an 8 MB master — and record the dead lightbox so that changing it is deliberate and visible.

### axe cannot catch the regression that matters most here

Planting `alt=""` on the artwork image left **every axe check green**, because an empty `alt` is
the standard way to mark an image *decorative* — correct in general, wrong on a site where the
image is the entire content of the page. So the accessible name is asserted directly, on both the
grid and the artwork page. Found only by proving the gate red.

## Verification

Every new gate is shown failing on a real defect before it is trusted (`CON-PROC-005`):

| Gate | Red | Green |
| --- | --- | --- |
| a11y (direct alt assertion) | `alt=""` planted in the template | restored |
| responsive baselines | a CSS rule that bites only below 400 px | restored |
| shellcheck | unquoted `rm -rf $DIR/build` | real files |
| bandit | `subprocess(..., shell=True)` planted | real files |
| URL-scheme guard | guard mutated to `if False:` | restored |

## Risks

| Risk | Mitigation |
| --- | --- |
| More baselines → more churn on any redesign | Viewport-sized, not fullPage; 4 new PNGs, not 4 multi-MB ones |
| axe version drift changes findings | Pinned to `@axe-core/playwright@4.14.0`, covered by `npm audit` |
| The characterisation test enshrines the dead lightbox | Named and commented as *recorded state, not desired*; it fails if someone fixes it, which is the prompt to rewrite it |
| Linters absent locally | Both containerised and pinned; `make lint` is the same command CI runs |
