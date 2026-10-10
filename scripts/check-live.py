#!/usr/bin/env python3
"""Watch the live site when nobody is changing it.

Every other gate here is triggered by a commit. Nothing notices decay: a certificate
expiring, DNS moving, an external link rotting, a deploy that quietly stopped happening.
This runs on a schedule and checks the deployed site rather than the repository.

Usage:  python3 scripts/check-live.py [base_url]
Exit:   0 = healthy (warnings allowed), 1 = something is wrong
"""
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://artbypriti.com"
PAGES = ["/", "/about/", "/request/", "/olive/", "/categories/acrylic-on-canvas/", "/robots.txt", "/sitemap.xml"]
ARCHIVE = "https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy"
# The masters were removed from the payload; if one is reachable again, publishResources regressed.
MUST_404 = "/olive/Olive.jpg"

errors, warnings, notes = [], [], []


def fetch(url, tries=3):
    """Retry before reporting: one flaky response must not cry wolf (NFR-002)."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "artbypriti-healthcheck"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception as e:  # network-level failure
            last = e
            time.sleep(2 * (attempt + 1))
    return None, str(last).encode()


def main(base=None):
    # Read argv here, not at import. Parsing it at module level meant importing this file
    # from a test runner picked up the runner's own arguments as the site URL, every request
    # then failed URL construction, and the retry backoff slept for real -- minutes per test.
    base = (base or (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE)).rstrip("/")
    for path in PAGES:
        code, _ = fetch(base + path)
        if code != 200:
            errors.append(f"{base}{path} returned {code}")
    if not errors:
        notes.append(f"{len(PAGES)} key pages return 200")

    code, _ = fetch(base + MUST_404)
    if code == 200:
        errors.append(
            f"{base}{MUST_404} is reachable — a full-resolution master is being published again"
        )
    else:
        notes.append("full-resolution masters are not published")

    code, _ = fetch(ARCHIVE)
    if code != 200:
        errors.append(f"the legacy archive reference no longer resolves ({code}) — {ARCHIVE}")
    else:
        notes.append("legacy archive still resolves")

    # CON-SEC-004: the headers a deployed project sends must be asserted against the
    # RUNNING site, not just present in a template. GitHub Pages cannot send real headers,
    # so what is assertable is the meta-tag policy -- and the gap is recorded in
    # docs/security.md rather than left implicit.
    code, body = fetch(base + "/")
    if code == 200:
        if b"Content-Security-Policy" not in body:
            errors.append("the live home page sends no Content-Security-Policy")
        elif b"script-src 'self'" not in body and b"script-src &#39;self&#39;" not in body:
            warnings.append("the live CSP no longer restricts script-src to 'self'")
        else:
            notes.append("live CSP present and script-src is restricted to 'self'")

    if code == 200 and b"_hu_" not in body:
        warnings.append("home page served no processed image variants — check the gallery rendered")

    for n in notes:
        print(f"ok:      {n}")
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR:   {e}")
    print(f"\nlive check of {base}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
