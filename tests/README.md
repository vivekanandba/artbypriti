# Tests

Four gates, all runnable locally and all run by CI on every pull request. Spec:
[`specs/001-quality-gates/spec.md`](../specs/001-quality-gates/spec.md).

| Gate | Command | Guards |
| --- | --- | --- |
| Content validation | `python3 scripts/check-content.py` | Front matter: declared files exist, captions well-formed |
| Output assertions | `python3 scripts/check-output.py public` | The **built site**: no published masters, payload budget, every artwork renders an image + caption, no broken internal links |
| Citation check | `python3 scripts/check-citations.py` | That every `CON-*` rule this repo cites actually **exists** upstream ([spec 012](../specs/012-citation-guard/spec.md)) |
| Visual regression | `make visual` | How pages actually **look** |

`make check` runs the first three (seconds). `make check-all` adds visual regression (needs Docker).

The citation check reads a **vendored** list, `docs/constitution-ids.txt`, because CI only gets this
repository and cannot see `~/.claude` (`CON-VER-004`). Refresh it with `make constitution-ids`. An ID
this repo has *proposed* but the constitution has not adopted goes in
`docs/constitution-ids-proposed.txt` with a reason — otherwise an honest proposal is
indistinguishable from a typo. To write *about* a bad ID without tripping the gate, put
`not-a-citation` on the line.

## Why output assertions exist at all

Hugo's dominant failure mode is silent fallback, not error. Front matter naming a file that does
not exist does not fail the build — Hugo picks another image and the deploy goes green. Three such
declarations shipped and survived ~15 months behind 16 consecutive successful deploys.

So a gate that only checks Hugo's exit code cannot catch this project's actual defects. Both
scripts assert on artefacts: one on inputs, one on `public/`.

### Errors block, content gaps do not

`check-content.py` fails on structural defects (a declared file that is absent, a malformed
caption) and only *warns* on things only the artist can supply (a missing size, an unwritten
description). A pipeline that blocks a deploy on an unwritten sentence gets bypassed, and a
bypassed pipeline protects nothing. See Constitution Principle III.

## Visual regression

```bash
make visual          # compare against committed baselines
make visual-update   # re-record baselines after an INTENTIONAL design change
```

Baselines live in `tests/visual/gallery.spec.js-snapshots/` and **are committed** — they are the
record of how the site is supposed to look. Run artifacts (`test-results/`, `playwright-report/`)
are ignored; on failure they contain `*-diff.png` images showing exactly what moved.

### Everything runs in a pinned container

`mcr.microsoft.com/playwright:v1.62.1-noble`, driven by `make`. This is not convenience: screenshots
are only comparable when font rendering is byte-identical, so the container is what lets CI and a
laptop agree. Never record baselines outside it — host fonts will differ and every subsequent run
will fail.

The image tag and `@playwright/test` in `package.json` must stay in step.

### Threshold calibration — do not loosen this

`playwright.config.js` sets `threshold: 0` with `maxDiffPixelRatio: 0.01`. That combination is
deliberate and was arrived at empirically:

- Playwright's **default `threshold: 0.2`** is a per-pixel YIQ tolerance of ~20% of a ~35215
  maximum, i.e. it ignores deltas up to ~7043 per pixel.
- Changing the whole site background from `#f4efe0` to `#e8dcc0` — obvious to any human — computes
  to a per-pixel delta of only **~193**. At the default threshold, that change **passed all 7
  tests**. The gate was measurably blind.
- With `threshold: 0`, the same change fails with **47–51% of pixels different**. Sensitivity now
  comes from the threshold; tolerance comes from `maxDiffPixelRatio`, which still permits 1% of
  pixels to differ before failing.

This is safe only because the container makes rendering deterministic — verified by running the
unchanged site three times with zero differences (spec NFR-002).

### Verified behaviour

| Scenario | Expected | Observed |
| --- | --- | --- |
| Unchanged site, run 3× | pass every time | 7/7 passed, three consecutive runs |
| Site background colour shifted | fail with a diff | failed, 47–51% pixels different, diffs written |
| Caption `font-size` changed | fail only the affected page | failed 1 of 7 (the artwork page) |
| Master image planted in `public/` | output assertions fail | failed, naming `olive/Olive.jpg` |
| Internal link broken | output assertions fail | failed, naming source page and dead target |

### A note on lazy loading

The theme lazy-loads via lazysizes, which only unveils images near the viewport. Measured: after
scrolling the home page's full height and returning to the top, **7 of 46 images still had no
`src`** — so a naive full-page screenshot captures blank tiles, and *which* tiles are blank varies
between runs. The test therefore promotes every `data-src` to `src` itself and waits for decode.

Consequence: screenshots verify layout, colour, and typography — not the lazy-loading mechanism.
That mechanism has its own assertion (`gallery images are lazy-loading, not eagerly inlined`), so
removing it cannot pass unnoticed.

## Adding a page to visual regression

Add an entry to `PAGES` in `tests/visual/gallery.spec.js`, then `make visual-update` and commit the
new baseline. Prefer one page per distinct *layout*: every artwork page uses the same template, so a
second one costs a baseline and guards nothing new.

Set `fullPage: false` for long listing pages. A full-page capture of the 46-image home grid is a
6.7 MB PNG; at viewport size it is 749 KB and still covers the grid's layout and palette. These
files are committed, so their size is a real cost (Constitution Principle IV).
