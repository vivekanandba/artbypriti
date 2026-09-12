# Implementation Plan: Stop Upscaling the Paintings

**Branch**: `006-image-resolution` | **Date**: 2026-09-12 | **Spec**: [spec.md](./spec.md)

## Summary

Size grid thumbnails by width instead of longest edge so portrait paintings stop being stretched, and
offer higher-resolution candidates via `srcset` — within the 40 MB budget, and without changing any
page's layout.

## Constitution Check

| Principle | Compliance |
| --- | --- |
| I / `CON-VER-003` — assert on output | The fix is verified by measuring rendered geometry and served pixel widths, not by reading templates. It also **overturned my own claim** about artwork pages. |
| II — the rendered page is the contract | Layout equivalence proved by measuring `getBoundingClientRect()` on both builds side by side, not by eye |
| III — content gaps warn | `about`'s 739 px master cannot fill a 1000 px slot; the gate warns rather than failing (Constitution III) |
| IV — performance is a budget | First attempt measured **46 MB**, over budget. Trimmed the 1200w candidates (10.1 MB) to land at **34.8 MB** |
| VI — images are the product | The whole point |
| IX — vendored theme declares itself | Two new root overrides recorded in `UPSTREAM.md`, including that the theme's copies are now dead code |

## Technical decisions

### Size by width, because the CSS constrains width

`images.Process "fit 600x600"` fits the *longest* edge. A portrait master therefore yields ~434 px of
width for a card that is 600 px wide. `Resize "600x"` fixes the width and lets height follow.

### Cap at the master, always

Every candidate width is emitted only when `≤ $oriented.Width`, so Hugo is never asked to invent
pixels. `images.AutoOrient` is applied *before* measuring, because a rotated master reports
pre-rotation dimensions and would select the wrong widths.

### 400/600/900, not 400/600/900/1200

Measured: the 1200w set cost **10.1 MB** and pushed the site to **46 MB**, over budget. 900w still
covers a 2× phone (~92 vw ≈ 720 CSS px), which is where high-DPI actually bites. A 2× desktop gets
900 px into a 600 px card — short of ideal, but far better than the 434 it received before, and it
keeps the site at 34.8 MB.

### The artwork page: measured, then reverted

The first implementation sized artwork pages by width too, on the assumption they were upscaling.
**They were not.** Their figure shrink-wraps, so `displayed == natural`; sizing by width *enlarged*
the paintings and made `/about/` grow 1636 → 2368 px. That is a design change, not a defect fix, so
the displayed image is byte-for-byte what it was and only a `srcset` candidate was added — reusing
the 1600 px lightbox variant that already exists, at zero extra payload.

`sizes` there is `{{ $thumbnail.Width }}px`, which is the *true* CSS width, because that surface has
no fixed slot.

### Rejected

- **Sizing artwork pages by width** — see above; the owner's call, not a defect.
- **1200w grid candidates** — over budget.
- **New 2000w variants for artwork pages** — the 1600 px lightbox variant already covers high-DPI.
- **Pillow in `check-output.py`** — NFR-004. A ~30-line stdlib JPEG/PNG header reader instead.

## Verification approach

| Claim | Method | Result |
| --- | --- | --- |
| Grid no longer upscales | Served width vs the 600 px slot, every card | 23 → **0** |
| Artwork layout unchanged | `getBoundingClientRect()` + page height, both builds | identical on all 3 sampled |
| Payload within budget | `du` + `check-output.py` | **34.8 MB** / 40 MB |
| The gate catches a regression | Re-introduced `Fit`, rebuilt | failed, naming the widths |
| Baselines changed for the right reason | Compared baseline PNG dimensions | only home + category, **same dimensions** |
