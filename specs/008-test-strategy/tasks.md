# Tasks: Test the Gates

**Branch**: `008-test-strategy` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] **T001** `requirements-dev.txt`, `pytest.ini`, `.coveragerc`.
- [x] **T002** `conftest.py`: fresh-module loader, content-tree builder, real JPEG/PNG byte helpers.
      *Loader initially assumed every script had a `notes` list; `check-content.py` does not.*
- [x] **T003** `test_check_content.py` — 26 tests. 100%.
- [x] **T004** `test_check_output.py` — 39 tests incl. header-parser edge cases. 99%.
- [x] **T005** `test_check_specs.py` — 22 tests against a real git repo. 100%.
      *Fixture used `git init -b main`, which needs git ≥2.28; this box has 2.25, so the repo was
      never created and the tests "passed" on empty diffs. Caught by the assertions.*
- [x] **T006** `test_check_live.py` — 8 tests, network mocked. 100%.
      *Exposed import-time `sys.argv` parsing that made the class take 300 s; fixed in the script.*
- [x] **T007** `test_regressions.py` — one named test per historical gate bug, plus 3 site
      invariants (masters unpublished, image cache configured, deploy gated).
- [x] **T008** `make test` / `make coverage`; `check` depends on `test`.
- [x] **T009** CI runs the suite **before** the gates judge the change.
- [x] **T010** Prove the floor blocks at 100 and passes at 95.
- [x] **T011** Record the accepted `.wpress` risk as ledger entry #10 with its decision and date.

## Deferred (tracked, not forgotten)

- [ ] **T012** E2E expansion: journeys, lightbox, mobile 375 / tablet 768, 404.
- [ ] **T013** Accessibility via axe-core — currently zero coverage.
- [ ] **T014** `shellcheck` on `scripts/*.sh` and `.githooks/*`; `bandit` on the Python.
- [ ] **T015** Scheduled security suite: dependency CVEs, history secret scan, DNS, TLS expiry.
- [ ] **T016** Unit tests for `tools/check_hygiene.py` — belongs upstream in the house repo.
