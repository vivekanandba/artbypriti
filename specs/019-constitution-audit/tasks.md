# Tasks: Meet the 22 Rules the Constitution Gained

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Branch**: `019-observability`

## Measure first

- [x] **T001** Extracted the full text of all 22 rules from the mirror and read each one, rather
  than judging from titles — which is how `CON-OBS-002`'s mention of this repo was found.
- [x] **T002** Pulled the health workflow's history: **four consecutive failures, Oct 12 → Nov 2,
  zero issues filed.** Cause, from the log: `/usr/bin/python3: No module named coverage`. The
  first failure was the Monday after #24 (mine) made `make check` depend on coverage. I was
  working in this repo during those weeks and did not notice.
- [x] **T003** Found #35 had already fixed it (Nov 7) — install step, reporter, tests, timeouts,
  house-gates 1.7.0. Confirmed green on Nov 9. Not redone.
- [x] **T004** Checked repo visibility (**public**), webfonts (**none**), service-worker blocking in
  screenshot tests (**present**), date-dependent output (**none**), the GCP uptime check
  (**present**), `grep -q` pipelines (**none**).

## Fix

- [x] **T005** `CON-PROC-016` — reproduced with a decoy repo (15 commits written into it), added
  an autouse `GIT_*` scrub in `conftest.py`, re-ran: decoy untouched, 27/27 pass. Verified the
  real repository holds no fixture commits and is not bare.
- [x] **T006** `CON-VER-010` — CI's two hand-written linter steps replaced by `make lint`;
  contract tests for image == lockfile, exact `@playwright/test` pin, and no restated pins.
- [x] **T007** `CON-COV-004` — `.githooks/*` (vendored house-gates v1.7.1) out of the style lint
  with the reason inline; `SHELL_FILES` is now `$(wildcard scripts/*.sh)`.
- [x] **T008** `CON-VER-011` — `check-citations.py` prints `mirror @ <commit> (<date>), generated
  <date> (<n> day(s) ago)` on every run; unknown provenance is reported as UNKNOWN, not guessed.
- [x] **T009** `CON-COV-005` — one build command; deploy runs the browser suite on its artifact
  before upload; contract tests that no workflow invokes `hugo` directly and the steps are in
  order. Ran the deploy's exact commands locally: 33 passed.
- [x] **T010** `CON-OBS-003` — `canary` input on `health.yml`.
- [x] **T011** Wrote the contract tests without PyYAML, which is not a dependency of this suite —
  a test that fails on `import yaml` in CI would have been a gate that cannot run (`CON-PROC-014`).

## Correct myself

- [x] **T012** Withdrew `CON-VER-012` as a gap: both uploads are `if: failure()`.

## Verify

- [x] **T013** Every contract test mutation-tested red, then restored.
- [x] **T014** `make check-all` exit 0.

## After merge — the canary, fired and recorded (`CON-OBS-003`)

- [x] **T015** Dispatched `health.yml` on `main` with `canary: true` at **2026-11-13 21:21:12Z**
  (run 43509940327). `live site` failed on purpose, `suite still current` passed, and the
  reporter ran. **Issue #40 opened at 21:23:46Z** — 2 min 34 s after dispatch. A normal dispatch
  (run 43510924281) succeeded and **closed #40 at 21:29:53Z**. Both halves of the path proven on
  `main`.
- [x] **T016** But the issue reaching GitHub is not the same as a person being told, and that
  half could **not** be confirmed: #40 was opened by `github-actions` with **no assignee and no
  mention**, so it notifies only whoever happens to watch the repo, and this session's token
  lacks the `notifications` scope to read the owner's inbox. Recorded as unverified rather than
  claimed (`CON-VER-007`). Fixed in the follow-up: the reporter now **assigns** the issue to the
  repo owner (`NOTIFY`), because GitHub always notifies an assignee — best effort, falling back
  to an unassigned issue rather than losing the alert. 6 unit tests; assignment and fallback each
  mutation-tested red.
- [ ] **T017** Owner to confirm, once, that an assigned failure issue arrives in their GitHub
  notifications or email. This cannot be checked from here.
