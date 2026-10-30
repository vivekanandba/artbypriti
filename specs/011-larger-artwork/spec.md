# Feature Specification: Show the Paintings Larger on Their Own Page

**Feature Branch**: `011-larger-artwork`

**Created**: 2026-10-30

**Status**: Draft

**Input**: The design decision `006-image-resolution` deliberately refused to make. Spec 006 found
that artwork pages were *under-filling* their column rather than being upscaled, and recorded:
"Sizing them by width would have enlarged the paintings and made pages 24–45% taller. That is the
artist's call, not this change's." The owner has since made that call: show them larger.

## Problem

On an artwork page the painting is laid out at its **natural** width — the figure shrink-wraps
(`display: flex; flex-direction: column; align-items: center`), so the image is never stretched. The
variant it is given comes from `images.Process "fit 1000x1000"`, which fits the image's **longest**
edge into 1000 px. For a portrait painting the longest edge is the *height*, so the height becomes
1000 and the width falls out short.

The column it sits in is 1000 px wide (`.gallery-single-img { width: 100%; max-width: 1000px }`).
Portrait paintings therefore occupy a fraction of it, while landscape and square ones fill it
exactly.

Measured on this branch's parent (`dc00112`), with a real browser at a 1280 px viewport:

| Page | Orientation | Displayed | Column | Fills |
| --- | --- | --- | --- | --- |
| `/olive/` | landscape | 1000 × 986 | 1000 | 100% |
| `/lotus-series-1/` | square | 1000 × 1000 | 1000 | 100% |
| `/pear/` | portrait | **792** × 1000 | 1000 | 79% |
| `/ganesha-with-lines/` | portrait | **723** × 1000 | 1000 | 72% |
| `/about/` | portrait | **577** × 1000 | 1000 | 58% |

`displayed == natural` on every page, confirming the shrink-wrap: this is under-filling, **not**
blurring. Nothing is wrong with the pixels being served; there are simply too few of them because
the wrong edge is being constrained.

**24 of 47 images** — exactly the portrait half of the collection — are shown smaller than the page
has room for. The remaining 23 are already at the cap and must not change.

**Root cause, one line:** the artwork page constrains the image's *width*, but the image is generated
by constraining its *longest edge*. This is the same mismatch spec 006 fixed for the grid, left
unfixed here on purpose.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A portrait painting fills the column it is given (Priority: P1)

As a visitor looking at a single painting, the painting is as large as the page allows, rather than
floating at 58–79% of the available width while the layout reserves the rest.

**Why this priority**: The images are the product (Constitution VI). This page exists to show one
painting; showing it at 58% of the available width is the page failing at its only job.

**Independent Test**: Measure the rendered width of the image on a portrait artwork page; it equals
the column width, or the master's width where the master is smaller.

**Acceptance Scenarios**:

1. **Given** a portrait painting whose master is at least 1000 px wide, **When** its page renders,
   **Then** the image is displayed 1000 px wide.
2. **Given** a landscape or square painting, **When** its page renders, **Then** its geometry is
   **unchanged** from before this change — the half that was already correct does not move.
3. **Given** a painting whose master is narrower than 1000 px, **When** its page renders, **Then** it
   is displayed at the master's width and **is not upscaled** — the source is the ceiling
   (Constitution III; the artist's resolution is not automation's to invent).
4. **Given** any artwork page, **When** it renders, **Then** the image is still never displayed wider
   than it is served.

---

### User Story 2 - The enlargement does not cost the visitor the page (Priority: P2)

As a visitor, the larger paintings do not push the site past its payload budget or make the build
slow enough to discourage deploying.

**Why this priority**: A quality gain that breaches the budget is not a gain; Constitution IV sets
both limits and this change spends against them deliberately.

**Acceptance Scenarios**:

1. **Given** the published site, **When** it is measured, **Then** it is **under 40 MB**
   (Constitution IV), and the measured figure is stated in the PR.
2. **Given** a cache-warm build, **When** it runs, **Then** it completes in **under 15 s**.
3. **Given** the artwork page, **When** a retina candidate is needed, **Then** the existing 1600 px
   lightbox variant is reused rather than a new one generated (carried over from `006` FR-005).
4. **Given** a 1× display, **When** the browser chooses from `srcset`, **Then** it downloads the 1×
   variant — the retina candidate costs disk, not every visitor's bandwidth.

---

### User Story 3 - A silent reversion is impossible (Priority: P1)

As a maintainer, if someone later restores a fit-by-longest-edge directive on this page, a gate fails
and names the pages affected.

**Why this priority**: `CON-PROC-003`. This exact mismatch has now been found **twice** in this
repository — once in the grid (spec 006), once here. It was invisible both times because visual
regression compares each page against its own equally-wrong baseline. Fixing the second instance
without closing the hole would guarantee a third.

**Acceptance Scenarios**:

1. **Given** an artwork page whose image is served narrower than the 1000 px column while its master
   is at least 1000 px wide, **When** output assertions run, **Then** they **fail**, naming the page,
   the served width and the column width.
2. **Given** the corrected site, **When** they run, **Then** they pass.
3. **Given** a painting whose master is genuinely smaller than the column, **When** the check runs,
   **Then** it **warns** rather than fails, and names it (Constitution III).
4. **Given** the pre-change template restored, **When** the check runs, **Then** it fails — proven by
   doing it, not by reading the code (`CON-PROC-005`).

---

### User Story 4 - The spec index tells the truth (Priority: P3)

As a maintainer, `specs/README.md` lists every spec, because an index that silently omits most of
them is worse than no index.

**Why this priority**: Found while writing this spec — the registry listed 4 of 11 specs. Small, but
it is a document whose entire purpose is to be complete, with nothing asserting that it is. Fixing
the rows without adding the check would let it drift again by the next PR.

**Acceptance Scenarios**:

1. **Given** a spec directory with no row in `specs/README.md`, **When** spec hygiene runs, **Then**
   it fails and names the directory.
2. **Given** a row pointing at a directory that does not exist, **When** it runs, **Then** it fails.
3. **Given** the corrected registry, **When** it runs, **Then** it passes.

## Requirements *(mandatory)*

### Functional

- **FR-001**: The artwork-page image is sized by **width** to the 1000 px column, not by longest edge.
- **FR-002**: It is never upscaled past the master; the source resolution is the ceiling. A master
  narrower than 1000 px is served at its own width.
- **FR-003**: `AutoOrient` is applied **before** the image is measured or resized, so an EXIF-rotated
  master is sized on the dimensions the visitor will actually see.
- **FR-004**: The page keeps `srcset` and `sizes`, with `sizes` stating the image's true CSS width so
  the browser's choice stays correct.
- **FR-005**: The existing 1600 px lightbox variant continues to serve as the retina candidate; no new
  variant is generated for it.
- **FR-006**: Landscape and square paintings are byte-for-byte unchanged in geometry.
- **FR-007**: `check-output.py` gains a column-fill assertion for artwork pages: an error when the
  served width is below the column and the master could have covered it, a warning when the master
  could not.
- **FR-008**: `check-specs.py` asserts that `specs/README.md` lists every spec directory and no
  others.
- **FR-009**: Sizing lives in the root `layouts/` override, never in the vendored theme
  (Constitution IX).

### Non-functional

- **NFR-001**: Published site stays under **40 MB** (Constitution IV).
- **NFR-002**: Cache-warm build stays under **15 s** (Constitution IV).
- **NFR-003**: **Geometry changes, and that is the intended result.** This is the exact inverse of
  `006` NFR-003, which required geometry to stay identical. Visual-regression baselines are therefore
  re-recorded, and the before/after measurements are stated so the change is reviewed rather than
  waved through.
- **NFR-004**: No change to CSS, typography, spacing or the palette — only which variant the template
  asks Hugo for.
- **NFR-005**: No new dependency.

## Success Criteria

- **SC-001**: Every portrait artwork page whose master allows it is displayed at **1000 px** wide,
  measured in a browser — up from 577–792 px. The count of pages that changed is stated.
- **SC-002**: The 23 landscape and square pages are measured and **unchanged**.
- **SC-003**: `/about/` (master 739 px wide, the one master below the column) is served at 739 px,
  **not upscaled**, and the gate warns rather than errors.
- **SC-004**: Restoring the old directive fails the new assertion. Demonstrated by doing it.
- **SC-005**: Published payload measured and under 40 MB; warm build measured and under 15 s; both
  figures in the PR.
- **SC-006**: Baselines re-recorded deliberately, with the measured geometry table as the evidence.
- **SC-007**: Spec hygiene fails on a spec directory missing from the registry. Demonstrated.

## Out of Scope

- The grid, which `006` already sized by width.
- The lightbox's 1600 px variant, correctly sized for its purpose.
- Re-encoding, renaming or replacing any master (Constitution VI).
- Changing the 1000 px column itself, or any CSS.
- WebP/AVIF — measured and rejected in `000-backend-optimization`; nothing has changed.
- Mobile and tablet viewport baselines, which `008-test-strategy` owns.
