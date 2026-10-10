# Feature Specification: Security Gates (CON-SEC-002/003/004)

**Feature Branch**: `009-security-gates`

**Created**: 2026-10-10

**Status**: Draft

**Input**: `CON-SEC-002`, `CON-SEC-003` and `CON-SEC-004` landed in the shared constitution. This
repository cites that constitution and complied with none of them.

## Problem

Three security rules became live obligations while this repo was doing other work. artbypriti
scanned **nothing** — no dependency audit, no secret scan — and declared **no** security headers.
Ten of twelve fleet projects were in the same state when the rules were written; this closes it
here.

The rules are not generic hardening. Each names an incident, and two name constraints this project
actually has: `CON-SEC-003` warns that a single vulnerability count misleads, and `CON-SEC-004`
names **GitHub Pages** explicitly as a host that cannot send headers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A committed secret cannot reach the remote unnoticed (Priority: P1)

As the owner, if a credential is ever committed — and then removed — CI still finds it, because the
history is what leaks.

**Acceptance Scenarios**:

1. **Given** a credential anywhere in git history, **When** CI runs, **Then** the build fails.
2. **Given** a clean history, **When** CI runs, **Then** it passes — no allowlist suppressing
   anything.
3. **Given** the scan passes, **When** its coverage is described, **Then** what it does *not* cover
   is stated too.

---

### User Story 2 - The shipped site stays dependency-free (Priority: P1)

As the owner, the day a CDN script or remote webfont enters the published site, I am told — because
that is the moment this site acquires a supply chain it did not have.

**Acceptance Scenarios**:

1. **Given** a page loading from an external origin, **When** the audit runs, **Then** it fails and
   names the page and host.
2. **Given** `schema.org` itemtypes and XML namespaces, **When** the audit runs, **Then** they are
   **not** treated as fetches.
3. **Given** build-time dependencies, **When** they are audited, **Then** it is a **separate**
   invocation with its own threshold (`CON-SEC-003`).

---

### User Story 3 - The browser is told what it may load (Priority: P2)

As a visitor, the page restricts what it can execute, and where it cannot, that limitation is
documented rather than implied.

**Acceptance Scenarios**:

1. **Given** any rendered page, **When** it loads, **Then** it carries a CSP restricting
   `script-src` to `'self'`.
2. **Given** the policy, **When** the site is exercised in a real browser, **Then** there are
   **zero** CSP violations — a policy that breaks the site gets removed, not fixed.
3. **Given** the deployed site, **When** the live check runs, **Then** it asserts the CSP against
   the **running** site, not the template.
4. **Given** headers this host cannot send, **When** the posture is documented, **Then** each is
   named with the reason.

## Requirements *(mandatory)*

- **FR-001**: `gitleaks` over full history (`fetch-depth: 0`), pinned version, failing on any
  finding.
- **FR-002**: `pip-audit --strict` on `requirements-dev.txt`; `npm audit --audit-level=high`.
- **FR-003**: `scripts/check-shipped-deps.py` fails if the published site loads any external origin.
- **FR-004**: A CSP and `Referrer-Policy` via meta tags, since the host cannot send headers.
- **FR-005**: `check-live.py` asserts the CSP against the deployed site.
- **FR-006**: `docs/security.md` states the posture, including what is impossible and what the
  secret scan does not cover.
- **FR-007**: Deterministic scans per PR; CVE feeds on the weekly schedule.

## Success Criteria

- **SC-001**: A planted GitHub PAT, Slack token and RSA private key are all caught. **Verified —
  3/3, exit 1**, and clean again on removal.
- **SC-002**: Full-history scan is green **without any allowlist**. Verified: 0 findings.
- **SC-003**: A planted CDN script fails the shipped-tree audit. Verified.
- **SC-004**: CSP present on every non-empty page; **zero** browser CSP violations. Verified: 60/60
  (the 61st is a deliberately empty 0-byte taxonomy page), 0 violations, A/B'd against a build
  without the policy.
- **SC-005**: Coverage floor still ≥95% with the new script included. Verified: **99%**.

## What this deliberately does not do

- **No gitleaks allowlist.** The `.wpress` archive is *not* detected — it is binary, and gitleaks
  has no rules for password hashes or personal data. Allowlisting it would suppress nothing real
  while blinding those paths to future findings. Incident #10 stays an accepted risk managed by
  decision, not by this scanner, and `docs/security.md` says so.
- **No fix for `style-src 'unsafe-inline'`.** 184 inline `style=` attributes from the theme force
  it. Moving them to CSS changes rendering and belongs in its own reviewed change.
- **Clickjacking and MIME-sniffing protection** are unachievable on GitHub Pages. Recorded, not
  worked around.
