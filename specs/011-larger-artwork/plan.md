# Implementation Plan: Show the Paintings Larger on Their Own Page

**Spec**: [spec.md](./spec.md) · **Branch**: `011-larger-artwork` · **Created**: 2026-10-30

## Approach

One directive changes. `layouts/partials/gallery.html` line 16 asks Hugo to fit the longest edge
into a 1000 px box; it should resize the **width** to 1000 instead, and decline to upscale a master
that cannot reach it.

```
- {{ $thumbnail := $image.Filter (slice images.AutoOrient (images.Process "fit 1000x1000")) }}
+ {{ $oriented := $image.Filter images.AutoOrient }}
+ {{ $width := int (math.Min 1000 $oriented.Width) }}
+ {{ $thumbnail := $image.Filter (slice images.AutoOrient (images.Process (printf "resize %dx" $width))) }}
```

Three details carry the correctness:

1. **`AutoOrient` first, then measure.** `$image.Width` on an EXIF-rotated master reports the stored
   dimensions, not the displayed ones, so a portrait photographed sideways would be capped on the
   wrong number. Applying the filter first and measuring the *result* is the only ordering that is
   right for both (FR-003).
2. **`math.Min` against the master's width** is the no-upscaling rule, expressed where the decision
   is made rather than checked afterwards (FR-002, Constitution III). Hugo would happily enlarge.
3. **`resize <w>x`** (width only, height omitted) preserves the aspect ratio. `fit 1000x1000`
   constrains the longest edge, which is the bug.

### `$oriented` measures; it does not produce

The obvious shorter form is `$oriented.Resize ...`, deriving the variant from the already-filtered
image. **Written that way first, then measured and rejected.** It resamples a processed intermediate
rather than the master, and it cost:

- **0.15 dB** against a Lanczos reference on `/olive/` (34.87 → 34.72 dB) — small, but a loss in the
  one direction this change exists to improve;
- **every one of the 23 landscape and square variants changed bytes**, on pages this change is
  supposed to leave untouched. The visual suite failed `/olive/` at a 0.40 pixel ratio for a page
  whose measured geometry had not moved at all.

Filtering the **master** in a single pipeline makes those 23 outputs **byte-identical** to what
shipped before (verified by checksum), and the extra decode leaves the build. `$oriented` survives
only to supply a number.

This is the plan's own worked example of the repository rule it opens with: the first version looked
correct, built green, passed every output assertion, and was wrong in a way only measurement showed.

The surrounding `srcset`/`sizes` machinery from spec 006 needs no change: it already derives both
from `$thumbnail`'s actual dimensions, so it follows the new width automatically. Worth stating
because it is the part most likely to be "fixed" unnecessarily.

## Why this is safe for the 23 unchanged pages

A landscape or square master already produces a 1000 px width under `fit 1000x1000`, because for
those the longest edge *is* the width. `math.Min 1000 width` yields the same 1000. The directive
changes; their output does not. This is asserted by measurement (SC-002), not by this argument.

## The gate (US3)

The artwork page still cannot *upscale* — the figure shrink-wraps, so the image renders at
`min(natural, 1000)` and the browser never stretches it. The existing `check_no_upscaling` therefore
correctly skips it, and must keep skipping it; pointing that check at this page would be the wrong
assertion wearing the right name (`CON-VER-005`).

The failure mode here is the opposite one: **under-filling**. So a new assertion,
`check_artwork_fills_its_column`, fails when an artwork page's image is served narrower than the
1000 px column *while its master could have covered it*, and warns when the master could not. Before
this change it would report 24 errors; after, 0 errors and 1 warning (`/about/`).

That asymmetry is the point. Under-filling is invisible to every gate this repo has: visual
regression compares each page against its own equally-under-filled baseline, and output assertions
check that an image exists, not that it is as large as the page affords. The same blindness let the
grid ship soft for 15 months (spec 006).

## The registry check (US4)

`specs/README.md` listed 4 of 11 specs. Nothing asserted it was complete, so it drifted silently —
the same shape of defect, in the document whose only job is completeness. `check-specs.py` gains a
check that the set of `specs/NNN-*/` directories and the set of rows in the table are equal.

Scope note: this is not part of the artwork change. It was found while writing this spec, it costs
~15 lines, and leaving a known-false index in place to keep a diff tidy is how it got that way. It
is called out separately in the PR rather than folded in quietly.

## Verification

Measurement first, and in a browser — this repository's standing rule is that reading a template
produces confident wrong conclusions (`CLAUDE.md`, and twice already in this session).

| What | How |
| --- | --- |
| Geometry before/after | Playwright probe in the pinned container: rendered box, natural pixels, page height, on 5 representative pages |
| All 47 images | Compute expected width from each master; cross-check against the built variants |
| No upscaling | `/about/` (739 px master) served at 739, asserted |
| Payload | `du -sh public` against the 40 MB budget |
| Warm build | `time hugo --gc --minify --cleanDestinationDir` against 15 s |
| Gate works | Restore the old directive, watch the new check fail, restore (`CON-PROC-005`) |
| Registry gate works | Remove a row, watch it fail |
| Unit tests | New cases for both checks; coverage floor ≥95% holds |
| Baselines | Re-recorded, reviewed as the record of an intended change |

## Alternatives considered

**Leave it, and raise the column instead.** Rejected: the column is 1000 px because that is the
readable measure the design settled on; the paintings not filling it is the defect, not the column.

**Generate a 1000 px variant but keep `fit` as a fallback.** Rejected: two directives describing one
slot is how the mismatch survived in the grid. One source of truth.

**Size by height to the viewport.** Rejected: makes the painting's size depend on the visitor's
window, which breaks `srcset` (the browser picks before layout) and the committed baselines.

## Risks

| Risk | Mitigation |
| --- | --- |
| Pages get much taller; the artist may dislike it | Measured and stated per page before merge; one directive to revert |
| Payload grows past budget | Measured; 35 MB before, budget 40 MB — stated in the PR, and the retina candidate is reused rather than regenerated |
| Baseline churn hides an unintended change | Geometry measured numerically as well as by screenshot, so "it looks different" is backed by which number moved |
