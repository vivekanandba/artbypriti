# Feature Specification: Defense in Depth — Catch It Before the Commit

**Feature Branch**: `003-defense-in-depth`

**Created**: 2026-08-08

**Status**: Implemented — PR #19

**Input**: User description: "I still don't understand why branch protection is always flagged. We
don't have any other options. Can we have Git Hooks? Why are we not having other kind of blockages to
stop the build itself from happening? Fail the build. Why are we going into deploy... Before even we
commit, we catch this problems... learn from other repos, find out what are the best practices. Can we
have a shared constitution? How do we learn it continuously?"

## Problem

The question is fair and the framing was wrong. Every gate this project built lands at **pull-request
time**, and the one repeatedly flagged as missing — branch protection — is a GitHub setting the owner
must flip. That made enforcement sound like it had a single point of failure outside anyone's control.

It does not. Two concrete holes existed:

1. **The deploy workflow ran no gates at all.** `hugo.yml` checked out, built, and published. A direct
   push to `main`, or any merge that skipped review, reached production with nothing validating it.
   Branch protection would prevent the push; **failing the build prevents the damage** — and needs no
   setting.
2. **Nothing ran before a commit existed.** The cheapest possible feedback — a secret, a commit
   straight onto `main`, an unfilled spec — was only discoverable after pushing.

Meanwhile, the best practice was already in this portfolio and unused here. `resumefit` has a
versioned gate bundle (`scripts/install-hooks.sh`) built to be vendored into sibling repositories:
`core.hooksPath` rather than copied hooks, gates skipped where they do not apply, existing hooks
extended rather than replaced, idempotent re-runs. Its own header states the case exactly: *"Branch
protection is unavailable on this repo, so everything worth enforcing runs here or not at all."*

`keepsake` also ships `.githooks`. `landseer`, `resumefit`, and `gadjoy` all carry real, filled
constitutions with overlapping principles. The portfolio has been converging on these answers
independently — this repository was simply behind.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mistakes are caught before a commit exists (Priority: P1)

As the person making a change, I am stopped at the moment I make a mistake — a pasted credential, a
commit onto `main` — instead of learning about it from CI minutes later, or not at all.

**Why this priority**: Cheapest feedback in the chain, and it covers classes CI never checked here
(secrets, protected branch, commit-message meaning).

**Independent Test**: Stage a credential-shaped string and commit; the commit is blocked and names the
file.

**Acceptance Scenarios**:

1. **Given** a staged value that looks like a live credential, **When** committing, **Then** it is
   blocked and the file is named.
2. **Given** work staged directly on `main`, **When** committing, **Then** it is blocked.
3. **Given** a spec left as an unfilled template, **When** committing, **Then** it is blocked.
4. **Given** a commit message that says nothing ("wip"), **When** committing, **Then** it is blocked.
5. **Given** any of the above and a deliberate `--no-verify`, **When** committing, **Then** it
   proceeds — hooks are fast feedback, not a security boundary.
6. **Given** an ordinary change, **When** committing, **Then** the hook adds no perceptible delay.

---

### User Story 2 - A broken site cannot be published (Priority: P1)

As the site owner, if something invalid reaches `main` by any route, the deploy fails rather than
publishing it — regardless of whether branch protection is configured.

**Why this priority**: This is the failure that actually matters. Everything else is convenience;
this is the site visitors see.

**Acceptance Scenarios**:

1. **Given** a push to `main` whose content fails validation, **When** the deploy workflow runs,
   **Then** it fails **before** building and nothing is published.
2. **Given** a build that succeeds but produces wrong output, **When** the assertions run, **Then**
   the artifact is never uploaded.
3. **Given** a valid change, **When** it merges, **Then** it deploys as before.

---

### User Story 3 - The whole chain is visible and local-first (Priority: P2)

As a contributor, I can run exactly what CI will run, before pushing, and understand which layer
catches what.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** `make setup` is run, **Then** hooks are active and the layers are
   printed.
2. **Given** `make preflight`, **When** it runs, **Then** it performs the same checks as CI.
3. **Given** a missing optional tool (Docker), **When** preflight runs, **Then** it skips that check
   loudly and does not fail.

## Requirements *(mandatory)*

### Functional

- **FR-001**: Hooks live in a versioned `.githooks/` enabled via `core.hooksPath`, never copied into
  `.git/hooks`, so they are reviewed and updated like any other code.
- **FR-002**: `pre-commit` runs hygiene (secrets, protected branch, determinism, binaries) and spec
  hygiene. Staged content only; no build; near-instant.
- **FR-003**: `commit-msg` rejects messages that state nothing.
- **FR-004**: `pre-push` runs the full local equivalent of CI.
- **FR-005**: The deploy workflow validates **before building** and asserts on the built site
  **before uploading**.
- **FR-006**: `make setup` installs the hooks; `make preflight` runs the full local suite.
- **FR-007**: Every gate has a documented bypass (`--no-verify`).
- **FR-008**: Gates that cannot apply are skipped loudly rather than failing.

### Non-functional

- **NFR-001**: `pre-commit` stays under ~2 s. A slow hook gets bypassed habitually, and a bypassed
  hook protects nothing.
- **NFR-002**: No new runtime dependency; the bundle is bash + stdlib Python.
- **NFR-003**: Hooks are *feedback*, not a security boundary — they are bypassable by design, and the
  documentation says so plainly rather than implying otherwise.

## Success Criteria

- **SC-001**: A staged credential blocks the commit, demonstrated.
- **SC-002**: An unfilled spec blocks the commit, demonstrated.
- **SC-003**: A meaningless commit message is rejected, demonstrated.
- **SC-004**: The deploy workflow fails before publishing when validation fails, and still deploys a
  valid change.
- **SC-005**: `make setup` on a fresh clone activates every hook.
- **SC-006**: `pre-commit` completes in under 2 s on this repository.

## Where each layer sits

| Layer | Runs | Catches | Bypassable |
| --- | --- | --- | --- |
| `pre-commit` | before a commit exists | secrets, commit on `main`, unfilled specs | yes (`--no-verify`) |
| `commit-msg` | at commit | messages that say nothing | yes |
| `pre-push` | before the round trip | everything CI runs | yes |
| PR checks | on the pull request | same, authoritatively | no (but merge is not blocked without protection) |
| **Deploy gates** | on push to `main` | **publishing something broken** | **no** |
| Branch protection | on merge | merging past failing checks | owner setting |

The point of the table: branch protection is now **one row, not the row**. The deploy gate closes the
same hole for the case that actually matters — a broken site reaching visitors — and it needs nobody's
permission.

## Out of Scope

- Fixing the bundle's installer bug in `resumefit` (reported, not changed — it is another repository).
- Extracting a shared constitution across the portfolio (proposed separately; it is a decision about
  several repositories, not this one).
- Secret scanning of history, dependency scanning, SAST.
