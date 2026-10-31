# Art by Priti — working notes

> Machine-wide engineering rules live in the **engineering constitution** (`~/.claude/CLAUDE.md`, versioned at `~/data-dash/constitution`) and are already loaded in this session. Cite a rule ID (e.g. `CON-VER-001`) rather than restating it — copies drift, citations don't. This file holds only what is specific to this repo.


A Hugo static site: an online gallery of Priti Ghatlia's paintings, deployed to GitHub Pages at
artbypriti.com. There is no application code — 46 artwork page bundles, four template overrides,
one stylesheet, and two Python validators.

## Read these first

- **[`.specify/memory/constitution.md`](.specify/memory/constitution.md)** — the *project* deltas
  only: Hugo's silent fallback, the image budget, the live-site-is-a-portfolio rules. It cites the
  house rules rather than repeating them.
- **[`tests/README.md`](tests/README.md)** — the three gates, what each guards, and how to run
  them.
- **[`specs/`](specs/)** — specifications for in-flight work. If a spec exists for what you are
  changing, read it before the code.

## Before you claim anything works

Hugo's dominant failure mode is **silent fallback, not error**. Front matter naming a file that
does not exist will not fail the build — Hugo picks a different image and the deploy goes green.
Three such declarations shipped and survived ~15 months behind 16 consecutive green deploys.

So: **verify against build output, never against the templates.** Grep `public/`, diff before
against after, compare screenshots. Reading a template tells you what it *probably* does — on this
repository that reasoning has produced confident, wrong conclusions more than once.

## Workflow: spec at the start, gate at the end

Both are enforced, because this project twice wrote down a process that nothing checked and then
skipped it.

1. **Before implementing** anything touching `layouts/`, `assets/`, `themes/`, `scripts/`, `tests/`,
   `.github/workflows/`, `hugo.toml`, `Makefile`, or `archetypes/` — write a spec:
   `/speckit-specify`, then `/speckit-plan` and `/speckit-tasks`. CI **fails** a PR that changes
   those paths with no spec.
   - Small change that genuinely needs no spec? Put `No-Spec: <reason>` in a commit message or the
     PR body. That is a supported route, not a workaround — but the reason gets recorded.
   - Content edits, `docs/`, and `README.md` need no spec at all.
2. **After implementing**, leave a gate behind: the defect you just fixed should be unable to return
   silently. Rendering changes are caught automatically by visual regression; content and output
   assertions run on every PR. For a genuinely new defect class, add the check — the PR template asks
   which gate now covers it, because CI cannot judge that for you.
3. **Verify by observation**, not by reading. See the warning above.

## Commands

```bash
make               # list every target
make serve         # dev server with drafts, localhost:1313
make check         # specs + citations + front matter + strict build + output assertions (~1s; what CI runs)
make check-all     # the above plus visual regression (needs Docker)
make spec-required BASE=main   # does this branch record its intent?
make new SLUG=my-painting      # scaffold an artwork bundle
```

`make check` must pass before you open a pull request.

`make constitution-ids` refreshes `docs/constitution-ids.txt`, the vendored list of rule IDs that
`make check` validates citations against. It is vendored because CI cannot read `~/.claude`
(`CON-VER-004`); see [`specs/012-citation-guard/`](specs/012-citation-guard/).

## Layout

| Path | What |
| --- | --- |
| `content/<slug>/` | One artwork per directory: `index.md` + its image |
| `layouts/` | Overrides that win over the theme — edit here, not in the theme |
| `assets/css/custom.css` | The site's visual identity. Reaches the page via `@import "custom"` in the theme's `main.scss`, **not** a `<link>` tag |
| `themes/gallery/` | **Vendored** (not a submodule) — see `themes/gallery/UPSTREAM.md` before touching it |
| `scripts/` | `check-content.py` validates inputs, `check-output.py` validates the built site |
| `tests/visual/` | Playwright specs and committed screenshot baselines |
| `docs/` | Deployment notes, security posture, incidents, the legacy archive pointer, the open questions for the artist, and the vendored constitution-ID list |

## Gotchas that have cost time

- **Image cache lives in the path set by `[caches.images]`**, not `HUGO_CACHEDIR` by default. A
  cold build is ~200 s; warm is ~3 s. CI persists it — do not remove that cache step.
- **Hugo leaves stale files in `public/`** unless `--cleanDestinationDir` is passed. A renamed
  stylesheet keeps its predecessor, which makes output assertions report phantom problems.
- **The grid branch of `layouts/partials/gallery.html` never renders.** The home page uses the
  theme's `home.html` → `album-card.html`, and there are no image-bearing section lists. Its
  `site.Params.Author` schema.org block is therefore dead code.
  - That branch holds the only `id="gallery"` on the site, and **two** theme modules key off it:
    `lightbox.js` and `gallery.js`. So neither ever ran. Spec 016 fixed the lightbox with
    `assets/js/artwork-lightbox.js` (scoped to the artwork section) plus a project override of
    `assets/js/main.js` that drops both dead modules. **Do not "fix" it by adding `id="gallery"`**
    — that was tried, and `gallery.js` forces the painting into a 288 px justified row; five
    baselines failed.
  - Because `assets/js/main.js` is now a project override, a theme update that adds a module
    there will **not** take effect until it is added to our copy. See `themes/gallery/UPSTREAM.md`.
- **Full-resolution masters are not published** (`publishResources: false` cascades from
  `content/_index.md`). Keep it that way: they were 116 MB of a 140 MB deploy and no page linked
  them.
- **`legacy/` was removed from the tree**, not from history — see
  [`docs/legacy-archive.md`](docs/legacy-archive.md).

## Working agreements

- Non-trivial work gets a spec under `specs/` first (`/speckit-specify`).
- Never force-push `main`; never rewrite shared history.
- Do not invent artistic facts. A painting's dimensions, a description, the artist's choice of
  units — these come from her, and automation warns rather than guesses. The open questions are
  collected in [`docs/artist-requests.md`](docs/artist-requests.md); add to it rather than
  filling a gap in.
- This repo raised four constitution amendments that are still proposals. What they need before
  they can be adopted is in [`docs/constitution-handoff.md`](docs/constitution-handoff.md) —
  the edit belongs in the fleet repo, not here (`CON-PROC-007`).
- Fixing a defect includes adding it to a gate, so the same class cannot return silently.
