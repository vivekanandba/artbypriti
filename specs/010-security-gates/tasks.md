# Tasks: Security Gates

**Branch**: `009-security-gates` (renumbered to spec 010) | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

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
- [x] **T008b** CI caught my own mistake: the shipped-tree audit sat in the `security` job, which
      deliberately does not build, so it failed with "no built site". Moved into `make check`,
      which is the job that builds — an assertion about *published output* belongs with the other
      output assertions. The secret scan itself passed on the real runner.

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

## Phase 4 — Reconciling with the PWA (spec 009-installable-gallery)

- [x] **T019** Renumber 009 → 010. `009-installable-gallery` landed on main first and took the
      number; two specs sharing one number is the same collision this project has already hit
      with constitution rule IDs.
- [x] **T020** **The CSP would have silently broken the PWA.** `009` registers its service worker
      from an *inline* `<script>`, and `script-src 'self'` blocks inline execution. Measured in a
      browser before merging: **0 service-worker registrations, 1 CSP violation**. Because the
      registration catches its own errors by design ("an unregistered worker is a missing
      optimisation, never a broken page"), nothing would have reported the loss.
- [x] **T021** Move the registration to `assets/js/sw-register.js`, fingerprinted, with the worker
      URL carried on a `data-sw-url` attribute so Hugo still resolves it. Re-measured: **1
      registration, 0 violations**. Rejected the easy fix of adding `'unsafe-inline'`, which would
      gut the single most valuable directive.
- [x] **T022** Extend the layer that missed it (`CON-PROC-003`): `check_csp_matches_the_markup`
      fails any page that declares `script-src 'self'` while carrying an inline `<script>`.
      Proven by reintroducing the exact defect.
- [x] **T023** Rewrite `009`'s own assertion, which grepped index.html for the word
      "serviceWorker" — true only while the registration was inline, so it failed a *correct*
      site. It now follows the chain: tag → script exists → script really calls
      `serviceWorker.register` → worker file exists. Stronger than the string it replaces, and
      still passes the inline form.
- [x] **T024** Cover both with unit tests (16 new). *The shared `site` fixture was extended by
      009 to ship a complete PWA, so "missing file" cases had to delete what the fixture provided
      rather than decline to add it — two tests failed until that was understood.* Coverage back
      to **99%**.
