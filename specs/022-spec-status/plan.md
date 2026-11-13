# Implementation Plan: A Spec Says Whether It Shipped

**Spec**: [spec.md](./spec.md) · **Branch**: `022-spec-status` · **Created**: 2026-11-13

## Approach

1. Correct the 15 headers once, from the merged PR history, with a script that asserts it never
   writes an emptied file (`CON-PROC-018`).
2. Compare header and registry on every run — an error, because it reads only files and so can
   never block an unrelated change for a reason outside it.
3. With a base ref, warn about specs that have shipped but still say Draft.

## Why the staleness check warns instead of failing

The PR after a spec merges is frequently someone else's, and often a content edit. Failing it
would make the artist's dimensions PR red over the developer's bookkeeping. The agreement check
is the hard gate; staleness is surfaced on every PR until fixed.

## Verification

Green on the corrected tree; red when one header is reverted to Draft; the warning fires for the
same spec against `origin/main`; three tests red under a mutation of the status mapping.
