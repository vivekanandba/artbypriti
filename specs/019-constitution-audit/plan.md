# Implementation Plan: Meet the 22 Rules the Constitution Gained

**Spec**: [spec.md](./spec.md) · **Branch**: `019-observability` · **Created**: 2026-11-13

## Approach

Read every new rule in full, check each against the repository by running something, fix only
what is genuinely missing, and don't redo what a parallel session already did. PR #35
(2026-11-07) had already fixed the broken weekly suite, added the failure reporter, set
timeouts and concurrency, and re-vendored house-gates with the git-environment scrub. All of
that is left alone.

## The six changes

| Rule | Change | Why this shape |
| --- | --- | --- |
| `CON-COV-005` | `make build BASE_URL=…` is the only build; deploy runs `make visual-built` on its artifact before upload | Unify the paths rather than compare them — the rule's own preferred fix ("test the shipping path and delete the other") |
| `CON-OBS-003` | `canary` dispatch input fails the live job on purpose | The reporter only acts on `main`, so the proof has to be a real run on `main` |
| `CON-PROC-016` | Autouse fixture strips `GIT_*` | Autouse covers the fixtures *and* the code under test, and a future test cannot forget it |
| `CON-VER-010` | CI calls `make lint`; contract tests on pins | Removing the duplicate beats testing that two copies agree |
| `CON-COV-004` | `.githooks/*` out of the style lint; `scripts/*.sh` by glob | Project logic for hooks already lives in `scripts/check-local-gates.sh`, which stays linted |
| `CON-VER-011` | Print snapshot provenance every run | CI's freshness check is always SKIPPED, so this is the only age CI ever states |

## Evidence over assertion

- **`CON-PROC-016` reproduced before it was fixed**: `GIT_DIR` → throwaway repo; 15 fixture
  commits and two branches written into it. After the fix: still 1 commit, 27/27 pass.
- **`CON-COV-005` run as the deploy runs it**: `make build BASE_URL="https://artbypriti.com/"`,
  `check-output.py`, `make visual-built` — 33 browser tests pass on that artifact.
- **Every contract test mutation-tested**: image tag bumped; a pin restated in CI; the old raw
  `hugo` deploy step restored. Each turned its test red.

## A finding I got wrong

I listed `CON-VER-012` as a gap from the step names alone. Reading the steps: both uploads are
`if: failure()`, so a full artifact store can only fail a job that has already failed. Met by
construction; adding `continue-on-error` would have been a change with no effect.

## Risks

| Risk | Mitigation |
| --- | --- |
| Deploy now takes ~1.5 min longer | Build job timeout is 20 min against ~40 s today |
| A stale baseline on `main` now blocks a deploy | Baselines are enforced on every PR, so `main` is green by construction; and blocking a deploy whose screenshots differ is the point |
| The canary is dispatched by accident | Default `false`; a schedule has no inputs; the step names itself "Not an outage" |
