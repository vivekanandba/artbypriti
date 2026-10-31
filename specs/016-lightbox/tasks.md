# Tasks: Make the Lightbox Work

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Branch**: `016-lightbox`

## Decide, on evidence

- [x] **T001** Chose "make it work" over "delete ~99 KB". The bytes already ship, the markup
  (`data-pswp-*`, the dimensions caption) was built for it, and the status quo — a click dumping
  the visitor on a bare JPEG — is the worst option available. Deleting stays a one-file change if
  the owner prefers it later.

## The attempt that failed, kept because it shaped the design

- [x] **T002** Added `id="gallery"` to the artwork wrapper, plus `data-pswp-target` to avoid the
  theme writing `#undefined` into the URL. The lightbox **opened**.
- [x] **T003** It also **broke the page**: five screenshot baselines failed. Cause found by
  reading the theme rather than the diff — `gallery.js` keys off the *same id* and
  absolutely-positions every `.gallery-item` into a 288 px justified row. The id means both
  "lightbox root" and "justified grid root".
- [x] **T004** Reverted. The failure is why the final design scopes to the artwork section: the
  module then cannot reach the home grid even if `#gallery` returns for its original purpose.

## Build

- [x] **T005** `assets/js/artwork-lightbox.js` — PhotoSwipe scoped to `.gallery-single-centered`,
  with the dimensions caption and a download control that preserves the visitor's previous
  ability to open the large image. PhotoSwipe is **imported** from the theme, never copied.
- [x] **T006** `assets/js/main.js` — project override dropping the theme's `gallery.js` and
  `lightbox.js` (neither can run) and adding the new module. **No file under `themes/` touched.**

## Verify by observation

- [x] **T007** Probed all three page types: `/olive/` creates 1 PhotoSwipe root and
  **`navigated: false`** — the visitor stays on the page. `/` and a category page create **0**.
  Zero page errors anywhere.
- [x] **T008** **Every existing baseline passed with no re-recording** — desktop, 375 px and
  768 px. This is the one that matters: the first attempt failed five of them.
- [x] **T009** `main.js` **94,179 → 90,963 bytes**. Smaller, because the justified-layout code
  went and PhotoSwipe is still bundled once.

## Getting one test right, three times

- [x] **T010** `toBeHidden()` after Escape failed — PhotoSwipe **removes** its root rather than
  hiding it, so `toHaveCount(0)` is the correct assertion.
- [x] **T011** Pressing Escape as soon as `pswp--ui-visible` appears also failed — and a raw
  probe **reproduced it outside the test runner**, so this is real behaviour, not a test
  artifact. That class is set within ~150 ms while the zoom animation still runs, and PhotoSwipe
  swallows Escape until it settles.
- [x] **T012** Pressing Escape twice in a row failed too: both presses land inside the animation.
  An earlier probe had "proved" the second press works only because it happened to wait 1.5 s
  between them.
- [x] **T013** Settled on the property that is actually true and actually matters: **an early
  press does not produce a state the visitor cannot leave.** Once the animation settles, Escape
  closes it. Asserted directly, with `lightboxSettled()` waiting for geometry to stop changing
  rather than sleeping a fixed 333 ms (`CON-VER-008`).
- [x] **T014** Recorded as incident #14. Not "fixed": it is upstream behaviour in a vendored
  theme, it does not trap anyone, and patching vendored code to smooth a 300 ms edge would cost
  more than it buys.

## Records

- [x] **T015** Incident #11 updated — the lightbox is no longer dead, and the entry now carries
  what the fix was and why `id="gallery"` was not it.
- [x] **T016** Incident #14 added for the Escape quirk.
- [x] **T017** `CLAUDE.md` and `tests/README.md` updated: the dead-branch gotcha now also
  explains that `assets/js/main.js` is a project override, which a theme bump must re-read.
- [x] **T018** `docs/constitution-handoff.md` corrected — superseded by the fleet PR, which uses
  `CON-PROC-015` (014 was taken by another open branch) and **keeps** `CON-PROC-010` after
  checking it has never named a rule.

## Verify

- [x] **T019** `make visual` → **30 passed**, zero baselines re-recorded.
- [x] **T020** `make check-all` → exit 0.
- [x] **T021** Still zero inline `<script>`, so `script-src 'self'` stays strict.

## Deliberately not done

- **Patching the theme.** Vendored; the whole change is project overrides.
- **Fixing the mid-animation Escape quirk.** Upstream, non-trapping, asserted against.
- **Hash deep-linking.** Pointless on a page that already is one painting, and the theme's
  version writes `#undefined` there.
- **Re-enabling the justified grid.** The home page uses album-card by design.
