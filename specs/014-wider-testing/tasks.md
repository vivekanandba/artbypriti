# Tasks: Test What the Suite Still Cannot See

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Branch**: `014-wider-testing`

## Measure before specifying

- [x] **T001** Probed axe-core over 6 pages at WCAG 2.0/2.1 A + AA: **0 violations**.
- [x] **T002** Did not believe it. Injected an `<img>` with no `alt` into a real page and
  re-ran: axe reported `image-alt`, **critical**. A tool that has never reported anything is not
  evidence of a clean site.
- [x] **T003** Ran `shellcheck` v0.10.0 at its strictest severity over all 5 shell files:
  **0 findings**, exit 0 — captured from shellcheck itself, not through a pipe into `head`, which
  had silently reported the wrong status once already (`CON-VER-001`).
- [x] **T004** Planted an unquoted `rm -rf $DIR/build`: **exit 1**, SC2086. The tool works.
- [x] **T005** Ran `bandit` 1.9.2: **225 findings — 1 Medium, 224 Low**. Read the composition
  rather than the count: the Low ones are `assert` in tests and literal-argv `subprocess`.

## Build

- [x] **T006** Moved `settle()` into `tests/visual/helpers.js` and confirmed the move changed
  nothing (8 passed before and after).
- [x] **T007** `a11y.spec.js` — axe over 7 pages, reporting rule, impact and node count rather
  than a bare number.
- [x] **T008** `responsive.spec.js` — 375 px and 768 px baselines, a no-horizontal-overflow
  assertion (invisible in a viewport screenshot, since the overflow is off-screen), and a test
  that the *selected* variant at 375 px is not the desktop one.
- [x] **T009** `journeys.spec.js` — the click-through and the 404 page.
- [x] **T010** `@axe-core/playwright@4.14.0` pinned as a devDependency; lockfile updated.
- [x] **T011** `make lint` + CI steps for shellcheck and bandit.

## What the tests found

- [x] **T012** **The lightbox never initialises, anywhere.** `lightbox.js` runs only
  `if (document.getElementById("gallery"))`, and that div is in the listing branch of
  `gallery.html` — the branch `CLAUDE.md` already records as never rendering. Measured: **0**
  pages with `#gallery`, **0** `.pswp` roots, and a click **navigates to the raw JPEG**.
  PhotoSwipe (~94 KB of `main.js`, ~5.3 KB of CSS) ships to every visitor and never runs.
- [x] **T013** Did not "fix" it. Restoring the lightbox or deleting the dead bundle is a design
  decision for the owner, not a testing change. Rewrote the journey tests to guard the invariant
  that *does* hold — a click must never reach an 8 MB master — plus a clearly-named
  characterisation test that fails if someone wires the lightbox up, so that change is visible
  rather than silent. Recorded in `docs/incidents.md`.
- [x] **T014** **axe cannot catch the regression that matters most here.** Planted `alt=""` on
  the artwork image: **every axe check stayed green**, because an empty `alt` is the standard way
  to mark an image decorative. Correct in general; wrong where the image is the whole page.
- [x] **T015** Added a direct accessible-name assertion for the artwork page (the grid already
  had one), watched it fail on the planted defect, then restored. The axe gate alone would have
  shipped that.

## Fix the one real security finding

- [x] **T016** `check-live.py` validates that a URL's scheme is `http`/`https` before fetching.
  It took a URL from argv and `urlopen` serves `file://` quite happily, so a tool whose job is
  "fetch this and show me" would read local files on request (B310, CWE-22).
- [x] **T017** Verified the guard behaves: `file://` and `ftp://` refused, `https://` unaffected.
- [x] **T018** The remaining `# nosec B310` sits on one line and exists only because bandit
  blacklists the call and cannot see a runtime check — **the hole was closed first, then the
  message silenced.** Reworded the surrounding comment after bandit parsed its prose as rule
  names and emitted warnings.

## A test that could not fail

- [x] **T019** Mutated the scheme guard to `if False:` — **the tests still passed.** The test
  used a sentinel `urlopen` that raised, but `fetch()` catches broad `Exception` for network
  errors, so the raise was swallowed; and the sentinel's own message contained the word
  ("refusing") that the assertion grepped for. It could not fail.
- [x] **T020** Rewrote it to record calls and assert `urlopen` was **never called**. Re-ran the
  mutation: all four parametrised cases now fail. Restored: green. This is the second
  can't-fail test this session, both found the same way.

## Verify

- [x] **T021** `make lint` → **exit 0**, both linters clean, no warning noise.
- [x] **T022** `make test` → **168 passed, 99%**, floor ≥95%.
- [x] **T023** `make visual` → **27 passed**; 4 new baselines at 375/768.
- [x] **T024** Narrow-only regression proven caught: a CSS rule biting below 400 px failed
  **only** the two mobile baselines while desktop and tablet passed. That regression would have
  shipped invisibly before this change.
- [x] **T025** bandit proven red **in the container CI uses** (`python:3.12-slim`), not just
  locally: planted `subprocess(..., shell=True)` → exit 1, B602 High.
- [x] **T026** Checked bandit 1.9.2 requires **Python ≥ 3.10** while the self-hosted runners are
  Ubuntu 20.04 / python3 3.8, and containerised the CI step accordingly — before writing it,
  rather than discovering it from a red build.

## Deliberately not done

- **Fixing or removing the dead lightbox.** A design decision (restore it, or drop ~99 KB of dead
  payload?) that belongs to the owner. Recorded, measured, and guarded against silent change.
- **Fixing accessibility problems** — there are none at A/AA. AAA is a design commitment, not a
  defect threshold.
- **Cross-browser baselines.** Screenshots depend on one pinned container's font rendering;
  adding engines multiplies baselines.
- **Gating bandit at Low.** 224 suppressions nobody would read.
