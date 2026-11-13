# Feature Specification: A Strict Style Policy

**Feature Branch**: `020-strict-style-src`

**Created**: 2026-11-13

**Status**: Implemented — PR #41

**Input**: The known debt recorded in `010-security-gates` and `docs/security.md`: `style-src`
needed `'unsafe-inline'` — "the one weak directive" — because of inline `style=` attributes.

## Problem

The Content-Security-Policy was strict for scripts and lax for styles:
`style-src 'self' 'unsafe-inline'`. An injected `style=` attribute can restyle a page, hide or
overlay content, or exfiltrate through CSS selectors; `'unsafe-inline'` lets all of it through.

Measured on `main` @ `2c1f718`:

| | |
| --- | --- |
| `style=` attributes in the built site | **368**, on 11 pages |
| Their source | **one** template, `layouts/partials/album-card.html` — 4 per card, 46 cards, home + category pages |
| `<style>` blocks | 0 |
| Patterns | 3 fixed (identical on every card) + 1 per-painting background colour |

### The per-painting colour had never rendered

The fourth attribute was `background-color: <the painting's dominant colour>`. But `custom.css`
sets `.card > figure { background: none !important }`, and an `!important` stylesheet
declaration beats a non-important inline style. Measured: **all 144 card figures** across three
pages and two viewports computed `rgba(0, 0, 0, 0)`. It was dead markup, so it is dropped — not
ported to a generated stylesheet, which would have added a request to change nothing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nothing a visitor sees changes (Priority: P1)

**Acceptance Scenarios**:

1. **Given** every card on the home and category pages, **When** the change is made, **Then**
   their computed styles are **identical** — checked property by property, not by screenshot
   tolerance.
2. **Given** every existing screenshot baseline, **When** the suite runs, **Then** it passes with
   **nothing re-recorded**.

### User Story 2 - The policy forbids inline styles, and nothing breaks (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the built site, **When** it is inspected, **Then** `style-src` is `'self'` with no
   `'unsafe-inline'`.
2. **Given** every page type and every interaction — scrolling, lazy loading, the menu, opening and
   closing the lightbox — **When** a browser listens for `securitypolicyviolation`, **Then** there
   are **none**. JavaScript can inject styles at runtime, which no markup check can see.
3. **Given** an inline style injected into a page, **When** the policy is in force, **Then** it is
   **blocked** — proving the listener can hear a violation at all.

### User Story 3 - It cannot quietly regress (Priority: P1)

A blocked inline style fails **silently**: the element just renders unstyled.

**Acceptance Scenarios**:

1. **Given** a template that emits a `style=` attribute or `<style>` block on a page whose
   `style-src` is strict, **When** output assertions run, **Then** they fail and name the page.
2. **Given** `'unsafe-inline'` restored to the policy, **When** the browser suite runs, **Then**
   the enforcement test fails.
3. **Given** the deployed site, **When** the live check runs, **Then** it reports whether
   `style-src` is strict.

## Requirements *(mandatory)*

- **FR-001**: `album-card.html` emits no `style=` attribute; the fixed layout is `.abp-card*`
  classes in `custom.css`, specific enough to beat the theme's `.card` rules as the inline styles
  did.
- **FR-002**: The dead per-painting background colour is removed.
- **FR-003**: `style-src 'self'`, without `'unsafe-inline'`.
- **FR-004**: `check_style_csp_matches_the_markup` in `check-output.py`.
- **FR-005**: `tests/visual/csp.spec.js` — no violations across pages and interactions, plus an
  enforcement self-test.
- **FR-006**: `check-live.py` asserts the deployed `style-src` is strict.

## Success Criteria

- **SC-001**: 0 `style=` attributes in the built site (was 368).
- **SC-002**: 0 of 9,216 computed properties differ across 144 cards.
- **SC-003**: All screenshot baselines pass unchanged.
- **SC-004**: 0 CSP violations in a browser; the enforcement self-test passes.
- **SC-005**: Each new check demonstrated red on the defect it guards.

## Out of Scope

- Clickjacking and MIME-sniffing headers — unachievable on GitHub Pages (`docs/security.md`).
- The theme's own templates. Every card on this site comes from the project override; the
  theme's `album-card.html` and `featured.html` never render here.
