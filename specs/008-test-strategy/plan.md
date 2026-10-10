# Implementation Plan: Test the Gates

**Branch**: `008-test-strategy` | **Date**: 2026-09-20 | **Spec**: [spec.md](./spec.md)

## Summary

Unit-test the four gate scripts to a enforced floor, with a named regression test for each bug the
gates have actually shipped.

## Constitution Check

| Rule | Compliance |
| --- | --- |
| `CON-COV-001` — coverage says less than you think | The percentage is stated *and* subordinated to the five named regression tests |
| `CON-COV-002` — a floor only ratchets up | `COVERAGE_FLOOR ?= 95`, currently exceeded at 99% |
| `CON-PROC-005` — watch a test fail | Every regression test was run against the reintroduced bug |
| `CON-VER-004` — run the check where it runs | Tests run in CI, not only locally; `requirements-dev.txt` installed there |
| `CON-REP-002` — report what you didn't do | `check_hygiene.py` exclusion is stated, not silent |

## Technical decisions

### Fresh module per test

The scripts keep module-level `errors`/`warnings`/`notes` lists. A cached module would leak findings
between tests and turn real failures green, so `conftest.load()` returns a new module object each
time and clears whichever buckets that script has.

### Real bytes, real git, mocked network

- The JPEG/PNG reader is exercised on genuine header bytes, including padded `0xFF` runs, standalone
  markers and truncation. Stubbing it would have tested nothing — it exists precisely to avoid Pillow.
- The spec-required gate runs against a real git repository, because it is a gate *about* git.
- `check-live.py` is fully mocked: a unit suite must never depend on production being reachable.

### One production change, and why it was warranted

`check-live.py` parsed `sys.argv` **at import time**. Importing it from a test runner picked up the
runner's own arguments as the site URL, every request then failed URL construction, and the retry
backoff slept for real — the class took **300 s** before timing out. Moving the parse into `main()`
is a small change that removes surprising import-time behaviour and makes the script testable at all.
Verified against production afterwards: still clean. Suite now runs in **0.06 s**.

### Rejected

- **Mocking git** for the spec gate — would assert my mock's behaviour, not the gate's.
- **Testing `tools/check_hygiene.py`** — house-owned; tests belong upstream.
- **Chasing 100%** — the two remaining lines are defensive `continue`/`return None` branches in the
  JPEG scanner. Contriving inputs to reach them would add fragile tests for no behavioural gain.

## Verification

| Claim | Method | Result |
| --- | --- | --- |
| Coverage ≥95% | `coverage report` | **99%**, 3 files at 100% |
| Floor blocks | `COVERAGE_FLOOR=100 make test` | exits 2 |
| Five bugs caught | one named test each | 8 regression tests pass |
| Suite is fast | `make check` timed | ~19 s including every other gate |
| No network | `check-live` tests mocked | 0.06 s for the file |
