# Feature Specification: A Spec Says Whether It Shipped

**Feature Branch**: `022-spec-status`

**Created**: 2026-11-13

**Status**: Implemented — PR #43

**Input**: A known disagreement recorded in `specs/README.md` since spec 011: shipped specs still
saying `Status: Draft` in their own header.

## Problem

A spec's status lives in two hand-kept places: its own `**Status**:` header, and its row in
`specs/README.md`. Nothing compared them. Measured on `main` @ `336e596`:

| | |
| --- | --- |
| Specs whose header said `Draft` | **15** |
| …of which the registry said `Implemented` | **14** |
| Registry rows themselves stale | **1** — `020` said "In review / this PR" after merging as #41 |

The disagreement was recorded rather than silently reconciled (`CON-DATA-003`), and then left for
weeks — a recorded problem with no gate is a wish (`CON-PROC-011`). Two copies of one fact drift
unless something compares them; spec 019 learned the same about duplicated linter pins.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A reader can trust a spec's status (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a spec header and its registry row, **When** spec checks run, **Then** they must
   agree on whether the work shipped, or the check fails naming the spec.
2. **Given** an unrecognised or missing status, **When** the check runs, **Then** it fails rather
   than passing silently.

### User Story 2 - Staleness is visible without blocking unrelated work (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a spec already on `main` that still says Draft, **When** a PR's spec checks run,
   **Then** a **warning** names it. A warning, because the next PR is often unrelated — an artist
   adding a painting's dimensions — and failing it for someone else's bookkeeping teaches people
   to route around the gate.
2. **Given** a spec new in the PR, **When** it says Draft, **Then** nothing is reported.

## Requirements *(mandatory)*

- **FR-001**: The 15 stale headers and the stale `020` row corrected against the merged PRs.
- **FR-002**: `check_status_agreement` — header and registry must agree; error otherwise.
- **FR-003**: `check_shipped_specs_say_so` — warning, with `--diff-base`, for specs on the base
  that still say Draft.
- **FR-004**: Statuses normalise to shipped / in review / backfilled; "Draft" ≡ "In review",
  "RETROACTIVE" ≡ "Backfilled".

## Success Criteria

- **SC-001**: All headers agree with the registry.
- **SC-002**: Reverting one header to Draft fails the check; the same spec on the base branch
  produces the warning. Both demonstrated.
- **SC-003**: Mutating the status mapping turns three tests red.

## Out of Scope

- Generating the registry from the headers. One source of truth would be cleaner still, but the
  registry carries prose (the numbering notes) that a generator would have to preserve; comparing
  the two is the cheaper fix that holds.
