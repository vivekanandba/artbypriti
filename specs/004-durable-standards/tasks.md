# Tasks: Durable Standards

**Branch**: `004-durable-standards` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 0 — Repair

- [x] **T001** Re-apply the deploy-time gates and `make setup`/`preflight` lost in PR #19 to a
      `git reset --hard` during a hook test. *Verified from `git show HEAD:<file>` this time, not from
      the working tree.* Recorded as ledger entry #8.

## Phase 1 — Shared constitution (US1, P1)

- [x] **T002** Read all four sibling constitutions and `~/.claude/CLAUDE.md`; extract only what
      converged independently.
- [x] **T003** Write `constitution/base.md` (5 principles, each citing its sources) + `VERSION`.
- [x] **T004** Splice the base into the project constitution between markers.
- [x] **T005** `scripts/check-constitution.py` — byte-compare the block against the base; wire into
      `make check` and `pre-commit`.
- [x] **T006** Prove drift detection in both directions.
- [x] **T007** Absorb principles VI–IX from the uncommitted `docs/fill-constitution-and-claude-md`
      branch so that work survives instead of losing a merge conflict.
- [x] **T008** `scripts/install-constitution.sh` to vendor into a sibling repo, preserving its own
      principles. **Not run against any sibling** — their maintainer decides.

## Phase 2 — Continuous learning (US2/US3, P1/P2)

- [x] **T009** `scripts/check-live.py` — key pages, masters still absent, archive still resolving;
      retries so transient noise does not cry wolf.
- [x] **T010** `.github/workflows/health.yml` — weekly `live` + `suite` jobs, deliberately uncached.
- [x] **T011** `docs/incidents.md` — 9 entries including the two caused by my own tooling, and the
      one where the honest answer is "no gate can catch this".
- [x] **T012** `make live`.

## Deferred

- [ ] **T013** Run the constitution installer against `landseer`, `resumefit`, `gadjoy` — needs their
      maintainer's go-ahead.
- [~] **T014** ~~Fix `resumefit/scripts/install-hooks.sh`, which aborts on any repo containing
      `specs/`.~~ **WITHDRAWN 2026-10-30 — the claim was false.** Re-checked against the file:
      line 47 reads `if [ -d specs ] || [ -d .specify ]`, which *enables* the spec gate where
      specs live and skips it elsewhere; `scripts/check-spec.sh` exists and was committed
      2026-08-05, before the session that reported this. The original note generalised one
      local failure into a defect in another project's code without reproducing it. Struck
      through rather than deleted, because a withdrawn claim is itself a record
      (`CON-DATA-001`) — and because resumefit was never told about a bug it did not have.
- [ ] **T015** Decide whether `~/.claude/CLAUDE.md` should become the canonical upstream for
      `constitution/base.md`.
- [ ] **T016** Branch protection / rulesets — still the owner's setting, now one layer of seven.
