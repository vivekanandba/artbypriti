# Feature Specification: Durable Standards — Shared Constitution & Continuous Learning

**Feature Branch**: `004-durable-standards`

**Created**: 2026-08-08

**Status**: Implemented — PR #20

**Input**: User description: "Can we have a common constitution? Can we have a shared constitution?
How do we learn it continuously? Please come up with some better ideas."

## Problem

Two gaps, both about standards surviving beyond the session that wrote them.

**Standards are duplicated and drifting.** Four repositories on this machine keep their own
constitution, and they independently arrived at the same rules: `landseer` III/IV, `resumefit` III
and `artbypriti` I/II all say some version of *verify the artifact, not the appearance of success*;
`resumefit` I, `gadjoy` III and `artbypriti` III all forbid fabricating domain content. That
convergence is evidence the rules generalise — and evidence that each repo is re-deriving them from
its own incidents, expensively. `~/.claude/CLAUDE.md` holds machine-wide principles but is not in
any repository, so it does not travel to CI, to a fresh clone, or to anyone else.

**Standards decay silently.** Every gate this project has runs on a change. Nothing watches the
system when nobody is changing it: a live site can break through DNS, an expired certificate, an
external link rotting, or a deploy that silently stopped happening — and no PR would ever notice.
Equally, `landseer` VII observes that *keeping a suite green is not keeping it current*: gates
accumulate only if someone remembers to add one after each incident.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Shared rules, one source, visible drift (Priority: P1)

As someone maintaining several repositories, I write a principle once, and every project that adopts
it carries the same words — and I am told when a copy has quietly diverged.

**Why this priority**: Cheap, and it stops the same lesson being paid for repeatedly.

**Independent Test**: Edit the shared block in a project constitution; the drift check fails. Restore
it; the check passes.

**Acceptance Scenarios**:

1. **Given** a project constitution with the shared block spliced in, **When** the drift check runs,
   **Then** it passes and reports the version in use.
2. **Given** a locally edited shared block, **When** the check runs, **Then** it fails and directs
   the author to amend upstream or override with a project principle.
3. **Given** a project whose needs differ, **When** it adds a principle below the block that
   contradicts a shared one and says why, **Then** that is legitimate and passes.
4. **Given** another repository, **When** the installer is run against it, **Then** the base and the
   check are vendored without disturbing that project's own principles.

---

### User Story 2 - The system is watched when nobody is looking (Priority: P1)

As the site owner, I find out that the live site broke — or that a gate has gone stale — from a
scheduled check, not from a visitor.

**Why this priority**: This is the only layer that catches decay rather than change. Everything else
in this project is triggered by a commit.

**Acceptance Scenarios**:

1. **Given** the site is live and healthy, **When** the scheduled check runs, **Then** it passes.
2. **Given** the live site returns a non-200 for a key page, **When** the check runs, **Then** it
   fails visibly.
3. **Given** the archive reference has stopped resolving, **When** the check runs, **Then** it fails.
4. **Given** a deploy has not happened in a long time while `main` has moved, **When** the check
   runs, **Then** it reports that.
5. **Given** the check runs on a schedule, **When** nothing has changed, **Then** it still runs —
   decay is the thing being watched.

---

### User Story 3 - Every incident becomes a gate (Priority: P2)

As a future maintainer, I can read what has gone wrong here, how it was found, and which check now
catches it — so the suite grows deliberately instead of by memory.

**Acceptance Scenarios**:

1. **Given** a defect is found, **When** it is fixed, **Then** the ledger records what it was, how it
   was found, and which gate now covers it — or states plainly that none can.
2. **Given** the ledger, **When** it is read cold, **Then** the entries are specific enough to be
   checkable, including the ones caused by the tooling itself.

## Requirements *(mandatory)*

### Functional

- **FR-001**: `constitution/base.md` holds the shared principles with a pinned version, each citing
  the repositories that converged on it.
- **FR-002**: The base is spliced into `.specify/memory/constitution.md` between explicit markers,
  above the project's own principles.
- **FR-003**: `scripts/check-constitution.py` fails when the spliced block differs from the base, and
  runs in `make check` and `pre-commit`.
- **FR-004**: `scripts/install-constitution.sh <repo>` vendors the base and the check into another
  repository, preserving that project's own principles, and is idempotent.
- **FR-005**: A scheduled workflow checks the **live site**: key pages, the archive reference, and
  deploy freshness — separately from any commit.
- **FR-006**: `docs/incidents.md` records every defect: what, how found, which gate now catches it.

### Non-functional

- **NFR-001**: No new dependency; bash and stdlib Python.
- **NFR-002**: The scheduled check must not fail on transient network noise alone — it retries before
  reporting.
- **NFR-003**: A project must always be able to override a shared principle, in writing. A shared
  rule that cannot be overridden gets the whole base rejected.

## Success Criteria

- **SC-001**: Editing the shared block fails the check; restoring it passes. Demonstrated.
- **SC-002**: The four domain principles from the parallel `docs/fill-constitution-and-claude-md`
  branch are incorporated, so that work is not lost to a merge conflict.
- **SC-003**: The scheduled workflow passes against the live site today, and its failure path is
  demonstrated.
- **SC-004**: The ledger contains this session's real incidents, including those caused by my own
  tooling.
- **SC-005**: `make check` still completes in seconds.

## Out of Scope

- Running the installer against sibling repositories — that is a change to repos this feature does not
  own, and their maintainer decides.
- Moving `~/.claude/CLAUDE.md` into version control.
- Alerting/paging on scheduled failures beyond GitHub's own notifications.
