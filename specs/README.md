# Specs

One directory per feature: `spec.md` (intent and acceptance criteria), `plan.md` (approach and
decisions), `tasks.md` (what was actually done). Created with `/speckit-specify`, and validated by
`scripts/check-specs.py` — an unfilled template fails, and so does a spec missing from the table
below.

| # | Feature | Status | Shipped as |
| --- | --- | --- | --- |
| [000](./000-backend-optimization/) | Backend & build optimization | ⚠️ **Backfilled** — shipped before this process existed | PR #15 |
| [001](./001-quality-gates/) | Automated quality gates | Implemented | PR #16 |
| [002](./002-spec-process/) | Spec-first, gate-last enforcement | Implemented | PR #17 |
| [003](./003-defense-in-depth/) | Defense in depth: local hooks + deploy-time gates | Implemented | PR #19 |
| [004](./004-durable-standards/) | Shared constitution & continuous learning | Implemented | PR #20 |
| [005](./005-adopt-house-standards/) | Adopt the house standards, delete the duplicates | Implemented | PR #22 |
| [006](./006-image-resolution/) | Stop upscaling the paintings (grid) | Implemented | PR #23 |
| [008](./008-test-strategy/) | Test the gates — 0% → 99% coverage | Implemented | PR #24 |
| [009](./009-installable-gallery/) | Installable gallery, offline pages | Implemented | PR #27 |
| [010](./010-security-gates/) | Security gates (CON-SEC-002/003/004) | Implemented | PR #26 |
| [011](./011-larger-artwork/) | Show the paintings larger on their own page | Implemented | PR #28 |
| [012](./012-citation-guard/) | Guard the constitution citations against rot | Implemented | PR #29 |
| [014](./014-wider-testing/) | Accessibility, responsive and journey tests; lint the gates | In review | this PR |

**Two numbering notes, recorded rather than tidied away:**

- **There is no `007`.** It was the working number for the larger-artwork change while that work sat
  deferred behind `006`; by the time it was written the branch had become `011`, and renumbering
  shipped specs to close a gap would break every citation pointing at them. The gap is an artefact
  of planning order, not a missing document.
- **There is no `013`.** It was the branch name for a docs-only change (PR #30: the artist's
  open questions, a withdrawn claim, and the constitution handoff). Those paths need no spec,
  so the number was used by a branch and never by a specification.
- **`010` was `009` first.** Two specs were written in parallel and both claimed `009`;
  `009-installable-gallery` landed first and kept it. This is the same collision the project hit
  with constitution rule IDs, and the same resolution: first to land keeps the number.

**On the Status column:** it records whether the work *shipped*, which is what a reader of this index
wants. Several `spec.md` files still carry `Status: Draft` in their own header even though they are
merged and deployed — those headers are stale. The disagreement is noted here rather than silently
reconciled (`CON-DATA-003`); correcting them is tracked separately.

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

Adding a spec means adding its row above: `check-specs.py` compares the directories on disk against
the rows in this table and fails if they disagree. The registry drifted to 4 of 11 before that check
existed.
