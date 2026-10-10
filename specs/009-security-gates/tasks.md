# Tasks: Security Gates

**Branch**: `009-security-gates` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 0 — Measure before designing

- [x] **T001** Baseline gitleaks over full history. *0 findings — overturning the plan's central
      assumption that the `.wpress` blobs would need allowlisting.*
- [x] **T002** Establish *why*: the archive is binary, and gitleaks has **0** rules for password
      hashes or personal data. So the scan is green **and** incident #10 is uncovered by it.
- [x] **T003** Prove the scanner fires. *First attempt used AWS's documentation example key, which
      gitleaks allowlists by design — it reported clean and I nearly shipped a gate I had never
      seen fail. Retested with a PAT, Slack token and RSA key: 3/3.*
- [x] **T004** Measure the CSP surface from **built output**: 0 inline scripts, 0 inline style
      blocks, **184 `style=` attributes**, no external origins.

## Phase 1 — Gates (US1, US2)

- [x] **T005** `security` job in `pr-check.yml`: pinned gitleaks, `fetch-depth: 0`, full history.
- [x] **T006** `pip-audit --strict` and `npm audit --audit-level=high` as separate invocations
      (`CON-SEC-003`).
- [x] **T007** `scripts/check-shipped-deps.py` — fails on any external origin in the published site;
      ignores `schema.org` itemtypes and XML namespaces, which are identifiers rather than fetches.
- [x] **T008** Negative-test it with a planted CDN script.

## Phase 2 — Headers (US3)

- [x] **T009** CSP + `Referrer-Policy` in `head-custom.html`.
- [x] **T010** A/B in a real browser: zero violations with or without the policy.
- [x] **T011** `check-live.py` asserts the CSP against the **running** site. Currently red against
      production, correctly — the policy has not deployed yet.
- [x] **T012** `docs/security.md`: the posture, the three headers this host cannot send, and the
      secret scan's blind spot.

## Phase 3 — Keep the suite honest

- [x] **T013** Unit tests for `check-shipped-deps.py` and the new CSP branch. Coverage **99%**.
      *Repeated an earlier mistake — attached helper methods to a `PosixPath` again — and had to
      rewrite the fixture as a class, exactly as in spec 008.*
- [x] **T014** Updated two existing `check-live` tests whose healthy-site fixture predated the CSP
      assertion. Fixed the fixture rather than weakening the check.

## Deferred

- [ ] **T015** Move the 184 `style=` attributes into `custom.css` so `style-src` can drop
      `'unsafe-inline'`. Changes rendering; needs its own visual review.
- [ ] **T016** Weekly CVE re-scan in `health.yml` (feeds move without the code changing).
- [ ] **T017** `shellcheck` / `bandit` — part of the remaining test-strategy work.
- [ ] **T018** Characterise why the lightbox did not open in the probe. Pre-existing, unrelated to
      the CSP, but currently unverified either way.
