# Tasks: A Strict Style Policy

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Branch**: `020-strict-style-src`

## Measure

- [x] **T001** Counted inline styles in `public/`: **368** on 11 pages, all from
  `layouts/partials/album-card.html` (4 per card). 0 `<style>` blocks. `docs/security.md` had said
  "184 on the home page" — that was the home page alone.
- [x] **T002** Captured the computed style of every card element before any change: 144 cards,
  three pages, two viewports.
- [x] **T003** Found the per-painting colour **never rendered**: all 144 figures computed
  `rgba(0, 0, 0, 0)`, because `.card > figure { background: none !important }` beats inline.

## Change

- [x] **T004** Built a generated `.bg-<hex>` stylesheet for the colour, then deleted it before
  committing once T003 showed it would change nothing.
- [x] **T005** `album-card.html` emits classes only; `.abp-card*` rules in `custom.css` at
  three-class specificity.
- [x] **T006** `style-src 'self'` — `'unsafe-inline'` removed.

## Prove

- [x] **T007** Re-snapshot: **0 of 9,216** computed properties differ.
- [x] **T008** Every screenshot baseline passes; none re-recorded.
- [x] **T009** Browser probe: **0** CSP violations across home, a category page, about, request,
  404 and an artwork page, plus the menu and the lightbox opened and closed.

## Gates

- [x] **T010** `check_style_csp_matches_the_markup` — 6 unit tests, including Hugo's unquoted
  minified attributes and prose that merely contains "style=". Red end to end: one `style=`
  restored to the card → exit 1 naming 11 pages.
- [x] **T011** `tests/visual/csp.spec.js` — 8 tests, including an enforcement self-test that
  injects an inline style and expects it blocked. Red when `'unsafe-inline'` was restored.
- [x] **T012** `check-live.py` asserts the deployed `style-src` is strict; 3 unit tests.
- [x] **T013** `docs/security.md` and the CSP comment updated: the "one weak directive" is gone.

## Verify

- [x] **T014** `make check-all` exit 0.
