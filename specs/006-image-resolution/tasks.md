# Tasks: Stop Upscaling the Paintings

**Branch**: `006-image-resolution` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 0 — Establish the defect

- [x] **T001** Measure served width vs display width on both surfaces. *23 of 46 grid images stretched;
      root cause is `fit NxN` fitting the longest edge while the CSS constrains width.*
- [x] **T002** Cost the fix before committing to it: width-based sizing is **+29%**; a 1200w retina set
      would add ~7 MB.

## Phase 1 — Grid (US1, P1)

- [x] **T003** Root override `layouts/partials/get-gallery.html`: size by width, cap at the master,
      `AutoOrient` before measuring, return a `srcset`.
- [x] **T004** Root override `layouts/partials/album-card.html`: emit `data-srcset` / `data-sizes`.
- [x] **T005** Trim candidates to 400/600/900. *First build measured 46 MB — over budget. The 1200w set
      alone was 10.1 MB.*

## Phase 2 — Artwork page (US2, P2)

- [x] **T006** Size artwork pages by width. **Reverted.**
- [x] **T007** *Measured the rendered geometry and disproved my own premise:* `displayed == natural`
      there, so those pages were never upscaled — they under-filled. Sizing by width grew `/about/`
      from 1636 to 2368 px. Restored the original sizing and added only a `srcset` candidate, reusing
      the existing 1600 px lightbox variant (zero extra payload).
- [x] **T008** Correct the spec in place, rather than quietly dropping the claim.

## Phase 3 — Close the hole (US3, P1)

- [x] **T009** `check-output.py`: assert served width ≥ slot width, erroring when the master could have
      covered it and warning when it could not (Constitution III).
- [x] **T010** Stdlib JPEG/PNG header reader — no Pillow on a bare runner (NFR-004).
- [x] **T011** Scope the assertion to the grid. *An earlier version assumed a 1000 px slot on artwork
      pages and would have failed correct pages — the same wrong premise as T006.*
- [x] **T012** Prove it: re-introduce `Fit`, rebuild, watch it fail; restore, watch it pass.

## Phase 4 — Record

- [x] **T013** Re-record baselines. Only home and category changed, at **identical dimensions** —
      the evidence that this is sharpness and not layout.
- [x] **T014** `UPSTREAM.md`: record the two newly shadowed theme files and that the theme's copies
      are now dead code.

## Deferred

- [ ] **T015** Whether artwork pages *should* show paintings larger (filling the 1000 px column) —
      a design decision for the artist. Pages would grow 24–45% taller.
- [ ] **T016** 1200w grid candidates, if the payload budget is ever raised.
- [ ] **T017** A higher-resolution master for `about` (739 px); only the artist can supply it.
