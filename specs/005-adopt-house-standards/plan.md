# Implementation Plan: Adopt the House Standards

**Branch**: `005-adopt-house-standards` | **Date**: 2026-08-08 | **Spec**: [spec.md](./spec.md)

## Summary

Delete what this repo re-derived, cite what the house already says, keep only the deltas, and send
the genuinely new lessons upstream as proposals.

## Constitution Check

Against the **house** rules, which is the point of this change:

| Rule | Compliance |
| --- | --- |
| `CON-VER-004` (run a check where it will actually run) | Why `check-specs.py` stays vendored in-repo: CI only gets the repository, so a skill outside it cannot gate CI |
| `CON-PROC-007` (automation proposes; humans dispose) | Four proposals written to `proposals/`; `CONSTITUTION.md` untouched |
| `CON-PROC-003` (extend the layer that should have caught it) | No enforcement lost — every gate that ran before still runs |
| `CON-REP-002` (report the cost of what you didn't do) | The duplication is named plainly, including that my vendored bundle was a version behind |

## Technical decisions

### Cite, don't restate — including deleting my own work

`constitution/base.md` restated five principles in full. The house model forbids exactly this
("copies drift; citations don't"), and `harvest.py` would have flagged it. It is deleted rather
than reconciled: a second copy of a rule is not a smaller problem than a wrong one.

### Defer to `house-gates` v1.2.0

I vendored resumefit's v1.0.0 bash bundle; the estate has since moved to a config-driven Python
implementation, already staged on this repo's `chore/house-gates` branch. Keeping mine would have
meant two hygiene gates, one of them stale. Deleted.

`.githooks/pre-commit` is kept holding **only** the repo-specific spec check, because the house
installer prepends its block and preserves what is below — so the two compose by design instead of
conflicting.

### What stays local, and why

Hugo's silent-fallback behaviour, the 40 MB payload budget, the images-are-the-product rule, the
vendored-theme discipline. None generalises: they are properties of a static gallery site.

### Rejected

- **Keeping `base.md` as a "cache" of the house rules** — that is the drift the model exists to
  prevent.
- **Editing `CONSTITUTION.md` directly** — forbidden by `CON-PROC-007`; proposals only.
- **Merging `chore/house-gates` myself** — the owner's branch and call.

## Verification approach

| Claim | How |
| --- | --- |
| No enforcement lost | `make check` and `make visual` pass; CI gates unchanged |
| Hooks compose | `.githooks/pre-commit` holds only the local check, below where the house block prepends |
| Nothing restated | Citations counted; no house-rule prose remains |
| Proposals are proposals | `CONSTITUTION.md` unmodified — verified by `git status` in that repo |
