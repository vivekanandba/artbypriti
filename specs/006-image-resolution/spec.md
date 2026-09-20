# Feature Specification: Stop Upscaling the Paintings

**Feature Branch**: `006-image-resolution`

**Created**: 2026-09-12

**Status**: Draft

**Input**: Workstream A from the post-merge planning survey: "23 of 46 grid images are being
upscaled... no srcset anywhere."

## Problem

The gallery displays paintings at a larger size than the images it generates, so the browser
stretches them. On a site whose product **is** the paintings (Constitution VI), the artwork is being
shown soft.

Measured on `main` @ `c24b6fd`:

| Surface | Displayed at | Upscaled | Worst case |
| --- | --- | --- | --- |
| Home / category grid | 600 CSS px (fixed) | **23 of 46** | `434 × 600` stretched to 600 wide (1.4×) |
| Artwork page | the image's own width | **0** — *see the correction below* | — |

> **Correction, made during implementation.** This spec was first written claiming 24 of 47 artwork
> pages were upscaled too. **That was wrong**, and measuring the rendered geometry disproved it: on
> the artwork page the figure shrink-wraps (flex column, `align-items: center`), so the image is laid
> out at its *natural* width and is never stretched. `displayed == natural` on every page measured.
>
> The artwork pages were **under-filling** their column, not blurring — a different thing, and a
> design question rather than a defect. Sizing them by width would have enlarged the paintings and
> made pages 24–45% taller (`/about/` 1636 → 2368 px). That is the artist's call, not this change's,
> so those pages keep their exact layout and gain only a high-DPI `srcset` candidate.
>
> The grid claim held up: its figure is `width: 100%` inside a 600 px card, so a 434 px image really
> is stretched.

**Root cause, one line:** `images.Process "fit 600x600"` fits the image's **long** edge to 600, but
the CSS constrains its **width** (`width: 100%; max-width: 600px`). For a portrait painting the long
edge is the *height*, so the width comes out short — 434 px where 600 is needed — and the browser
scales it up. Landscape images are unaffected, which is why exactly the portrait half of the
collection is soft.

It is worse than the table suggests on a high-DPI screen: a 577 px source filling a 1000 px slot on a
2× display is a ~3.5× upscale.

Nothing detected this. Visual regression compares each page against its own committed baseline, so a
uniformly-soft gallery matches a uniformly-soft baseline. `check-output.py` asserts an image *exists*,
not that it is big enough to be shown at its display size. That gap is the second half of this work.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Paintings are shown at their true sharpness (Priority: P1)

As a visitor — a collector, a commission enquirer — the paintings look as crisp as the screen I am
using allows, rather than visibly soft on half the collection.

**Why this priority**: The images are the product. Everything else this site does is scaffolding
around showing them.

**Independent Test**: For every rendered image, compare its intrinsic width against the CSS width it
is displayed at; no image is displayed wider than its source.

**Acceptance Scenarios**:

1. **Given** a portrait painting in the grid, **When** the page renders, **Then** the served image is
   at least 600 px wide.
2. **Given** a portrait painting on its own page, **When** the page renders, **Then** its layout is
   **unchanged** — the image keeps the size it had — and a higher-resolution candidate is offered to
   high-DPI screens via `srcset`.
3. **Given** a landscape painting, **When** the page renders, **Then** it is unchanged — no
   regression to the half that was already correct.
4. **Given** any painting whose master is smaller than the target width, **When** the variant is
   generated, **Then** it is **not** upscaled by Hugo either; the source is the ceiling.

---

### User Story 2 - A high-DPI screen gets a high-DPI image (Priority: P2)

As a visitor on a retina laptop or phone, I receive an image matched to my device, and a visitor on a
low-DPI screen or a slow connection is not made to download it.

**Why this priority**: Real quality gain, but it costs payload in a way US1 does not, so it is
constrained by the budget rather than pursued at any cost.

**Acceptance Scenarios**:

1. **Given** a grid or artwork image, **When** it renders, **Then** it offers multiple widths via
   `srcset` with a `sizes` hint describing its layout.
2. **Given** a 1× display, **When** the browser chooses, **Then** it downloads a variant appropriate
   to 1× — retina candidates cost disk, not every visitor's bandwidth.
3. **Given** the published site, **When** it is measured, **Then** it remains **under the 40 MB
   budget** (Constitution IV). If retina candidates would breach it, they are reduced, and the
   measured numbers are stated.
4. **Given** the artwork page, **When** a retina candidate is needed, **Then** the existing 1600 px
   lightbox variant is reused before generating anything new.

---

### User Story 3 - This class of defect cannot return silently (Priority: P1)

As a maintainer, if someone later changes a display width or a processing directive so images are
upscaled again, a gate fails.

**Why this priority**: `CON-PROC-003`. The defect survived every existing gate; fixing it without
closing that hole repeats the pattern this project has already documented nine times.

**Acceptance Scenarios**:

1. **Given** an image served narrower than the width it is displayed at, **When** output assertions
   run, **Then** they fail and name the page and both numbers.
2. **Given** the corrected site, **When** they run, **Then** they pass.
3. **Given** an image whose master is genuinely too small to fill its slot, **When** the check runs,
   **Then** it **warns** rather than fails — the master is the artist's, and no automation can
   conjure resolution that was never photographed (Constitution III).

## Requirements *(mandatory)*

### Functional

- **FR-001**: Grid thumbnails are sized by **width**, not by longest edge, so every card is filled at
  its display width.
- **FR-002**: Artwork-page images keep their current displayed size (no layout change) and gain a
  high-DPI `srcset` candidate. *Amended from "sized by width" once measurement showed those pages were
  never upscaled.*
- **FR-003**: Neither may upscale beyond the master; the source resolution is the ceiling.
- **FR-004**: Both surfaces emit `srcset` and `sizes`.
- **FR-005**: The artwork page reuses the existing 1600 px variant as a retina candidate rather than
  generating a new one.
- **FR-006**: `check-output.py` gains an intrinsic-width-vs-display-width assertion (errors when the
  master could have covered it, warns when it could not).
- **FR-007**: Sizing lives in root `layouts/` overrides, never in the vendored theme (Constitution IX).

### Non-functional

- **NFR-001**: Published site stays under **40 MB** (Constitution IV).
- **NFR-002**: Cache-warm build stays under **15 s** (Constitution IV).
- **NFR-003**: Layout does not change — only resolution. Page structure, spacing and dimensions in CSS
  pixels are identical; visual-regression baselines change *because the images are sharper*, and that
  is stated and reviewed rather than waved through.
- **NFR-004**: No new dependency.

## Success Criteria

- **SC-001**: Zero images displayed wider than their source in the grid — measured, down from **23**.
  Artwork pages were already at 0; the figure that claimed 24 was wrong and is corrected above.
- **SC-002**: Re-introducing a fit-by-long-edge directive fails the new assertion. Demonstrated.
- **SC-003**: Published payload measured and under 40 MB; the number is stated in the PR.
- **SC-004**: Landscape images unchanged, and **every artwork page's rendered geometry is identical to
  `main`** — verified by measuring displayed size and page height, not by eye.
- **SC-005**: Baselines re-recorded deliberately, with before/after evidence that the change is
  sharpness and not layout.

## Out of Scope

- Re-encoding, renaming or replacing any master (Constitution VI).
- Changing layout, spacing, typography or the palette.
- WebP/AVIF — measured and rejected in `000-backend-optimization`; nothing has changed.
- The lightbox's 1600 px variant, which is correctly sized for its purpose.
