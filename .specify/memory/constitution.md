# Art by Priti Constitution

Machine-wide rules live in the **engineering constitution** (`~/.claude/CLAUDE.md`, versioned at
`~/data-dash/constitution`) and are loaded in every session. This file **cites** those rules by ID
and never restates them — copies drift, citations don't; `tools/harvest.py` reports duplication.

What follows is only what is specific to a Hugo gallery site with no application code.

## What the house rules already cover

These were re-derived here before the shared constitution existed. They are **not** repeated:

| Learned here | Already a house rule |
| --- | --- |
| A green Hugo build is not evidence the site is right | `CON-VER-001`, `CON-VER-003` |
| Reading a template is not verification; grep the built HTML | `CON-VER-003`, `CON-VER-006` |
| A gate whose tolerance is too loose passes everything | `CON-PROC-005` (a test that has never been red proves nothing) |
| Specs precede implementation | `CON-PROC-001`, `CON-PROC-005` |
| Every escaped defect extends the layer that should have caught it | `CON-PROC-003` |
| A green suite is not a current suite | `CON-PROC-002` |
| Don't commit straight to a protected branch | `CON-PROC-008` |
| Say what was verified, and what wasn't | `CON-REP-001`, `CON-REP-002` |
| A credential in a conversation is compromised | `CON-SEC-001` |

## Core Principles — specific to this repository

### I. Hugo fails by silent fallback, so assert on `public/`

An instance of `CON-VER-003`, sharp enough here to need saying: front matter naming a resource that
does not exist will not fail the build. Hugo picks a different image and the deploy goes green.
Three such declarations survived ~15 months behind 16 consecutive successful deploys.

Therefore every gate asserts on built output (`scripts/check-output.py`), never only on the exit
code.

### II. The rendered page is the contract

Visitors experience pixels, not templates. Reading `gallery.html` here produced two confident and
wrong conclusions — that the grid linked full-resolution masters, and that `params.author` would
emit schema.org metadata. Both were disproved by grepping built HTML. Visual regression
(`tests/visual/`) exists because this site's product *is* its appearance.

### III. Structural errors fail; artist-authored gaps warn

Only the artist can supply a painting's dimensions, her description, or her choice of units.
Blocking a deploy on those trains everyone to bypass the pipeline. Structural defects — a declared
file that is absent, a bundle with no image — are unambiguous and fail.

Automation must never invent artistic facts.

### IV. Performance is a budget

200 s of image processing per deploy and 116 MB of unreferenced masters persisted for a year
because nothing watched them. The deployed site stays **under 40 MB**, a cache-warm build **under
15 s**, and no full-resolution master is ever published. A change that breaches a budget states the
new number and why.

### V. The live site is someone's portfolio

Merging deploys. There is no staging step between `main` and a working artist's public presence, so
`main` must always build and always look right.

### VI. The images are the product

Never re-encode, rename, or move artwork unasked. A missing or degraded image is worse than a broken
layout — the layout is scaffolding, the painting is the point. This is why downscaling the masters
was measured and then rejected.

### VII. URLs that exist must keep existing

Gallery links are shared, bookmarked and printed; they outlive redesigns. Add an alias rather than
breaking a path.

### VIII. Size constraints are a hard wall

No Git LFS here, so GitHub's **100 MB per-file limit** binds — the WordPress backup is stored as
99 MB chunks precisely because of it. Do not rewrite history to reclaim space; it would invalidate
every clone in exchange for disk that costs nothing. Archive by reference instead: `legacy/` lives
at the `legacy-archive` tag.

### IX. The vendored theme declares itself

`themes/gallery` is committed directly while `.gitmodules` once claimed a submodule, and CI ran a
`submodules: recursive` step that did nothing. Vendored code records upstream, version and every
local modification (`themes/gallery/UPSTREAM.md`). Customise in root `layouts/` and
`assets/css/custom.css`, not in the vendored copy.

## Development Workflow

The house rules set the shape (`CON-PROC-001`, `-003`, `-004`, `-008`). What is enforced *here*:

- `make check` — spec hygiene, front matter, a strict build, and assertions on `public/`.
- `make visual` — screenshots against committed baselines, in a pinned container.
- `scripts/check-specs.py --diff-base <ref>` — a change to substantive paths must carry a spec or a
  written `No-Spec: <reason>`.
- Deploy-time gates in `.github/workflows/hugo.yml` — a broken site cannot publish even if it
  reaches `main` unreviewed.
- `.github/workflows/health.yml` — weekly, watches the **live** site for decay.
- `docs/incidents.md` — every defect and the gate that now catches it (`CON-PROC-003`).

## Governance

Amendments to *this* file land through a reviewed PR stating the incident that prompted them. A rule
that turns out to apply to every project belongs upstream instead — propose it with `/lesson`.

**Version**: 2.0.0 | **Ratified**: 2026-08-05 | **Last Amended**: 2026-08-08

### Amendments

- **2.0.0** (2026-08-08) — Rewritten to cite the shared engineering constitution rather than restate
  it. Five locally-derived principles were removed as duplicates of `CON-VER-*`/`CON-PROC-*`; the
  domain principles (V–VIII) were kept and extended. Prompted by discovering that this repo had
  re-derived rules that already existed house-wide.
- **1.1.0** (2026-08-06) — Workflow steps gained their enforcement mechanisms.
- **1.0.0** (2026-08-05) — First real constitution, replacing 16 unfilled placeholders.
