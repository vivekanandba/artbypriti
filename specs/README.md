# Specs

One directory per feature: `spec.md` (intent and acceptance criteria), `plan.md` (approach and
decisions), `tasks.md` (what was actually done). Created with `/speckit-specify`, and validated by
`scripts/check-specs.py` — an unfilled template fails.

| # | Feature | Status | Shipped as |
| --- | --- | --- | --- |
| [000](./000-backend-optimization/) | Backend & build optimization | ⚠️ **Backfilled** — shipped before this process existed | PR #15 |
| [001](./001-quality-gates/) | Automated quality gates | Implemented | PR #16 |
| [002](./002-spec-process/) | Spec-first, gate-last enforcement | Implemented | PR #17 |
| [009](./009-installable-gallery/) | Installable gallery, offline pages | Implemented | this PR |

## Why 000 is numbered out of band

`000-backend-optimization` documents work that shipped **with no spec**. It is backfilled, and
numbered 000 to say so plainly rather than to blend into a tidy sequence. It records the measurements
that were taken, the alternatives that were rejected and why, and the two conclusions that turned out
to be wrong — because a backfill pretending the process was followed would be worse than no backfill.

## Working on a feature

```bash
/speckit-specify   # create specs/NNN-name/spec.md on a matching branch
/speckit-plan      # add plan.md
/speckit-tasks     # add tasks.md
make check         # spec hygiene runs here, alongside the content and output gates
```

A change touching templates, styles, config, CI, or scripts must either update something here or
record `No-Spec: <reason>` in a commit message or the PR body. See the Development Workflow section of
[the constitution](../.specify/memory/constitution.md).
