# Tasks: Guard the Constitution Citations

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Branch**: `012-citation-guard`

## Measure first

- [x] **T001** Counted the citations. The plan said "11 IDs cited"; the real figure on `main` @
  `16597cf` is **25 distinct IDs** across specs, scripts, docs and templates. Corrected before
  designing anything around the smaller number.
- [x] **T002** Established the authority: `~/.claude/CLAUDE.md` is a **symlink** into
  `~/data-dash/.constitution-mirror/CONSTITUTION.md`, which defines **35** rule IDs. Checked rather
  than assumed — the IDs appear in five files in that mirror, and only one of them is the
  constitution.
- [x] **T003** Diffed cited against defined: **2 dangling** — `CON-DATA-006` and `CON-PROC-010`,
  both in `specs/005-adopt-house-standards/tasks.md`, and **both proposals this repo made**. So the
  gate's central requirement was not "reject the unknown" but "tell a proposal from a typo".

## Build

- [x] **T004** `docs/constitution-ids.txt` — the vendored snapshot, with provenance in the header
  (source repo, mirror commit, date, refresh command). Vendored because CI cannot read `~/.claude`
  (`CON-VER-004`).
- [x] **T005** `docs/constitution-ids-proposed.txt` — the two real proposals, each with a reason. An
  entry without a reason is an error; the exemption costs a sentence by design.
- [x] **T006** `scripts/check-citations.py` — fails on an unresolvable ID naming file and line,
  errors on a proposal that has since been adopted, warns on an exemption nothing cites, and reports
  freshness as a **warning** (mirror present) or **SKIPPED** (no mirror), never as a green tick that
  checked nothing (`CON-VER-005`).
- [x] **T007** `scripts/refresh-constitution-ids.py` behind `make constitution-ids`. It refuses to
  write an empty list when the mirror yields no IDs — otherwise an upstream heading-format change
  would make all 26 citations dangle at once, reading as 26 broken citations instead of one broken
  parser.
- [x] **T008** Wired into `make check`, so it gates every PR rather than being a thing someone
  remembers to run.

## What the first run found

- [x] **T009** The finished gate immediately failed on **the spec and its own docstring**, which
  quote bad IDs as examples. A gate that makes its own documentation unwritable gets deleted, so
  added the `not-a-citation` per-line marker — the same bargain `check-specs.py` strikes with
  `No-Spec:`: visible in the diff, suppresses one line, never a file.
- [x] **T010** Reworded the spec and docstring to describe the typo rather than spell it, keeping
  the marker for the genuine cases (test fixtures), so the suppression is rare rather than habitual.

## Prove it

- [x] **T011** Planted a citation to a non-existent rule in `docs/security.md`: gate **exit 1**,
  naming `docs/security.md:107`. Removed → clean. (`CON-PROC-005`)
- [x] **T012** 15 unit tests for the gate and 8 for the generator, covering every branch that
  matters: dangling, adopted-but-exempted, reason-less exemption, dead exemption, letter-O typo,
  suppression, absent mirror, stale mirror, unparseable mirror, missing vendored list.
- [x] **T013** Mutation-tested **three** assertions — never report dangling, never check adopted
  proposals, always suppress — and each mutation was caught. The second mutation silently failed to
  apply the first time (the shell ate an `&`), and the run that "passed" proved nothing; re-applied
  properly and it failed as it should. A mutation test that does not mutate is a test that cannot
  fail.
- [x] **T014** Fixed a test that polluted its own subject: the fake mirror was written **inside**
  the scanned directory, so the gate read its rule *definitions* as citations. Moved outside via
  `tmp_path_factory`.

## Coverage, honestly

- [x] **T015** The new generator took the suite to **94%**, under the floor, and `make test`
  **failed** as designed (exit 2). Fixed by testing it, not by lowering the floor (`CON-COV-002`).
  Back to **163 tests, 98%**.

## Registry

- [x] **T016** Added the `012` row to `specs/README.md`. Worth recording: the registry gate shipped
  in PR #28 caught this spec's missing row on its **first real use**, one PR later.

## Verify

- [x] **T017** `make check` → **exit 0**, including the new gate.
- [x] **T018** `make test` → **163 passed, 98%**, floor ≥95%.
- [x] **T019** `make constitution-ids` regenerates the snapshot from the mirror: 35 IDs, matching.
- [x] **T020** Gate output on the real repo: 26 distinct IDs cited, 35 defined, 2 reported as
  proposed, 0 errors.

## Deliberately not done

- **Adopting, renumbering or withdrawing the two pending proposals.** That is the separate handoff
  (`CON-PROC-010` in particular needs renumbering *and* a security-remediation exception). This
  change only stops their citations being indistinguishable from typos — and by listing them with
  reasons, it makes the pending handoff visible in the repo rather than only in a session.
- **Checking that a citation is apt.** Whether `CON-VER-005` is the right rule for the sentence it
  sits in is a judgement, not a check (`002-spec-process`, "Honest limits").
- **Scheduled auto-refresh** of the snapshot (`CON-PROC-007`: automation proposes, humans dispose).
