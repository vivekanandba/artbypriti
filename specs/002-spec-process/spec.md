# Feature Specification: Spec-First, Gate-Last Enforcement

**Feature Branch**: `002-spec-process`

**Created**: 2026-08-06

**Status**: Implemented — PR #17

**Input**: User description: "going forth the specs at the start and tests at the end of
implementation shouldn't be forgotten let me know what steps will be taken in that regard"

## Problem

This project has now written its process down twice and followed it once.

- The speckit scaffolding was installed 2025-04-30 and **never used**: no `specs/` directory, zero
  spec files, and a constitution consisting of 16 `[PLACEHOLDER]` tokens. `CLAUDE.md` said only "read
  the current plan", which resolved to nothing.
- The backend optimization work (`000-backend-optimization`) shipped as PR #15 with **no spec**. It
  worked, but on the strength of an unusually measurement-heavy session — not because anything
  required it. Two claims had to be corrected mid-flight, and a third error (an artwork miscount) went
  unfixed until this feature backfilled it.
- `001-quality-gates` wrote a spec first and was better for it: the acceptance test stated in that
  spec is what exposed that the validator missed one of the four defects it existed to catch.

The pattern is clear: **written intent that nothing checks gets skipped.** The scaffolding advertised a
process for 15 months while the repository ignored it, which actively misled readers — including
automated agents, which follow written instructions literally.

Two habits need to survive without depending on anyone's diligence:

1. **Spec at the start** — non-trivial work states its intent and acceptance criteria before
   implementation.
2. **Gate at the end** — work finishes by leaving behind a check that fails if the defect returns.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A substantive change cannot merge without recorded intent (Priority: P1)

As the site owner reviewing a pull request weeks later, I can see what the change was *meant* to
achieve and how it was verified, rather than inferring intent from a diff.

**Why this priority**: This is the failure that has already happened twice, and the one the owner asked
to prevent.

**Independent Test**: Open a PR touching templates or config with no spec; CI fails with an
explanation. Add a spec (or a recorded exemption); CI passes.

**Acceptance Scenarios**:

1. **Given** a PR changing templates, config, CI, or scripts, **When** no file under `specs/` is
   touched and no exemption is recorded, **Then** CI fails and the message explains both routes
   forward.
2. **Given** a PR that only edits content or documentation, **When** CI runs, **Then** it passes — a
   typo must not require a specification.
3. **Given** a genuinely small change to a substantive path, **When** the author records
   `No-Spec: <reason>` in a commit message or the PR body, **Then** CI passes and the reason is
   preserved in history.
4. **Given** a spec that exists but is still a template, **When** CI runs, **Then** it fails — an
   unfilled spec is not a spec.

---

### User Story 2 - Finished work leaves a gate behind (Priority: P2)

As the site owner, when a defect is fixed, I want the same defect to be unable to return silently — so
the suite grows with each incident instead of staying where it started.

**Why this priority**: The compounding habit, but it depends on judgment in a way US1 does not (see
"honest limits" below).

**Acceptance Scenarios**:

1. **Given** a change to stylesheets or templates that alters rendering, **When** CI runs, **Then**
   visual regression fails unless baselines were deliberately re-recorded in the same change.
2. **Given** a change to content or front matter, **When** CI runs, **Then** content and output
   assertions run against it automatically.
3. **Given** a defect fix, **When** the PR is opened, **Then** the author is prompted — in the PR
   template — to state which gate now covers it, or why none can.
4. **Given** a spec, **When** it is checked, **Then** it must contain success criteria, so "how would
   we know this worked" is answered before implementation rather than after.

---

### User Story 3 - The process is discoverable, not folklore (Priority: P3)

As a new contributor or agent, I can find the expected workflow in one place and follow it without
having read this session's history.

**Acceptance Scenarios**:

1. **Given** a fresh checkout, **When** `CLAUDE.md` and the constitution are read, **Then** the
   spec-first/gate-last workflow and its escape hatches are stated explicitly.
2. **Given** the specs directory, **When** it is listed, **Then** each feature's status is legible,
   including which shipped before the process existed.

## Requirements *(mandatory)*

### Functional

- **FR-001**: A CI check fails a pull request that modifies substantive paths without either a
  `specs/**` change or a recorded exemption.
- **FR-002**: Substantive paths are `layouts/`, `assets/`, `themes/`, `scripts/`, `tests/`,
  `.github/workflows/`, `hugo.toml`, `Makefile`, `package.json`, `playwright.config.js`, and
  `archetypes/`. Content markdown, `docs/`, `README.md`, and `specs/` themselves are not.
- **FR-003**: Exemptions are recorded as `No-Spec: <reason>` in a commit message or the PR body —
  visible in history, not a label that disappears.
- **FR-004**: A spec-hygiene check fails on unfilled template tokens (`[PLACEHOLDER]`,
  `[FEATURE NAME]`, `NEEDS CLARIFICATION`) and on a spec missing its success criteria.
- **FR-005**: Every feature directory must contain `spec.md`; `plan.md` and `tasks.md` are expected and
  warned about when absent.
- **FR-006**: The constitution states the spec-first and gate-last rules, including the exemption
  route.
- **FR-007**: A pull-request template prompts for the spec link, the verification evidence, and which
  gate now covers the change.
- **FR-008**: `CLAUDE.md` documents the workflow end to end.

### Non-functional

- **NFR-001**: The checks must not be bypassable by accident, nor annoying enough to route around. An
  exemption must always exist and must cost one line.
- **NFR-002**: No new dependency; stdlib Python only, consistent with the existing validators.
- **NFR-003**: Runtime under 5 s, so it never becomes the slow part of CI.
- **NFR-004**: The checks must be honest about what they cannot verify. A check that appears to enforce
  more than it does is the "theatre" failure mode this project has already documented.

## Success Criteria

- **SC-001**: A PR touching `layouts/` with no spec and no exemption **fails**; the same PR with an
  exemption line **passes**. Demonstrated, not asserted.
- **SC-002**: A content-only PR passes without a spec.
- **SC-003**: A spec still containing template tokens **fails** hygiene.
- **SC-004**: All three existing feature directories (`000`, `001`, `002`) pass hygiene.
- **SC-005**: `make check` includes the new checks and stays within its 60 s budget.
- **SC-006**: The workflow is stated in the constitution, `CLAUDE.md`, and the PR template, with no
  instruction pointing at something nonexistent.

## Honest limits — what this cannot enforce

Stated so the gate is not mistaken for more than it is (NFR-004, Constitution Principle I):

- **"A gate exists for this defect" is not machine-checkable.** Whether a new check genuinely covers a
  new defect class is a judgment. CI could require that *some* file under `tests/` changed, but that is
  satisfied by a meaningless edit — it would measure compliance, not coverage. Handled by the PR
  template and review, deliberately.
- **Spec *quality* is not checkable.** The checks catch an absent spec and an unfilled template. They
  cannot tell whether the acceptance criteria are meaningful.
- **What is already enforced mechanically**, needing no new check: a rendering change fails visual
  regression unless baselines are re-recorded in the same commit; content and output assertions already
  run on every PR. For those classes, "tests at the end" is structural rather than aspirational.

## Out of Scope

- Requiring a spec for every commit, or for direct pushes to `main`.
- Configuring GitHub branch protection (the owner's call; these checks are what protection would
  enforce).
- Retroactively specifying anything older than `000-backend-optimization`.
