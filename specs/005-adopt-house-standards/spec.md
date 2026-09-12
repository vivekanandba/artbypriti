# Feature Specification: Adopt the House Standards, Delete the Duplicates

**Feature Branch**: `005-adopt-house-standards`

**Created**: 2026-08-08

**Status**: Draft

**Input**: User description: "check if a lot of these hooks are part of the new constitution report
that I created. see if you can compare what is learnt over here into that report. If it is that
already fine, sound specific to this repo can be separated only."

## Problem

This repository re-derived, in isolation, a set of rules and tools that already exist house-wide —
and in two places shipped an **older** version of them.

Discovered on inspection of `~/data-dash/constitution`:

| Built here | Already existed |
| --- | --- |
| `constitution/base.md` — 5 "shared principles" restated in full | `CONSTITUTION.md` with 24 rules, IDs, and the explicit rule that *projects cite IDs and never restate them* |
| `scripts/install-constitution.sh` | `skills/adopt-constitution` |
| `scripts/check-constitution.py` (drift of a vendored copy) | Unnecessary once nothing is copied |
| `scripts/check-hygiene.sh` + `check-message.sh` (resumefit bundle **v1.0.0**, bash) | `house-gates` **v1.2.0** (`tools/check_hygiene.py`, config-driven via `.house-gates.json`) — already staged on this repo's `chore/house-gates` branch |

The house model is a layer model: constitution → skills → project guide → specs, where **a project
guide cites and never restates**. `tools/harvest.py` reports duplication, so the local base would
have been flagged as drift the next time it ran.

Meanwhile a handful of lessons from this repo's work are genuinely *not* in the house constitution,
and belong upstream rather than here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One source for shared rules (Priority: P1)

As someone maintaining twelve repositories, a rule I write once reaches all of them, and no project
carries a stale paraphrase of it.

**Acceptance Scenarios**:

1. **Given** the project constitution, **When** it is read, **Then** shared rules appear as citations
   (`CON-VER-001`), never as restated text.
2. **Given** the harvester runs, **When** it scans this repo, **Then** it reports no duplication of
   constitution text.
3. **Given** a house rule changes upstream, **When** nothing is copied here, **Then** this project
   needs no follow-up commit.

---

### User Story 2 - The house gates run here, not a fork of them (Priority: P1)

As the owner of the estate's tooling, this repo runs the same hygiene gates as its peers, at the
current version, with only its own additions layered on.

**Acceptance Scenarios**:

1. **Given** `chore/house-gates` is merged, **When** its installer writes `.githooks/pre-commit`,
   **Then** it prepends its block and preserves this repo's own checks below it — no conflict.
2. **Given** the repo-specific hook, **When** it runs, **Then** it performs only what is specific to
   this repository (spec hygiene), not a second copy of secrets/message checks.
3. **Given** the removal, **When** `make check` runs, **Then** it still passes.

---

### User Story 3 - Transferable lessons reach every project (Priority: P2)

As the estate owner, what this repo learned that *is* transferable becomes a proposal against the
shared constitution, not a local rule nobody else sees.

**Acceptance Scenarios**:

1. **Given** a lesson with an incident behind it and no existing rule covering it, **When** it is
   captured, **Then** a dated proposal appears in `constitution/proposals/` — never an edit to
   `CONSTITUTION.md` (`CON-PROC-007`).
2. **Given** a lesson a rule nearly covers, **When** it is captured, **Then** it proposes
   *strengthening* that rule rather than a near-duplicate ID.
3. **Given** a lesson specific to this repo, **When** it is captured, **Then** it stays in this
   repo's constitution.

## Requirements *(mandatory)*

- **FR-001**: Delete `constitution/base.md`, `constitution/VERSION`, `scripts/check-constitution.py`,
  `scripts/install-constitution.sh`.
- **FR-002**: Delete the vendored v1.0.0 bundle (`check-hygiene.sh`, `check-message.sh`,
  `post-merge-notes.sh`) and the hooks that call them; `house-gates` v1.2.0 supersedes them.
- **FR-003**: Keep `.githooks/pre-commit` holding **only** repo-specific checks, positioned so the
  house installer's block prepends cleanly above it.
- **FR-004**: Rewrite `.specify/memory/constitution.md` to cite house IDs and keep only project
  deltas.
- **FR-005**: `CLAUDE.md` states the layer model and points at the constitution.
- **FR-006**: Genuinely new lessons become proposals under `constitution/proposals/`.
- **FR-007**: No loss of enforcement: every gate that ran before still runs.

## Success Criteria

- **SC-001**: The project constitution contains zero restated house-rule text and ≥10 citations.
- **SC-002**: `make check`, `make visual` and the PR gates all still pass.
- **SC-003**: `chore/house-gates` merges into this branch without conflict in `.githooks/`.
- **SC-004**: Four proposals exist upstream, each naming its incident; none edits `CONSTITUTION.md`.
- **SC-005**: The project constitution drops from ~190 lines to roughly half, having lost only
  duplication.

## Out of Scope

- Accepting the proposals — that is a reviewed commit in the constitution repo, the owner's call.
- Merging `chore/house-gates` itself.
- Changing any sibling repository.
