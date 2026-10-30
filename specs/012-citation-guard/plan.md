# Implementation Plan: Guard the Constitution Citations

**Spec**: [spec.md](./spec.md) · **Branch**: `012-citation-guard` · **Created**: 2026-10-30

## Approach

Three small pieces, because the hard part is not the matching — it is telling three things apart
that look identical in prose.

| Piece | Why it exists |
| --- | --- |
| `docs/constitution-ids.txt` | The vendored snapshot. CI only gets this repository, so a gate cannot read `~/.claude` (`CON-VER-004`). |
| `docs/constitution-ids-proposed.txt` | IDs this repo cites *as proposals*, each with a reason. Without it, an honest proposal is indistinguishable from a typo. |
| `scripts/check-citations.py` | The gate, wired into `make check`. |

Plus `scripts/refresh-constitution-ids.py` behind `make constitution-ids`, which is the only thing
that should write the snapshot.

## The three cases

A rule ID appearing in this repo is exactly one of:

1. **Adopted** — in the vendored list. Passes silently.
2. **Proposed** — in the proposed list, with a reason. Passes, and is *reported as proposed* so a
   reader of the output knows the citation is a record, not an authority.
3. **Neither** — a typo, a renumbering, or a rule that was retired upstream. **Fails**, naming every
   file and line.

The second case is the one that makes this gate survivable. This repo really has proposed two rules
(`CON-DATA-006`, `CON-PROC-010`) and cites them in `specs/005-adopt-house-standards/tasks.md`. A
gate that failed those would be failing honest text, and a gate that fails honest text gets switched
off — a lesson already written down twice here.

Two guards keep that exemption from rotting into a blanket:

- a proposed ID that has since been **adopted** is an **error** (the citation should now stand on
  its own);
- a proposed ID that **nothing cites** is a **warning** (a dead exemption).

## The regex is deliberately loose

`CON-[A-Z]{3,5}-[A-Z0-9]{2,4}` matches the numeric part loosely on purpose. A tight `[0-9]{3}`
would mean an ID with a letter O in place of a zero does not match the pattern at all — and
therefore sails through as "not a citation". The most convincing typo would be the one the checker
cannot see. Matching loosely and then failing to resolve is the behaviour that catches it.

## Freshness is a warning, never an error

The vendored list is a snapshot of a file in another repository. When a mirror happens to be present
locally the gate compares the two and **warns** on any difference. When there is no mirror — which
is always true in CI — it reports **SKIPPED**.

That distinction is the whole point: "checked, and identical" and "could not check" must not print
the same way (`CON-VER-005`, `CON-DATA-002`). And a rule landing upstream is not a reason to fail an
unrelated PR; it is a reason for a person to look (`CON-PROC-007` — automation proposes).

## The escape hatch, and why it is per-line

Writing *about* a bad ID — documenting this checker, recording a typo that was fixed — must stay
possible, or the gate makes its own documentation unwritable and someone deletes the gate. A line
carrying `not-a-citation` is skipped.

It is per-line and shows up in the diff, the same bargain `check-specs.py` already strikes with
`No-Spec:`: the hatch exists so nobody routes around the gate wholesale, and using it leaves a trace
a reviewer can see. This was not theoretical — the first run of the finished gate failed on the
spec and the script's own docstring.

## Verification

| What | How |
| --- | --- |
| Catches a dangling ID | Plant one in a real file, run the gate, remove it |
| Accepts a real proposal | The two genuine proposed IDs pass and are reported as proposed |
| Rejects a stale exemption | Mark an adopted ID as proposed; must fail |
| Honest about freshness | With no mirror, the line must read SKIPPED, not ok |
| Generator is safe | An unparseable mirror must refuse to write, not empty the file |
| Assertions can fail | Mutate each one and watch the test go red (`CON-PROC-005`) |
| Coverage | Floor ≥95% holds *including* the new generator |

## Alternatives considered

**Read the constitution live from `~/.claude`.** Rejected: `CON-VER-004`. It would pass locally and
check nothing in CI, which is worse than no gate because it looks like one.

**Vendor the full rule text, not just IDs.** Rejected: a copy that drifts is the exact problem the
citation convention exists to avoid. IDs are the minimum needed to answer "does this resolve?".

**Fail on a stale snapshot.** Rejected: it would make an unrelated upstream amendment break every
open PR here, and the pressure would be to delete the check rather than refresh the file.

**Infer "proposed" from nearby words** like *proposed* or *new*. Rejected: fragile, and it would
exempt any sentence that happened to contain the word. An explicit list with a stated reason is
auditable; a heuristic is not.

## Risks

| Risk | Mitigation |
| --- | --- |
| The snapshot goes stale and passes citations that no longer resolve | Freshness warning whenever a mirror is present; one-command refresh |
| The escape hatch gets used to silence a real break | Per-line, visible in review; it suppresses one line, never a file |
| Upstream changes its heading format | The generator refuses to write an empty list and says why, rather than making all 26 citations dangle at once |
