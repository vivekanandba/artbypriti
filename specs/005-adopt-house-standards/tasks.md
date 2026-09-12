# Tasks: Adopt the House Standards

**Branch**: `005-adopt-house-standards` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 0 — Compare before changing

- [x] **T001** Read `~/data-dash/constitution` end to end: `CONSTITUTION.md` (24 rules), `README.md`
      (the layer model), `PROJECTS.md`, `skills/`, `proposals/`.
- [x] **T002** Map every principle written in this repo to a house rule ID. *Result: 3 of 5 shared
      principles already existed verbatim in intent; 1 partially; 1 genuinely new.*
- [x] **T003** Discover `chore/house-gates` — house gates **v1.2.0** already staged here, while I had
      vendored resumefit's **v1.0.0**. My version was a version behind.

## Phase 1 — Delete the duplication (US1, P1)

- [x] **T004** Remove `constitution/base.md`, `constitution/VERSION`,
      `scripts/check-constitution.py`, `scripts/install-constitution.sh`.
- [x] **T005** Remove the vendored v1.0.0 bundle and the hooks calling it.
- [x] **T006** Reduce `.githooks/pre-commit` to the repo-specific spec check only, so the house
      installer's block prepends cleanly above it.
- [x] **T007** Rewrite `.specify/memory/constitution.md`: 190 → 115 lines, 13 house-rule citations,
      9 project-specific principles retained.
- [x] **T008** `CLAUDE.md` states the layer model and cites rather than restates.

## Phase 2 — Send the transferable lessons upstream (US3, P2)

- [x] **T009** `proposals/2026-08-08-verify-from-the-commit.md` — new `CON-PROC-009`. The incident:
      a hook test ran `git reset --hard`, destroying verified-but-unstaged work, and the change was
      reported as shipped while production stayed unguarded for three merges.
- [x] **T010** `proposals/2026-08-08-history-is-additive.md` — new `CON-PROC-010`, from removing
      1.38 GB by reference rather than by rewrite; converged with resumefit V.
- [x] **T011** `proposals/2026-08-08-never-fabricate-domain-content.md` — new `CON-DATA-006`;
      three projects wrote it locally before anyone wrote it once.
- [x] **T012** `proposals/2026-08-08-gates-need-a-bypass.md` — **strengthen** `CON-PROC-003` rather
      than add a near-duplicate ID, per the `lesson` skill's own guidance.

## Not done

- [ ] **T013** Accept any proposal — a reviewed commit in the constitution repo; the owner's call.
- [ ] **T014** Merge `chore/house-gates`.
- [ ] **T015** Fix `resumefit/scripts/install-hooks.sh`, which still aborts on any repo with
      `specs/` (its `check-spec.sh` no longer exists).
