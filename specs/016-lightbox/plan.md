# Implementation Plan: Make the Lightbox Work

**Spec**: [spec.md](./spec.md) · **Branch**: `016-lightbox` · **Created**: 2026-10-31

## The decision, and why this way round

`014` left two legitimate closures: **make it work**, or **delete ~99 KB of dead payload**.
Chosen: make it work.

- The bytes are already being shipped, so "fixing" costs nothing extra that deleting would save.
- The markup was built for it — `data-pswp-src`, `-width`, `-height`, `-caption` are all already
  emitted, and the dimensions caption exists purely to be shown there.
- The current behaviour is the worst option on offer: a click dumps the visitor on a bare JPEG
  with no navigation.

Deleting instead remains a one-file change if the owner prefers it later.

## Approach

Two project files. **No theme file is touched** (Constitution IX).

| File | Role |
| --- | --- |
| `assets/js/artwork-lightbox.js` | Initialises PhotoSwipe scoped to `.gallery-single-centered` |
| `assets/js/main.js` | Project override of the theme's 5-line entrypoint |

`main.js` drops the theme's `gallery.js` and `lightbox.js` — neither can run, both key off
`#gallery` — and adds the new module. PhotoSwipe is **imported from the theme's assets**, not
copied, so it is bundled exactly once.

### Why not just add `id="gallery"`

Tried first, and measured. The lightbox worked, and `gallery.js` — which keys off the same id —
absolutely-positioned the painting into a 288 px justified row. **Five screenshot baselines
failed.** The id means two things; this page wants one of them.

That failure is the argument for scoping to the artwork section instead: the new module cannot
reach the home grid even if `#gallery` is reintroduced for its original purpose one day.

## Verification

Behaviour measured in a browser, not inferred:

| Property | Method |
| --- | --- |
| Opens, stays on the page | Probe + test: `.pswp` root created, `page.url()` unchanged |
| Nothing else moves | **All** existing baselines pass with no re-recording |
| Listing pages untouched | Zero `.pswp` roots on `/` and a category page |
| Serves a derived variant | `src` contains `_hu_`, never the master |
| Keyboard dismissal | Escape on a settled lightbox; body not scroll-locked |
| Not a trap | Early Escape, then settle, then Escape → closed |
| Bundle | `main.js` size before/after |

## The Escape quirk, and how the test was got right

Three wrong versions of one test, each of which taught something:

1. **`toBeHidden()` after Escape** — failed. PhotoSwipe *removes* its root rather than hiding it,
   so absence (`toHaveCount(0)`) is the correct assertion.
2. **Escape as soon as `pswp--ui-visible` appears** — failed, and *reproducibly*. That class is
   set within ~150 ms while the zoom animation is still running, and PhotoSwipe swallows Escape
   until it settles. This is real behaviour, not a test artifact; a raw probe reproduced it.
3. **Pressing Escape twice in a row** — also failed. Both presses land inside the animation.

The property worth asserting is therefore neither "Escape always closes instantly" nor "press
twice": it is **an early press does not produce a state the visitor cannot leave**. Once settled,
Escape works. Recorded as incident #14 and asserted directly.

`lightboxSettled()` waits for geometry to stop changing rather than sleeping a fixed 333 ms —
the thing being waited for is "the animation finished", and measuring that directly is both
honest and robust (`CON-VER-008`: a timing assertion that depends on machine load is a defect).

## Risks

| Risk | Mitigation |
| --- | --- |
| A theme update adds a module to `main.js` and it silently never loads | The override says so in a comment and points at `UPSTREAM.md`; a theme bump must re-read it |
| PhotoSwipe bundled twice | Imported from the theme's assets, never copied; bundle size measured before/after |
| The lightbox leaks onto listing pages | Scoped to `.gallery-single-centered` and asserted on `/` and a category page |
| The download control exposes a master | It uses the anchor's `href`, which is the 1600 px variant; masters are not published at all, and `check-output.py` fails if one ever is |
