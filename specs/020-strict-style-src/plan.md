# Implementation Plan: A Strict Style Policy

**Spec**: [spec.md](./spec.md) · **Branch**: `020-strict-style-src` · **Created**: 2026-11-13

## Approach

1. Find every inline style in the **built output**, not the templates: 368, all from one
   override.
2. Snapshot the computed style of every card element **before** changing anything — 16
   properties × 4 elements × 144 cards at two viewports.
3. Replace the three fixed patterns with classes; drop the fourth (dead).
4. Re-snapshot and diff. The bar is **zero** differences, because pixel tolerance would let a
   small shift through.
5. Make `style-src` strict, then listen in a browser for violations while exercising everything
   that runs JavaScript.
6. Leave three gates: markup (build time), browser (runtime), live (deployed).

## Why classes with three-class specificity

An inline style outranks every non-`!important` selector. The theme styles `.card > figure` and
`.card figure > img`, and the inline styles used to win against those. A class rule only wins if
it is more specific, hence `.card.abp-card > .abp-card__figure`. Where `custom.css` has
`!important` rules, the inline style already lost and the class loses the same way. The diff is
what proves this reasoning, not the reasoning itself.

## The colour that was never there

I first designed a generated, fingerprinted stylesheet — one `.bg-<hex>` rule per painting — to
carry the per-painting colour without inline styles. The before-snapshot showed it was pointless:
every figure computed transparent, because `custom.css` forces `background: none !important`.
Built and then removed before commit; the measurement made the design unnecessary.

## Verification

| Check | Result |
| --- | --- |
| `style=` in built HTML | 368 → **0** |
| Computed-style diff | **0 of 9,216** differ |
| Screenshot baselines | **all pass, none re-recorded** |
| Browser CSP violations | **0**, across 6 pages, menu, lightbox open/close |
| Markup gate red | one `style=` restored to the card → 11 pages named, exit 1 |
| Browser gate red | `'unsafe-inline'` restored → enforcement test fails |
