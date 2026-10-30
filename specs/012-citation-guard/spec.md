# Feature Specification: Guard the Constitution Citations

**Feature Branch**: `012-citation-guard`

**Created**: 2026-10-30

**Status**: Draft

**Input**: Outstanding item from the post-merge plan: "11 IDs cited, nothing checks them." The real
count, measured on `main` @ `16597cf`, is **25 distinct IDs** across specs, scripts, docs and
templates.

## Problem

This repository's house style is to **cite** a shared rule by ID rather than restate it —
`CON-VER-005`, `CON-PROC-003` — because copies drift and citations do not. That style only holds if
the citations resolve. Nothing checks that they do.

The rules live outside this repository, in `vivekanandba/fleet`, and they change without this repo
being touched: the local mirror picked up **26 → 35 rules** unattended during one session. Three
things can therefore go wrong silently:

1. **A cited rule is renumbered or retired.** The citation still reads as authoritative and now
   points at nothing, or worse, at a different rule.
2. **A typo'd ID** — a letter O where a zero belongs — looks exactly as convincing as a real one.
3. **A proposed ID is cited as though adopted.** This repo has done exactly that twice — it
   proposed `CON-DATA-006` and `CON-PROC-010` in `specs/005-adopt-house-standards/tasks.md`, and
   neither exists in the constitution. Those two are honest records of a proposal, not errors, but
   nothing distinguishes them from the first two cases.

Measured on `main` @ `16597cf`: **25 cited**, **35 defined**, **2 cited-but-undefined** — both
proposals.

**Why a check and not care:** `CON-PROC-011` — a rule with no enforcing mechanism is a wish. The
whole citation convention is an unenforced rule today.

## Constraint that shapes the design

`CON-VER-004`: a checker that lives outside the repository cannot be a CI gate, because CI only
gets the repository. GitHub Actions cannot read `~/.claude` or `~/data-dash`. So the list of valid
IDs must be **vendored into the repo**, and kept fresh deliberately rather than read live.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A citation that points at nothing fails the build (Priority: P1)

As a maintainer, if I cite a rule that does not exist — mistyped, renumbered, or retired — CI tells
me before the claim ships.

**Why this priority**: A wrong citation is worse than no citation. It reads as authority and sends
the next reader after a rule that is not there.

**Independent Test**: Introduce a citation to a rule that does not exist in any tracked file; the
gate fails and names the file and line.

**Acceptance Scenarios**:

1. **Given** a citation to an ID absent from the vendored list, **When** the gate runs, **Then** it
   **fails**, naming the ID and every file and line citing it.
2. **Given** only citations that resolve, **When** it runs, **Then** it passes.
3. **Given** a malformed ID that looks real (a letter O in place of a zero), **When** it runs,
   **Then** it fails rather than ignoring it as unrecognised.

---

### User Story 2 - An honest proposal is not treated as a mistake (Priority: P1)

As a maintainer recording that this project *proposed* a new rule, that record survives the gate
without weakening it.

**Why this priority**: A gate that fails honest text gets disabled, and a disabled gate protects
nothing — this project has already written that lesson down twice. But a blanket exemption for
anything resembling a proposal would gut the check.

**Acceptance Scenarios**:

1. **Given** an ID listed in the proposed-IDs file with a stated reason, **When** the gate runs,
   **Then** it passes and reports it as proposed, not as resolved.
2. **Given** a proposed ID that has since been **adopted** into the constitution, **When** the gate
   runs, **Then** it **fails** — the entry is stale and the citation should now stand on its own.
3. **Given** an entry in the proposed file with no reason recorded, **When** it runs, **Then** it
   fails. The exemption costs a sentence, which is the point.
4. **Given** a proposed ID that nothing in the repo actually cites, **When** it runs, **Then** it
   **warns** — a dead exemption is how an allowlist quietly becomes a blanket.

---

### User Story 3 - The vendored list cannot silently rot (Priority: P2)

As a maintainer, I can tell whether the vendored list still matches the real constitution, and
refresh it in one command.

**Why this priority**: A vendored copy is a snapshot. The failure this guards against is the guard
itself going stale and passing citations that no longer resolve upstream.

**Acceptance Scenarios**:

1. **Given** the constitution mirror is present locally, **When** the gate runs, **Then** it
   compares the vendored list against it and **warns** on any difference, naming what changed.
2. **Given** the mirror is absent (CI), **When** it runs, **Then** it says the freshness check was
   **skipped** — distinct from "checked and fine" (`CON-VER-005`, `CON-DATA-002`).
3. **Given** a drifted list, **When** `make constitution-ids` is run, **Then** the vendored file is
   regenerated from the mirror and records its source and date.

## Requirements *(mandatory)*

### Functional

- **FR-001**: `docs/constitution-ids.txt` vendors the valid rule IDs, with a header recording the
  source, the commit it was taken from, and how to refresh it.
- **FR-002**: `docs/constitution-ids-proposed.txt` lists IDs this repo cites as *proposed*, each
  with a one-line reason. An entry without a reason is an error.
- **FR-003**: `scripts/check-citations.py` fails on any cited ID that is neither vendored nor
  proposed, naming file and line.
- **FR-004**: It fails on a proposed entry that has since been adopted, and warns on a proposed
  entry nothing cites.
- **FR-005**: It warns — never errors — when the vendored list disagrees with a locally present
  mirror, and reports **skipped** when no mirror is available.
- **FR-006**: It runs in `make check`, so it gates every PR (`CON-VER-004`: the check ships with
  the repo).
- **FR-007**: `make constitution-ids` regenerates the vendored list from the mirror.
- **FR-008**: Scanning covers tracked text files and excludes `node_modules/`, `public/`,
  `themes/` (vendored) and the two list files themselves, which would otherwise match every ID.
- **FR-009**: A line carrying the marker `not-a-citation` is skipped, so documenting the checker —
  or recording a typo that was fixed — stays possible. Per-line and visible in the diff, the same
  bargain as `No-Spec:`: an escape hatch exists so the gate is never routed around wholesale, and
  using it leaves a trace. Without it this spec and the script's own docstring could not be written.

### Non-functional

- **NFR-001**: No new dependency; standard library only.
- **NFR-002**: Runs in well under a second, so `make check` stays usable.
- **NFR-003**: Unit tests join the existing suite; the ≥95% coverage floor holds.

## Success Criteria

- **SC-001**: The gate fails on a planted citation to a non-existent rule and passes once removed.
  Demonstrated.
- **SC-002**: The two real proposed IDs (`CON-DATA-006`, `CON-PROC-010`) pass via the proposed file
  and are reported as proposed, not as resolved.
- **SC-003**: Marking an adopted ID as proposed fails. Demonstrated.
- **SC-004**: With the mirror absent, the freshness line reads *skipped*, not *ok*.
- **SC-005**: `make check` exit 0 with the gate wired in; coverage floor ≥95% holds.
- **SC-006**: Every assertion mutation-tested — the code it guards is broken and the test watched to
  fail (`CON-PROC-005`).

## Out of Scope

- Adopting, renumbering or withdrawing any constitution rule. The two pending proposals are a
  separate handoff; this change only stops their citations being indistinguishable from typos.
- Checking that a citation is *apt* — whether `CON-VER-005` is the right rule for the sentence it
  sits in is a judgement, not a check (`002-spec-process`, "Honest limits").
- Citations in other repositories. Reporting across the fleet is the harvester's job.
- Automatically refreshing the vendored list on a schedule (`CON-PROC-007`: automation proposes).
