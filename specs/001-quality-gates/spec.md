# Feature Specification: Automated Quality Gates

**Feature Branch**: `001-quality-gates`

**Created**: 2026-08-05

**Status**: Implemented — PR #16

**Input**: User description: "Automated quality gates: output assertions and visual regression testing"

## Problem

This repository has no automated tests. Coverage is 0%, with no test runner and no dependency
manifest. Until 2026-08-04 there was no pull-request validation of any kind — the only automation
was deploy-on-merge.

The consequence is measurable, not hypothetical:

| Defect | Introduced | Found | Time in production |
| --- | --- | --- | --- |
| `content/about/` declares a portrait file that does not exist | 2025-04-30 | 2026-08-04 | ~15 months |
| Home cover names a file inside a child bundle; OpenGraph silently falls back | 2025-04-30 | 2026-08-04 | ~15 months |
| `ganeshas-blessings` declares `.jpg`, the file is `.jpeg` | 2025-05-19 | 2026-08-05 | ~14 months |
| CI sets `HUGO_CACHEDIR` but persists nothing (~200 s wasted per deploy) | 2025-04-30 | 2026-08-04 | ~15 months |

All four shipped through **16 consecutive green deploys**. None was found by automation; all were
found by a human reading files more than a year later. The reason is Constitution Principle I:
Hugo answers a missing resource with a silent fallback, not an error, so an exit-code check can
never see it.

Two defect classes remain entirely unguarded today:

1. **Wrong output from a successful build** — a missing image, a vanished caption, a broken link, a
   master accidentally republished. `scripts/check-content.py` validates *inputs*; nothing yet
   validates the *built site*.
2. **Visual regression** — this site's product is its appearance, and that appearance rests on a
   single 119-line `custom.css` leaning on `!important` overrides against a vendored theme. Nothing
   detects a layout or colour regression. The only such check ever performed was manual HTML
   diffing during the 2026-08 backend work.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A broken artwork page cannot reach production (Priority: P1)

As the site owner, when I add or edit a painting and open a pull request, I am told before merging
if the page will render incorrectly — a missing image, an absent size caption, a dead link, or a
republished master — rather than discovering it months later, or never.

**Why this priority**: This is the class behind every known defect in this repository. It is also
the cheapest to check, because it needs no browser.

**Independent Test**: Deliberately break a painting's front matter on a branch, open a PR, confirm
CI fails naming the file and the problem. Revert, confirm CI passes.

**Acceptance Scenarios**:

1. **Given** an artwork whose `resources` entry names a file absent from its bundle, **When** CI
   runs, **Then** it fails and the message names the artwork and the missing file.
2. **Given** a full-resolution master present in `public/`, **When** output assertions run,
   **Then** they fail, citing the performance budget in Principle IV.
3. **Given** a page linking to a path that does not exist in the built site, **When** the link
   check runs, **Then** it fails and prints the source page and the dead target.
4. **Given** an artwork with no `dimensions`, **When** CI runs, **Then** it **warns** and
   **passes** — per Principle III, artist-authored content never blocks a deploy.
5. **Given** a valid site, **When** CI runs, **Then** every check passes with no manual steps.

---

### User Story 2 - A CSS change cannot silently disfigure the gallery (Priority: P2)

As the site owner, when a stylesheet, template, or theme update changes how a page looks, I see
which pages changed and by how much before it reaches visitors — instead of trusting that an
`!important` override did not cascade somewhere unexpected.

**Why this priority**: The highest-value protection for a site whose product is appearance, but it
depends on P1's build being trustworthy and costs more to run and maintain (baseline images, a
browser toolchain).

**Independent Test**: Change a colour in `custom.css` on a branch, confirm CI fails with a visual
diff; accept the new baseline, confirm CI passes.

**Acceptance Scenarios**:

1. **Given** an unchanged site, **When** visual regression runs twice, **Then** it passes both
   times with no spurious differences (no flakiness from fonts, image loading, or animation).
2. **Given** a modified `custom.css` that changes rendering, **When** the check runs, **Then** it
   fails and produces an image diff identifying the affected page.
3. **Given** an intentional redesign, **When** baselines are regenerated, **Then** the change is
   reviewable in the pull request as changed baseline images.
4. **Given** CI and a local developer machine, **When** both run the check on identical content,
   **Then** they agree — screenshot rendering must not depend on the host's fonts.

---

### User Story 3 - The next contributor inherits a documented process (Priority: P3)

As a future contributor — human or AI agent — I can discover how this project expects work to be
done, instead of following `CLAUDE.md`'s instruction to "read the current plan" and finding that no
plan exists.

**Why this priority**: Cheap, and it compounds. It is also a correctness issue for agents, which
follow written instructions literally.

**Independent Test**: Read `CLAUDE.md` and the constitution cold; confirm they describe what the
repository actually contains and how to run the gates.

**Acceptance Scenarios**:

1. **Given** a fresh checkout, **When** a contributor reads `CLAUDE.md`, **Then** every instruction
   in it resolves to something that exists.
2. **Given** the constitution, **When** a contributor reads it, **Then** it contains project
   principles rather than `[PLACEHOLDER]` tokens.

## Requirements *(mandatory)*

### Functional

- **FR-001**: A single command (`make check`) runs every gate locally, and CI runs that same set.
- **FR-002**: Output assertions inspect the built site and fail on: any published full-resolution
  master; an artwork page missing its image or size caption; a missing expected page; an internal
  link resolving to nothing; a total payload over the 40 MB budget.
- **FR-003**: Hugo build warnings fail the gate (`--panicOnWarning`), so new warnings cannot
  accumulate unnoticed.
- **FR-004**: Content validation keeps its existing split — structural errors fail, artist-authored
  gaps warn (Principle III).
- **FR-005**: Visual regression captures agreed pages at a fixed viewport and compares against
  committed baselines, failing on a difference beyond a documented pixel tolerance.
- **FR-006**: Visual regression runs in a pinned container so rendering is identical in CI and
  locally, and baselines are regenerable with one documented command.
- **FR-007**: Every gate runs on `pull_request`; deploys stay on merge to `main`.
- **FR-008**: `CLAUDE.md` and the constitution describe the repository as it actually is.

### Non-functional

- **NFR-001**: Non-visual gates complete in under 60 s with a warm image cache; the full set
  including visual regression in under 5 minutes.
- **NFR-002**: Zero flaky failures — a passing site passes repeatedly. A gate that cries wolf gets
  ignored, and is worse than no gate.
- **NFR-003**: No new runtime dependency for the site itself. Test tooling must not affect
  published output.

## Success Criteria

- **SC-001**: Each historical defect above that is *gateable* is caught by a check that fails when
  the defect is reintroduced. This is the acceptance test for the whole feature: a suite that cannot
  catch the bugs that actually happened is theatre.

  Verified by reintroducing each defect and observing the failure:

  | Historical defect | Gated? | Evidence |
  | --- | --- | --- |
  | `about/` declares a nonexistent portrait | ✅ | `check-content` errors, naming the file present instead |
  | Home cover names a file in a child bundle | ✅ | `check-content` errors, and points at the child bundle holding it |
  | `ganeshas-blessings` `.jpg` vs `.jpeg` | ✅ | `check-content` errors (this is how the defect was found) |
  | CI sets `HUGO_CACHEDIR` but persists nothing | ❌ | **Not gated — deliberately.** |

  The cache defect is a CI-configuration mistake, not a property of the site's inputs or output. The
  only test that could "catch" it would grep the workflow YAML for a cache step, which asserts the
  shape of the fix rather than the behaviour, breaks on any legitimate refactor, and would give false
  assurance — the theatre this spec exists to avoid. It is instead handled by making the behaviour
  observable and documented: every run logs `Cache restored from key` or `Cache not found`, the
  measured 43.8 s → 0.35 s difference is recorded in `docs/backend-optimization-plan.md`, and both
  workflows carry comments explaining the cache and GitHub's ref scoping.
- **SC-002**: A deliberately broken painting and a deliberately altered stylesheet each fail CI,
  demonstrated on this branch rather than asserted.
- **SC-003**: `make check` passes on `main` with no manual intervention.
- **SC-004**: No `[PLACEHOLDER]` tokens remain in the constitution, and no instruction in
  `CLAUDE.md` points at something that does not exist.

## Out of Scope

- Unit tests of site code — there is none: 681 lines of content markdown, 123 of templates, 119 of
  CSS. The only unit-testable code in the repo is the validator itself, whose behaviour is covered
  end to end by SC-001/SC-002.
- Accessibility, Lighthouse, and HTML-standards auditing — worth doing later, not needed to close
  the defect classes that have actually bitten.
- Changing how the site looks. Baselines record current appearance; they neither endorse nor alter
  it.
