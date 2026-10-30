# Tasks: Show the Paintings Larger on Their Own Page

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Branch**: `011-larger-artwork`

Order matters here: the geometry was measured **before** anything changed, so the "after" numbers
have something honest to be compared against. Every claim below is a measurement, not a reading of
the template (`CLAUDE.md`: on this repository, reasoning from templates has produced confident wrong
conclusions more than once — and did so again in T009).

## Measure first

- [x] **T001** Verified the parent commit's deploy is live and healthy before building on it —
  `check-live.py` clean, and the PWA chain confirmed by hand on the running site (script tag →
  fingerprinted `sw-register.js` → a real `serviceWorker.register` call → `sw.js` → manifest, with
  0 inline scripts under `script-src 'self'`). PR #26 was the first deploy carrying CSP and the
  service worker together, so this was not assumed.
- [x] **T002** Probed the rendered geometry of 5 representative pages in the pinned Playwright
  container: rendered box, natural pixels, served variant, `sizes`, `srcset`, page height.
  Confirmed `displayed == natural` everywhere — the page under-fills, it does not stretch.
- [x] **T003** Measured every master. **Exactly one** is narrower than the 1000 px column:
  `about/Priti-Ghatlia.jpeg` at 739 px. This corrected the pre-measurement estimate, which had
  predicted `/about/` would reach 1000 px and grow to 2368 px tall — it cannot, and does not.
- [x] **T004** Counted the blast radius from the masters: **24 of 47** images grow (every portrait),
  **23 unchanged**, growth factor up to **1.50×**.

## Implement

- [x] **T005** `layouts/partials/gallery.html`: sized by width to the column, capped at the master,
  `AutoOrient` applied before measuring. Replaced the comment block that recorded why spec 006
  deliberately left this alone, since that reason no longer holds.
- [x] **T006** Rebuilt and re-probed. Portrait pages grew as predicted; landscape and square pages
  unchanged; nothing upscaled.

## The measurement that changed the implementation

- [x] **T007** Visual regression failed `/olive/` at a **0.40** pixel ratio — a page whose measured
  geometry had **not moved**. Treated as a contradiction to explain rather than a baseline to
  re-record.
- [x] **T008** Found the cause: the first implementation derived the variant from the
  already-filtered `$oriented` resource, so it resampled a processed intermediate instead of the
  master. Every landscape and square variant changed bytes.
- [x] **T009** Quantified it before deciding, rather than acting on the hunch that it was a double
  JPEG encode — it was not. **0.15 dB** worse against a Lanczos reference (34.87 → 34.72 dB), with
  42.20 dB agreement between old and new: real, small, and in the wrong direction.
- [x] **T010** Switched to a single `Filter` pipeline over the master, keeping `$oriented` only to
  supply the width. The 23 unchanged variants are now **byte-identical** to what shipped before —
  verified by checksum, not by the screenshot passing.

## Leave a gate behind

- [x] **T011** `check_artwork_fills_its_column` in `scripts/check-output.py`: errors when an artwork
  image is served below the 1000 px column while its master could have covered it, warns when the
  master could not (Constitution III), and reports **"cannot determine"** when the served variant is
  wider than the master as measured — the EXIF-rotation case, where the comparison itself is
  unsound (`CON-VER-005`). Deliberately **separate** from `check_no_upscaling`: this page can waste
  its column but can never stretch an image, so pointing the upscaling check here would have been
  the wrong assertion wearing the right name.
- [x] **T012** Proved it red before trusting it green: restored the old directive, rebuilt, and
  watched the gate fail with **23 named errors** (exit 1) while `/about/` correctly degraded to a
  warning. Restored → 0 errors (`CON-PROC-005`).
- [x] **T013** 8 unit tests for the new check, including the uncertainty path and the grid-exemption
  path. Mutation-tested twice — `ARTWORK_COLUMN = 1`, and routing errors to the warning bucket — and
  both mutations were caught. A test that has never been red proves nothing.
- [x] **T014** Added `/ganesha-with-lines/` to the visual suite. The suite's only artwork page was
  `/olive/`, which is **landscape** — so the entire portrait half, the subject of this change, had
  no baseline at all. Verified the new baseline fails on reversion and passes on restore.

## A gap found on the way

- [x] **T015** `specs/README.md` listed **4 of 11** specs. Added the 7 missing rows with each
  spec's real merged PR (read from the merge history, not inferred), and recorded two numbering
  facts rather than tidying them away: there is no `007`, and `010` was `009` first.
- [x] **T016** `check_registry` in `scripts/check-specs.py` fails when the directories on disk and
  the rows in the table disagree, in either direction. 5 unit tests, mutation-tested. The index
  drifted for seven features precisely because nothing asserted it was complete (`CON-PROC-011`).
- [x] **T017** Recorded, rather than silently reconciled, that several merged specs still carry
  `Status: Draft` in their own headers while the registry calls them Implemented (`CON-DATA-003`).

## Verify

- [x] **T018** `make check` → **exit 0**.
- [x] **T019** `make coverage` → **140 tests pass, 99%**, floor ≥95% holds (`check-specs.py` at 100%).
- [x] **T020** `make visual` → **8 passed**, exactly one baseline re-recorded (`about-linux.png`)
  plus one added (`artwork-portrait-linux.png`).
- [x] **T021** Payload **35,709,224 → 36,848,766 bytes** (+1.09 MiB, **+3.2%**); the gate reads
  33.8 → 34.9 MB against a 40 MB budget. Warm build **1.35 s** against a 15 s limit.

## Deliberately not done

- **Mobile and tablet baselines.** `sizes` now states a larger width, and its effect at 375/768 px
  is unmeasured here. That belongs to `008-test-strategy`, which already owns viewport coverage;
  noted rather than quietly skipped (`CON-REP-002`).
- **Correcting the stale `Status: Draft` headers** in nine merged specs. Recorded in the registry
  as a known disagreement; a nine-file sweep does not belong in this change.
- **Any CSS change.** The 1000 px column is unchanged; only which variant the template requests.
