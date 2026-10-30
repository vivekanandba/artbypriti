# Questions only Priti can answer

Everything here is a **gap in the record**, not a defect in the site. A painting's size, its
description, the units it is measured in — these come from the artist. The gates warn about them
and deliberately do not fail, because no automation can supply a fact nobody has.

That is `CON-DATA-001` in practice: a field left blank because nobody looked is information; a
field filled by inference is a fabrication that later reads as fact. **Nothing below has been
guessed, and nothing should be filled in on her behalf.**

Generated from `python3 scripts/check-content.py` on **2026-10-30** (7 warnings across 6 artworks)
plus one measurement from `scripts/check-output.py`. Re-run those two to refresh it.

## 1 · Missing dimensions (3 paintings)

The size caption simply does not render on these pages.

| Painting | Page | What's needed |
| --- | --- | --- |
| Mosaic Coasters | `/mosaic-coasters/` | Dimensions, e.g. `(20 cm X 20 cm)` |
| Peace Stool | `/peace-stool/` | Dimensions — a stool, so possibly height × seat diameter; her call how to express it |
| Vegetables & Fruits on a Staircase | `/staircase/` | Dimensions |

Add to the page's `index.md` front matter as `dimensions: (W cm X H cm)`.

## 2 · Missing descriptions (2 paintings)

The subtext under the title is empty, so these two pages are barer than every other.

| Painting | Page |
| --- | --- |
| Pear with Pink Background | `/pear-with-pink-background/` |
| Vegetables & Fruits on a Staircase | `/staircase/` |

*(Staircase appears in both lists — it is missing a description **and** its dimensions.)*

## 3 · Units: inches where the rest of the site uses centimetres (2 paintings)

| Painting | Currently reads | Question |
| --- | --- | --- |
| Ganesha's Blessings | `(36 inch X 36 inch)` | Convert to cm (~91 × 91), or keep inches? |
| Modern Ganesha | `(12" Diameter)` | Convert to cm (~30), or keep inches? |

**This is a presentation choice, not an error.** The warning exists because the site is otherwise
consistently metric, and a visitor comparing two paintings sees two scales. Either answer is fine —
convert them, or decide the site shows whichever unit the work was made in. **It should not be
changed without her saying which.** The conversions above are arithmetic offered for convenience,
not a recommendation.

## 4 · One photograph is lower-resolution than the page can now show

Since spec `011-larger-artwork`, an artwork page displays its image up to **1000 px** wide. One
master cannot reach that:

| File | Master width | Displayed at |
| --- | --- | --- |
| `content/about/Priti-Ghatlia.jpeg` | **739 px** | 739 px |

It is **not** stretched — the site refuses to upscale, so it simply renders smaller than the
column. This is the artist's own photograph on the About page rather than a painting, so it may not
matter at all. If a larger original exists, dropping it in makes the page fill its column; if not,
nothing is wrong.

`check-output.py` reports this as a *warning* for exactly this reason: "the master is smaller" is a
fact about the source, not a bug in the site.

## What happens when these are answered

Edit the `index.md` in the painting's folder under `content/`. Content edits need no spec and no
review ceremony — `make check` will confirm the warning is gone. The warnings shrink as the record
fills in; they are a to-do list, not a failure.
