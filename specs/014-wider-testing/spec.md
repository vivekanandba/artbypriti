# Feature Specification: Test What the Suite Still Cannot See

**Feature Branch**: `014-wider-testing`

**Created**: 2026-10-30

**Status**: Draft

**Input**: The remaining item of the post-merge plan — "E2E journeys, lightbox, **mobile 375 /
tablet 768** screenshots, 404; `axe-core` accessibility (currently zero); `shellcheck` on
`scripts/*.sh` and the hooks; `bandit` on the Python."

## Problem

`008-test-strategy` took the gate scripts from 0% to 99% coverage, and `001-quality-gates` records
how pages look. Both are real. Four gaps survive them, and each is a place where a defect would
reach the live site unseen.

**1 · Nothing checks accessibility.** Zero coverage, on a site whose whole purpose is showing
images to people. An image that loses its `alt`, a control that stops being reachable by keyboard,
a contrast regression in `custom.css` — none of it fails anything today.

**2 · Nothing is checked at the sizes most people use.** Every baseline is 1280×900. This is the
sharpest gap, because `006` and `011` both added `sizes` attributes whose *entire purpose* is to
change which image a narrow screen downloads — and no test has ever rendered this site narrow.
The code paths added by the last two image changes are the ones with no coverage at all.

**3 · The suite checks pages, not journeys.** The lightbox is the one piece of real interactivity
on the site; it is asserted to *point at* the right file, never actually opened. The 404 page has
no test of any kind.

**4 · The code that runs the gates is not itself checked.** Five shell files — two scripts and
three hooks — and seven Python scripts. `CON-COV-001`: application coverage says nothing about
whether software ships; the delivery path needs testing too. A bug in `pre-push` silently stops
gating commits.

### Measured before designing anything

| Probe | Result |
| --- | --- |
| axe-core, WCAG 2.0/2.1 A + AA, 6 pages | **0 violations** |
| axe self-test (inject a missing `alt`) | **detected, critical** — so the zero is real, not a misconfigured tool |
| `shellcheck` v0.10.0, strictest severity, 5 shell files | **0 findings**, exit 0 |
| `shellcheck` on a planted unquoted `rm -rf $DIR/build` | **exit 1**, SC2086 — the check works |
| `bandit` 1.9.2 over `scripts/` + `tests/` | 225 findings: **1 Medium**, 224 Low |
| The 1 Medium | `B310` — `urlopen` in `check-live.py` accepts **any** scheme, including `file://` |

Two consequences shape this spec. The accessibility and shell baselines are **already clean**, so
their gates can be set at zero and act as regression guards from day one — no backlog to negotiate.
The bandit finding is **real** and is fixed here, not suppressed around.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The gallery stays usable to people who are not using a mouse and a big screen (Priority: P1)

As a visitor using a screen reader, keyboard, or a phone, the site keeps working, and a change that
breaks it fails before it ships.

**Why this priority**: The site's product is images. Accessibility is how a visitor who cannot see
them gets anything at all, and it currently has no coverage whatsoever.

**Independent Test**: Run axe against representative pages; zero violations at WCAG 2.0/2.1 A + AA.

**Acceptance Scenarios**:

1. **Given** any representative page, **When** axe runs at WCAG 2.0/2.1 A + AA, **Then** it reports
   **zero** violations — the measured baseline today, so the gate starts clean.
2. **Given** a page with a genuine violation introduced, **When** the gate runs, **Then** it
   **fails** and names the rule, the impact and the offending element.
3. **Given** the artwork page, **When** the gate runs, **Then** the painting's `alt` text is among
   the things covered — the single most important accessible fact on this site.

---

### User Story 2 - The site is tested at the sizes it is actually read at (Priority: P1)

As a visitor on a phone or tablet, the layout and the image I am served are correct, and a
regression at those widths is caught.

**Why this priority**: `006` and `011` added `sizes` attributes that only take effect on narrow
viewports. Those code paths have **never been rendered by a test**. The most recently changed
behaviour is the least covered.

**Acceptance Scenarios**:

1. **Given** a **375 px** viewport, **When** the home and artwork pages render, **Then** they match
   committed baselines.
2. **Given** a **768 px** viewport, **When** they render, **Then** they match committed baselines.
3. **Given** a narrow viewport, **When** an artwork page loads, **Then** the browser selects a
   variant appropriate to that width rather than the desktop one — asserted on the *selected*
   image, not on the markup that offers it.
4. **Given** a layout regression at a narrow width only, **When** the suite runs, **Then** it
   fails. Demonstrated.

---

### User Story 3 - The one interactive thing on the site is exercised (Priority: P2)

As a visitor, clicking a painting opens the lightbox and shows the large image; and a wrong URL
gets a real 404 page rather than nothing.

**Why this priority**: The lightbox is asserted to *point at* a derived variant but has never been
opened by a test, so "it points at the right file" and "it works" are different claims and only
the first is checked.

**Acceptance Scenarios**:

1. **Given** an artwork page, **When** the painting is clicked, **Then** the lightbox opens and
   displays an image.
2. **Given** the lightbox is open, **When** it is dismissed, **Then** the page returns to its
   previous state.
3. **Given** a URL that does not exist, **When** it is requested, **Then** the 404 page renders
   with the site's navigation, not a bare server error.

---

### User Story 4 - The gates' own code is checked (Priority: P2)

As a maintainer, a bug in a hook or a gate script fails CI rather than silently disabling the
protection it provides.

**Why this priority**: `CON-COV-001`. A broken `pre-push` stops gating commits and nothing says so;
the suite would stay green while the gates quietly stopped running.

**Acceptance Scenarios**:

1. **Given** the shell scripts and hooks, **When** `shellcheck` runs at its strictest severity,
   **Then** it reports **zero** findings — the measured baseline.
2. **Given** a shell defect introduced (an unquoted path in an `rm`), **When** it runs, **Then** it
   **fails**. Demonstrated.
3. **Given** the Python, **When** `bandit` runs at **medium severity and above**, **Then** it
   reports zero findings.
4. **Given** the `B310` finding, **When** it is addressed, **Then** it is addressed by **validating
   the URL scheme**, not by suppressing the message — and the suppression that remains exists only
   because bandit blacklists the call itself and cannot see a runtime guard.

## Requirements *(mandatory)*

### Functional

- **FR-001**: An accessibility gate runs axe-core at WCAG 2.0/2.1 A + AA over representative pages
  and fails on any violation.
- **FR-002**: Visual baselines exist at **375 px** and **768 px** for the home and artwork pages.
- **FR-003**: A test asserts the *selected* image variant at a narrow viewport, exercising `sizes`.
- **FR-004**: A test opens and dismisses the lightbox.
- **FR-005**: A test asserts the 404 page renders as a site page.
- **FR-006**: `shellcheck` runs over all shell scripts and hooks at its strictest severity and
  gates CI.
- **FR-007**: `bandit` runs over the Python at medium severity and above and gates CI.
- **FR-008**: `check-live.py` validates that a URL's scheme is `http` or `https` before fetching it,
  with a unit test.
- **FR-009**: Both linters are runnable locally by one `make` target each, pinned to the exact
  version CI uses.
- **FR-010**: Linters run in containers or via `uv`, because neither is installed on this machine
  or guaranteed on the runner (`CON-VER-004`).

### Non-functional

- **NFR-001**: The only new dependency is `@axe-core/playwright`, test-only, pinned, and covered by
  the existing `npm audit` gate.
- **NFR-002**: New baselines are viewport-sized, not full-page, where full-page would commit
  multi-megabyte PNGs (`001` NFR on repository weight).
- **NFR-003**: The coverage floor ≥95% continues to hold.
- **NFR-004**: No change to the site's own output. This spec adds tests; the **only** production
  change is the URL-scheme guard in a developer healthcheck script.

## Success Criteria

- **SC-001**: axe reports **0** violations across the covered pages, and a planted violation fails
  the gate. Both demonstrated.
- **SC-002**: Baselines committed at 375 px and 768 px, and a narrow-only regression is shown to
  fail.
- **SC-003**: The lightbox is opened and dismissed by a test that fails if it stops opening.
- **SC-004**: `shellcheck` exits 0 on the real files and 1 on a planted defect. Both demonstrated.
- **SC-005**: `bandit` at medium+ exits 0, with the one real finding **fixed** rather than filtered.
- **SC-006**: `make check-all` exits 0; coverage ≥95%.
- **SC-007**: Every new assertion is mutation-tested or shown failing before it is trusted
  (`CON-PROC-005`).

## Out of Scope

- **Fixing accessibility problems** — there are none to fix at A/AA today; this gate keeps it that
  way. A deliberate push to AAA is its own decision.
- **Performance budgets / Lighthouse.** Payload is already gated; a speed budget is a separate
  conversation.
- **Cross-browser testing.** The baselines depend on one pinned container's font rendering
  (`001` FR-006); adding engines multiplies baselines and is not free.
- **Refactoring the 184 inline `style=` attributes** that keep `style-src` from going strict —
  recorded in `010-security-gates` as its own change.
- **Testing the vendored theme's own JavaScript.** It is upstream code (`themes/gallery/UPSTREAM.md`).
