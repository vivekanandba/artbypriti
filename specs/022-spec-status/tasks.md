# Tasks: A Spec Says Whether It Shipped

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Branch**: `022-spec-status`

- [x] **T001** Measured: 15 headers said Draft; 14 registry rows said Implemented; row `020` was
  itself stale ("In review / this PR" after merging as #41).
- [x] **T002** Corrected all 15 headers to `Implemented — PR #N` from the merge history, and row
  `020` to PR #41.
- [x] **T003** `check_status_agreement` (error) and `check_shipped_specs_say_so` (warning).
- [x] **T004** 8 unit tests, including a missing status line and RETROACTIVE ≡ Backfilled. The
  test fixture's "clean tree" now carries a status that agrees with its registry — one existing
  test failed until it did, which is the check working.
- [x] **T005** Red end to end: one header reverted → error naming `011-larger-artwork`; the same
  spec against `origin/main` → the staleness warning. Mutation of the mapping → 3 tests red.
- [x] **T006** Replaced the registry's "the headers are stale, tracked separately" note with how
  status is now kept in step.
