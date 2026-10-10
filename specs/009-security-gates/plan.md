# Implementation Plan: Security Gates

**Branch**: `009-security-gates` | **Date**: 2026-10-10 | **Spec**: [spec.md](./spec.md)

## Summary

Close the three live `CON-SEC` obligations by reusing the fleet's existing pattern, and state the
limits this host imposes rather than pretending they are choices.

## Constitution Check

| Rule | Compliance |
| --- | --- |
| `CON-SEC-002` | gitleaks full history + `pip-audit` + `npm audit`, all failing the build |
| `CON-SEC-003` | Shipped and build trees audited separately, with the shipped side guarded by its own script |
| `CON-SEC-004` | CSP + Referrer-Policy declared; the three headers this host *cannot* send are each named with the reason |
| `CON-VER-005` | The secret scan's **blind spot** is documented — a green badge that implied incident #10 was covered would misdiagnose |
| `CON-PROC-003` | CVE feeds kept off the PR path so a gate nobody can act on does not train bypassing |
| `CON-REP-002` | Three gaps listed in `docs/security.md`, not just the wins |

## Technical decisions

### Reuse wealth-weave's gitleaks pattern

Pinned `8.21.2`, downloaded and installed into `$RUNNER_TEMP`, `fetch-depth: 0`. Named in
`CON-SEC-002` as the reference implementation; copying it keeps one dialect across the fleet.

### No allowlist — and that is the finding

The plan assumed the `.wpress` archive would trip the scan and need allowlisting with a pointer to
incident #10. **Measuring disproved it**: 0 findings across full history. The archive is binary, and
gitleaks detects credentials, not password hashes or personal data.

So an allowlist would have suppressed **nothing real** while permanently blinding those paths to
future findings — a net loss. Instead the blind spot is written into `docs/security.md`: the scan is
green *and* incident #10 is uncovered by it, both true at once.

### Prove the scanner fires before trusting it

First attempt used AWS's documentation example key — gitleaks allowlists it by design, so it
reported clean and I nearly concluded the gate worked. Retested with a GitHub PAT, a Slack token and
an RSA private key: 3/3 caught, exit 1. A gate never observed failing is not known to work
(`CON-PROC-005`).

### Measure the CSP against built output, then against a browser

Templates say what a page *probably* contains. The built output showed **184 `style=` attributes**,
which is what forces `'unsafe-inline'` on `style-src` — invisible from the template alone. The
policy was then A/B'd in a real browser against a build without it: zero violations either side.

The lightbox did **not** open in that probe — but it did not open *without* the CSP either, so the
policy is not the cause. That is recorded as an open question for the E2E work rather than claimed
as verified.

### Rejected

- **An allowlist for `.wpress`** — see above; suppresses nothing, blinds future findings.
- **Fixing `style-src` now** — 184 attributes; changes rendering; belongs in its own reviewed change.
- **`npm audit` in the weekly job only** — `CON-SEC-002` says CI gate, so it runs per PR at
  `--audit-level=high`, with the noisier feed left to the schedule.

## Verification

| Claim | Method | Result |
| --- | --- | --- |
| Scanner detects real secrets | planted PAT + Slack token + RSA key | **3/3, exit 1**; clean on removal |
| History is genuinely clean | full scan, no allowlist | 0 findings, 61 commits |
| Shipped tree stays dependency-free | planted a CDN `<script>` | fails, names page and host |
| CSP reaches the browser | built output + live assertion | 60/60 non-empty pages; live check currently **red** until this deploys, which is correct |
| CSP breaks nothing | browser A/B with and without | 0 violations both sides |
| Coverage floor holds | `coverage report` | **99%** with the new script covered |
