# Handoff: four amendment proposals this repo raised

**Status: not adopted, and not adoptable from here.** These are proposals in
`vivekanandba/fleet` (`proposals/`), raised from incidents in this repository. They need an edit
in **that** repo; this document states exactly what, so the work does not have to be re-derived.

Why it is written down rather than done: `CON-PROC-007` — automation proposes, humans dispose. A
proposal is a proposal, and one project's local lesson must not become a fleet standard by a
session quietly editing another repository.

Verified against the mirror at `~/data-dash/.constitution-mirror` @ `df884fd` on **2026-10-30**.

## The collision

Two proposals claim `CON-PROC-009`. That ID is **taken**:

> ### CON-PROC-009 · A review loop ends on a clean round, not on a green suite

— adopted from a trailward incident (PRs #67, #69, #70), after these proposals were written.

`CON-PROC` currently defines **001–009, 011, 012, 013**. So:

- **`CON-PROC-010` is an unexplained gap.** It appears nowhere in the fleet repo outside these
  proposals: never defined, and never marked retired-in-place as the amendment rules require. Its
  history cannot be reconstructed from the repo, so **do not fill it** — a gap whose cause is
  unknown may be a rule retired incorrectly, and reusing the number would redefine it.
- **Next genuinely free: `CON-PROC-014`, `CON-PROC-015`.** Append-only after the highest defined.

## What each proposal needs

| Proposal | Currently claims | Should become |
| --- | --- | --- |
| `2026-08-08-verify-from-the-commit.md` | `CON-PROC-009` | **`CON-PROC-014`** |
| `2026-08-08-history-is-additive.md` | `CON-PROC-010` (and `-009` as fallback) | **`CON-PROC-015`** + the exception below |
| `2026-08-08-never-fabricate-domain-content.md` | `CON-DATA-006` | **unchanged** — `CON-DATA` defines 001–005, so 006 is genuinely next |
| `2026-08-08-gates-need-a-bypass.md` | amends `CON-PROC-003` | **unchanged** — strengthens an existing rule, needs no new ID |

Each file's `**Proposed ID**:` line and its `### CON-...` heading both carry the number, and
`history-is-additive`'s line reads *"next free after CON-PROC-009 if that lands; otherwise -009"* —
that parenthetical is now stale and should go.

## `history-is-additive` also needs a security exception

As written it says:

> Do not force-push a shared branch or rewrite published history: it buys disk and costs every
> existing clone.

**As worded, that forbids the correct response to a secret or personal-data exposure.** Purging a
leaked credential or a personal-data dump from git history *requires* rewriting published history;
leaving it reachable to preserve clones is the wrong trade.

This is not hypothetical here. [Incident #10](incidents.md) is a public `.wpress` WordPress backup
in this repo's own history containing a password hash and roughly 1,250 email addresses. The owner
accepted that risk and chose rotation over a purge — but that was a *decision*, and the rule as
drafted would have removed the option.

Suggested addition to the proposed text:

> **Exception — security remediation.** A credential, key or personal-data exposure is the one case
> where rewriting published history is correct. Purge it, rotate what leaked, and tell every clone
> holder; the cost to existing clones is the smaller harm. `CON-SEC-001` governs the rotation, and
> the decision to purge or accept the risk is the owner's, recorded either way.

## What this repo already does about it

- `docs/constitution-ids-proposed.txt` lists `CON-DATA-006` and `CON-PROC-010` with reasons, so the
  citation gate (`scripts/check-citations.py`) accepts them as **proposals** rather than typos —
  and reports them as proposed, so the pending state is visible on every CI run.
- When a proposal is adopted upstream, that gate **fails** until the entry is removed, which is the
  prompt to update the citations here. The handoff cannot be silently forgotten.

## To act on this

In the fleet repo, on a branch, through a reviewed PR (`CON-PROC-004`, `CON-PROC-008`): renumber the
two proposals, drop the stale parenthetical, add the security exception. None of it touches
`CONSTITUTION.md` — adoption remains a separate, human decision.
