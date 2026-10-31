# Feature Specification: Make the Lightbox Work

**Feature Branch**: `016-lightbox`

**Created**: 2026-10-31

**Status**: Draft

**Input**: The open question left by `014-wider-testing`, which found the lightbox had never
worked and deliberately did not fix it: *"restoring the lightbox or deleting ~99 KB of dead
payload is the owner's design call, not a testing change."* The owner has now asked for it to be
closed.

## Problem

Clicking a painting **navigates away to a bare JPEG** — no site navigation, no caption, no way
back except the browser's Back button. The lightbox the theme ships for exactly this purpose has
never run.

`themes/gallery/assets/js/lightbox.js` initialises only inside
`if (document.getElementById("gallery"))`. That `#gallery` div lives in the **listing branch** of
`layouts/partials/gallery.html` — the branch `CLAUDE.md` already records as never rendering,
because the home page uses the theme's `home.html` → `album-card.html`.

Measured on the built site before this change:

| | |
| --- | --- |
| Pages containing `#gallery` | **0** |
| PhotoSwipe roots ever created | **0** |
| Result of clicking a painting | navigates to `/olive/Olive_hu_….jpg` |
| Dead payload shipped to every visitor | **~94 KB** of `main.js`, **~5.3 KB** of CSS |

So the site pays for a lightbox on every page load and no visitor has ever seen one.

### The obvious fix is wrong, and was measured

Adding `id="gallery"` to the artwork wrapper makes the lightbox initialise — and **breaks the
page**. `themes/gallery/assets/js/gallery.js` keys off the *same id* and unconditionally
absolutely-positions every `.gallery-item` into a 288 px justified row. Tried: the lightbox
worked and **five screenshot baselines failed**.

The id is overloaded — it means both "lightbox root" and "justified grid root" — and a
single-painting page wants only the first. Any fix has to separate them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A visitor can see the painting large without leaving the page (Priority: P1)

As a visitor, clicking a painting shows it as large as my screen allows, over the page, with its
dimensions; closing it returns me exactly where I was.

**Why this priority**: This site exists to show paintings. Navigating a visitor to a bare image
file is the worst available answer to "I'd like to see that bigger".

**Independent Test**: Click a painting; a lightbox opens showing the image, and the page URL does
not change.

**Acceptance Scenarios**:

1. **Given** an artwork page, **When** the painting is clicked, **Then** the lightbox opens and
   displays the image, and **the browser does not navigate away**.
2. **Given** the lightbox is open, **When** it is dismissed, **Then** the page is unchanged
   underneath and is not left scroll-locked.
3. **Given** the lightbox is open, **When** the image is shown, **Then** it is a Hugo-derived
   variant — the full-resolution master is not published and must stay unreachable.
4. **Given** the painting has `dimensions` in front matter, **When** the lightbox opens, **Then**
   the caption shows them.

---

### User Story 2 - Nothing else on the site moves (Priority: P1)

As a maintainer, enabling the lightbox changes no layout anywhere.

**Why this priority**: The first attempt at this change silently reflowed every artwork page. A
fix for a click handler must not be a redesign.

**Acceptance Scenarios**:

1. **Given** every existing visual baseline, **When** the suite runs, **Then** **all** of them
   pass unchanged — desktop, 375 px and 768 px.
2. **Given** the home and category pages, **When** they load, **Then** **no** lightbox is
   initialised; the module cannot reach them.
3. **Given** the vendored theme, **When** this ships, **Then** **no file under `themes/`** is
   modified (Constitution IX).

---

### User Story 3 - A keyboard user is never trapped (Priority: P1)

As a visitor using a keyboard, I can always dismiss the lightbox.

**Why this priority**: An overlay that cannot be closed without a mouse is an accessibility
failure, not a rough edge.

**Acceptance Scenarios**:

1. **Given** an open, settled lightbox, **When** Escape is pressed, **Then** it closes.
2. **Given** Escape is pressed **during the opening animation**, **When** it is swallowed,
   **Then** the lightbox is still closable afterwards — an early press must not produce a state
   it can never leave.
3. **Given** the lightbox has closed, **When** the page is inspected, **Then** `body` is not left
   with `overflow: hidden`.

---

### User Story 4 - The dead code goes (Priority: P2)

As a maintainer, modules that cannot run are not shipped.

**Acceptance Scenarios**:

1. **Given** the built bundle, **When** it is measured, **Then** it no longer contains the
   justified-layout grid code, which has no element to act on.
2. **Given** PhotoSwipe, **When** the bundle is built, **Then** it appears **once** — the fix must
   not duplicate it.

## Requirements *(mandatory)*

### Functional

- **FR-001**: The artwork page opens its painting in a lightbox instead of navigating.
- **FR-002**: The lightbox root is scoped to the artwork page's own section, **never** `#gallery`,
  so the theme's justified-layout cannot fire.
- **FR-003**: The lightbox shows the `dimensions` caption.
- **FR-004**: A download control preserves the visitor's previous ability to open the large image,
  pointing at the derived variant.
- **FR-005**: Listing pages initialise no lightbox.
- **FR-006**: No file under `themes/` is modified; this ships as project overrides
  (Constitution IX).
- **FR-007**: The theme's `gallery.js` and `lightbox.js` are dropped from the bundle, since
  neither can run.
- **FR-008**: PhotoSwipe is **imported** from the theme, not copied, so it is bundled once.

### Non-functional

- **NFR-001**: Every existing visual baseline passes **unchanged**.
- **NFR-002**: The published payload does not grow.
- **NFR-003**: No new dependency.
- **NFR-004**: Still no inline `<script>`, so `script-src 'self'` stays strict (spec 010).

## Success Criteria

- **SC-001**: Clicking a painting opens the lightbox and the URL does not change. Demonstrated.
- **SC-002**: All visual baselines pass with **no** re-recording.
- **SC-003**: Escape closes a settled lightbox; an early Escape never traps the visitor. Both
  asserted.
- **SC-004**: Home and category pages create zero PhotoSwipe roots.
- **SC-005**: `main.js` is **no larger** than before; the measured size is stated.
- **SC-006**: `make check-all` exits 0.

## Out of Scope

- **Changing the theme.** It is vendored; see `themes/gallery/UPSTREAM.md`.
- **Fixing PhotoSwipe's mid-animation Escape quirk.** Upstream behaviour, not trapping, recorded
  as incident #14 and asserted against.
- **Deep-linking** a lightbox via the URL hash. Meaningful for a gallery listing, pointless on a
  page that already *is* one painting — and the theme's version writes `#undefined` here.
- **Re-enabling the justified grid.** The home page uses the theme's album-card layout, which is a
  separate design decision nobody has asked for.
