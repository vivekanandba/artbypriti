# Feature Specification: Test the Gates

**Feature Branch**: `008-test-strategy`

**Created**: 2026-09-20

**Status**: Draft

**Input**: "I want unit tests to have more than 95% coverage... it's all written by you, AI... And even
end-to-end tests also... repo scripts to be checked... more comprehensive testing."

## Problem

Four gate scripts decide whether anything ships here. They were written by an AI, nothing tests them,
and **they have already shipped five bugs** — every one caught by a human, none by automation:

| # | Bug in a gate | Consequence |
| --- | --- | --- |
| 1 | `check-output.py` flagged `static/images/favicon.png` as a published master | false positive in a blocking gate |
| 2 | `check-content.py` never read `content/_index.md` | **missed the very defect it was built to catch**, which then lived ~15 months |
| 3 | `check-specs.py` failed both real specs for quoting a token in prose | a checker that cannot be documented |
| 4 | the no-upscaling assertion assumed a 1000 px slot on artwork pages | would have failed correct pages |
| 5 | Playwright's default `threshold: 0.2` | let an obvious background-colour change pass **7/7** |

**1,122 lines of Python, 0% unit coverage.** The thing every other check depends on is the only thing
unchecked.

`CON-COV-001` is the caution against reading too much into a percentage: one project sat at 97% while
every incident lived in code no suite touched. So the number is necessary and not sufficient — the
acceptance test is the five bugs above.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A broken gate cannot ship (Priority: P1)

As the owner, if someone changes a validator so it stops catching what it was written to catch, the
suite fails before that change is merged.

**Acceptance Scenarios**:

1. **Given** any of the five historical bugs is reintroduced, **When** the suite runs, **Then** a
   test named for that incident fails.
2. **Given** coverage of the gate scripts drops below the floor, **When** `make test` runs, **Then**
   it exits non-zero.
3. **Given** a clean tree, **When** `make check` runs, **Then** it stays fast enough to keep running
   before every PR.

---

### User Story 2 - The suite tests behaviour, not mocks (Priority: P2)

As a maintainer, the tests exercise the real parsers and the real git plumbing, so passing means
something.

**Acceptance Scenarios**:

1. **Given** the JPEG/PNG header reader, **When** it is tested, **Then** it parses genuine header
   bytes — not a stubbed return value.
2. **Given** the spec-required gate, **When** it is tested, **Then** it diffs a real git repository.
3. **Given** `check-live.py`, **When** it is tested, **Then** the network is mocked — a unit suite
   must not depend on production being up.

## Requirements *(mandatory)*

- **FR-001**: Unit tests for `check-content.py`, `check-output.py`, `check-specs.py`,
  `check-live.py`.
- **FR-002**: A named regression test for each of the five historical gate bugs.
- **FR-003**: `COVERAGE_FLOOR` (default 95) enforced by `make test` and CI; ratchets up only
  (`CON-COV-002`).
- **FR-004**: Tests run in CI **before** the gates are trusted to judge the change.
- **FR-005**: No network access from the unit suite.
- **FR-006**: `tools/check_hygiene.py` is **excluded and said so** — it is house-owned, and testing
  it here would fork it.

### Non-functional

- **NFR-001**: `make check`, including the suite, stays under 60 s.
- **NFR-002**: No flaky tests; no reliance on wall-clock, network, or the developer's git version
  beyond what the repo already requires.

## Success Criteria

- **SC-001**: Coverage of the four scripts **≥95%**. Achieved: **99%** (3 files at 100%).
- **SC-002**: 5/5 historical bugs have a failing-when-reintroduced test. Achieved — 8 regression
  tests including 3 site invariants.
- **SC-003**: The floor demonstrably blocks: at `COVERAGE_FLOOR=100` the suite exits non-zero.
- **SC-004**: `make check` under 60 s. Achieved: **~19 s** for 102 tests plus every existing gate.

## Out of Scope

- `tools/check_hygiene.py` (house-owned).
- E2E expansion, accessibility, shellcheck and the scheduled security suite — planned, tracked
  separately so this lands reviewable.
- Conventional API tests: there is no API. The deployed HTTP contract (`check-live.py`) is the
  equivalent, and is covered here.
