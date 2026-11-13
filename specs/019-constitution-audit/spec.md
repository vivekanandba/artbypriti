# Feature Specification: Meet the 22 Rules the Constitution Gained

**Feature Branch**: `019-observability`

**Created**: 2026-11-13

**Status**: Draft

**Input**: fleet#54 (2026-11-07) adopted 22 rules this repository had never been checked
against. One of them, `CON-OBS-002`, names this repository in its own incident: *"artbypriti's
weekly health job [failed] four Mondays, unread."*

## Problem

The constitution is cited, not restated, so when it grows a project inherits obligations
without any of its files changing. This repo had been audited against 35 rules; there are now 57.

### The audit, measured on `main` @ `9c5b8f7`

Each rule was read in full — not judged from its title — and checked against this repository by
running something, not by reading templates.

| Rule | Finding | Action |
| --- | --- | --- |
| `CON-OBS-002` Scheduled job proves it ran | **Failed four Mondays (Oct 12 → Nov 2), zero issues filed.** Cause: `health.yml` never installed `requirements-dev.txt` after #24 made `make check` need coverage. The reporter did not exist yet. | **Already fixed by #35** (2026-11-07): install step, reporter, regression test. Nov 9 green. Absence detection remains — see Out of Scope. |
| `CON-OBS-003` Fire the alert path once | The reporter #35 added has **never fired**: its only run since was a success. | **This spec**: a `canary` dispatch input; fire it, record delivery. |
| `CON-COV-005` Test the build that ships | **Gap, confirmed.** Deploy ran `hugo --minify --baseURL …`; every browser test ran on `make build`. ~33 tests had never seen a shipped byte. | **This spec**: one build command; the deploy runs the browser suite on its own artifact before upload. |
| `CON-PROC-016` Tests in git's environment | **Gap, reproduced.** With `GIT_DIR` pointed at a throwaway repo, `test_check_specs.py` wrote **15 fixture commits and two branches into it** and three tests failed on the wrong history. The real repo was checked: untouched. | **This spec**: autouse fixture strips every `GIT_*` for every test. House-gates 1.7.0 already scrubs at hook entry (#35). |
| `CON-VER-010` Pin the floor; image matches lockfile | Image and lockfile agree (1.62.1) but **nothing asserts it**; shellcheck/bandit pins were **duplicated** in Makefile and CI. | **This spec**: CI calls `make lint` (one copy of each pin); contract tests for image == lockfile and no restated pins. |
| `CON-COV-004` Vendored files exempt from host style gates | `make lint` style-linted `.githooks/*`, which carry a **vendored house-gates v1.7.1** block. Passing today; a latent red build on the next re-vendoring. | **This spec**: hooks excluded with the reason inline; `scripts/*.sh` linted by glob. |
| `CON-VER-011` Vendored copy says what and how old | `docs/constitution-ids.txt` records provenance in its header, but **no run ever printed it** — and CI's freshness check is always SKIPPED, so CI never stated the age at all. | **This spec**: `check-citations.py` prints commit, sync date and age on every run. |
| `CON-VER-012` Infrastructure limit ≠ software signal | Both artifact uploads are `if: failure()`, so a full store **cannot** turn a green run red. | Met by construction. I first listed it as a gap; that was wrong. |
| `CON-VER-015` Pixel baselines by construction | Images forced by `settle()`; service workers blocked in screenshot tests; **no** web fonts; nothing date-dependent rendered. | Met. |
| `CON-VER-014` `grep -q` under `pipefail` | No such pipeline in any script, hook or workflow. | Met. |
| `CON-OBS-001` External probe, human told | A GCP uptime check named `artbypriti` exists, outside GitHub. | Met. |
| `CON-PROC-014` A gate that cannot run | `pull_request:` has no branch filter, so every PR is gated. The citation-freshness SKIP in CI is honest and now accompanied by a stated age (above). | Met. |
| `CON-PROC-017` Pipeline is budgeted | Every job has `timeout-minutes` and every workflow a concurrency group (#35). The repo is **public**, so the self-hosted-runner clause does not bind. | Met. |
| `CON-PROC-018` In-place edit reads, then writes | Every edit here reads into a variable first; `check-specs.py` fails an empty spec. | Met. |
| `CON-VER-009`, `CON-PROC-019`, `CON-PROC-020`, `CON-OBS-004` | No cloud reads; no CRUD entities; no contract-harness registry; no runtime logs (static site). | Not applicable, with the reason stated. |
| `CON-DATA-006`, `CON-PROC-010`, `CON-PROC-015`, `CON-VER-013` | This repo's own proposals, adopted in fleet#54. | Met — they were written from this repo's practice. |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The tests look at what ships (Priority: P1)

As the owner, a deploy cannot publish a site whose screenshots, accessibility or lightbox
behaviour would fail — because those tests run on the exact bytes being uploaded.

**Acceptance Scenarios**:

1. **Given** a deploy, **When** it builds, **Then** it uses `make build`, the same command every
   test path uses.
2. **Given** the built artifact, **When** the deploy continues, **Then** the browser suite runs on
   it **before** upload, and a failure stops the publish.
3. **Given** a workflow that reintroduces a raw `hugo` command, **When** unit tests run, **Then**
   they fail.

### User Story 2 - A red health check provably reaches a person (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a dispatch with `canary: true` on `main`, **When** it runs, **Then** the run fails on
   purpose and an issue is opened.
2. **Given** a following normal dispatch, **When** it succeeds, **Then** the issue is closed.
3. **Given** the canary was fired, **When** this work is recorded, **Then** the issue number and
   the time it arrived are written down (`CON-OBS-003`).

### User Story 3 - Tests cannot write into the developer's repository (Priority: P1)

**Acceptance Scenarios**:

1. **Given** `GIT_DIR` set to another repository, **When** the unit suite runs, **Then** that
   repository is unchanged and every test passes.

### User Story 4 - Pins live in one place and agree (Priority: P2)

**Acceptance Scenarios**:

1. **Given** the Playwright image tag and the lockfile, **When** they disagree, **Then** a test
   fails.
2. **Given** a workflow that restates a pinned linter, **When** unit tests run, **Then** they fail.

## Requirements *(mandatory)*

- **FR-001**: `make build` takes an optional `BASE_URL`; it is the only build command anywhere.
- **FR-002**: `make visual-built` runs the browser suite on the existing `public/` without
  rebuilding; the deploy runs it between build and upload.
- **FR-003**: `health.yml` accepts a `canary` boolean input that fails the run deliberately.
- **FR-004**: An autouse unit-test fixture removes every `GIT_*` variable.
- **FR-005**: CI runs `make lint`; linter pins exist only in the Makefile.
- **FR-006**: `.githooks/*` are excluded from shellcheck's style gate, with the reason inline.
- **FR-007**: `check-citations.py` prints the vendored list's commit, sync date and age every run.

## Success Criteria

- **SC-001**: The deploy's exact build and browser steps pass locally: done — 33 passed.
- **SC-002**: The `GIT_DIR` reproduction leaves the decoy at 1 commit (was 16).
- **SC-003**: Each new contract test fails on the defect it guards — demonstrated by mutation.
- **SC-004**: The canary fires on `main`, an issue arrives, a success closes it; both times
  recorded.
- **SC-005**: `make check-all` exits 0.

## Out of Scope

- **Absence alarms for GitHub scheduled workflows** (`CON-OBS-002`'s "a scheduler that has never
  fired is red"). GitHub disables schedules in a repository with no activity for 60 days, and a
  workflow cannot report its own non-existence. The right observer is outside the repo — the
  fleet's VM cron already audits Cloud Scheduler jobs and could audit these. Proposed to the
  fleet rather than half-solved here.
- **Fixing the house-gates installer** so it registers the lint exclusion itself (`CON-COV-004`
  "Enforced by: not yet"). That is the fleet's tooling.
