#!/usr/bin/env python3
"""Every constitution rule this repo cites must actually exist.

The house style is to CITE a shared rule by ID rather than restate it, because copies drift
and citations do not. That only holds while the citations resolve -- and the rules live in
another repository that changes without this one being touched: the local mirror picked up
26 -> 35 rules unattended during a single session. A renumbered rule, a retired one, or a
typo (a letter O where a zero belongs) all read as authority and point at nothing.

Nothing checked them. The convention was an unenforced rule, which is the thing CON-PROC-011
exists to name.

Why a vendored list: CI only gets this repository, so a checker that reads ~/.claude or
~/data-dash cannot be a gate (CON-VER-004). docs/constitution-ids.txt is the snapshot, and
`make constitution-ids` refreshes it. When a mirror happens to be present the freshness is
reported as a WARNING, and when it is not, as SKIPPED -- never as "fine" (CON-VER-005,
CON-DATA-002: "could not determine" is not "no difference").

Usage:
  python3 scripts/check-citations.py [root]
Exit: 0 = clean (warnings allowed), 1 = errors found
"""

import os
import re
import sys

IDS_FILE = os.path.join("docs", "constitution-ids.txt")
PROPOSED_FILE = os.path.join("docs", "constitution-ids-proposed.txt")
MIRROR = os.path.expanduser("~/data-dash/.constitution-mirror/CONSTITUTION.md")

# Deliberately loose on the numeric part so a malformed-but-plausible ID is CAUGHT rather
# than skipped as unrecognised: an ID with a letter O where a zero belongs must fail, not
# pass unnoticed as something this regex does not recognise.
CITATION_RE = re.compile(r"\bCON-[A-Z]{3,5}-[A-Z0-9]{2,4}\b")

# Writing ABOUT a bad ID -- documenting this checker, or recording a typo that was fixed --
# must not be impossible, or the gate makes its own documentation unwritable and gets
# switched off. A line carrying this marker is skipped. It is per-line and visible in the
# diff, the same bargain as `No-Spec:` in check-specs.py: the escape hatch exists so the
# gate is never routed around, and using it leaves a trace someone can review.
SUPPRESS = "not-a-citation"
DEFINITION_RE = re.compile(r"^#+\s*(CON-[A-Z]{3,5}-[0-9]{3})\b")

SCAN_EXTS = (".md", ".py", ".yml", ".yaml", ".html", ".js", ".txt", ".toml", ".sh")
SKIP_DIRS = {
    ".git", "node_modules", "public", "resources", "test-results",
    "playwright-report", "__pycache__", ".claude",
    "themes",      # vendored upstream; not this repo's prose
}
# The two list files name every ID by construction and would match themselves.
SKIP_FILES = {IDS_FILE, PROPOSED_FILE}

errors = []
warnings = []
notes = []


def load_ids(path):
    """IDs from a vendored list, ignoring comments and blank lines."""
    out = set()
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            out.add(line.split()[0])
    return out


def load_proposed(path):
    """Proposed IDs mapped to their stated reason. A missing reason is an error."""
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split(None, 1)
            ident = parts[0]
            reason = parts[1].strip() if len(parts) > 1 else ""
            if not reason:
                errors.append(
                    f"{path}:{n}: {ident} is exempted with no reason recorded — "
                    f"the exemption costs a sentence, which is the point"
                )
            out[ident] = reason
    return out


def citations(root):
    """Every CON-* citation in the repo's own text, as {id: [locations]}."""
    found = {}
    for dp, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(SCAN_EXTS):
                continue
            path = os.path.join(dp, fn)
            rel = os.path.relpath(path, root)
            if rel.replace(os.sep, "/") in {p.replace(os.sep, "/") for p in SKIP_FILES}:
                continue
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for n, line in enumerate(fh, 1):
                        if SUPPRESS in line:
                            continue
                        for ident in CITATION_RE.findall(line):
                            found.setdefault(ident, []).append(f"{rel}:{n}")
            except OSError:
                continue
    return found


def check_freshness(vendored):
    """Compare the snapshot against a mirror IF one is present. Never an error.

    A difference here means the vendored list is stale, which is a local chore, not a reason
    to fail someone's PR -- and in CI there is no mirror at all, so the honest report is
    "skipped" rather than a green tick that checked nothing.
    """
    if not os.path.isfile(MIRROR):
        notes.append("vendored ID list freshness: SKIPPED (no local constitution mirror)")
        return
    live = set()
    with open(MIRROR, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = DEFINITION_RE.match(line.strip())
            if m:
                live.add(m.group(1))
    if not live:
        warnings.append(f"{MIRROR} defines no rule IDs — cannot judge freshness")
        return
    added, removed = sorted(live - vendored), sorted(vendored - live)
    if added or removed:
        bits = []
        if added:
            bits.append(f"{len(added)} new upstream ({', '.join(added[:5])})")
        if removed:
            bits.append(f"{len(removed)} gone upstream ({', '.join(removed[:5])})")
        warnings.append(
            "vendored ID list is stale: " + "; ".join(bits) + " — run `make constitution-ids`"
        )
    else:
        notes.append(f"vendored ID list matches the mirror ({len(live)} rules)")


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(root)

    vendored = load_ids(IDS_FILE)
    if not vendored:
        errors.append(f"{IDS_FILE}: missing or empty — nothing to check citations against")
        print_report()
        return 1
    proposed = load_proposed(PROPOSED_FILE)

    # A proposal that has since been adopted is a stale exemption, not a courtesy.
    for ident in sorted(set(proposed) & vendored):
        errors.append(
            f"{PROPOSED_FILE}: {ident} has been ADOPTED into the constitution — "
            f"remove the exemption so the citation stands on its own"
        )

    found = citations(".")
    dangling = sorted(i for i in found if i not in vendored and i not in proposed)
    for ident in dangling:
        where = ", ".join(found[ident][:4])
        more = f" (+{len(found[ident]) - 4} more)" if len(found[ident]) > 4 else ""
        errors.append(f"{ident} is cited but does not exist: {where}{more}")

    for ident in sorted(set(proposed) - set(found) - vendored):
        warnings.append(
            f"{PROPOSED_FILE}: {ident} is exempted but nothing cites it — "
            f"drop it, or an allowlist quietly becomes a blanket"
        )

    cited_proposed = sorted(i for i in found if i in proposed and i not in vendored)
    if cited_proposed:
        notes.append(
            f"{len(cited_proposed)} ID(s) cited as proposed, not as adopted: "
            + ", ".join(cited_proposed)
        )
    notes.append(
        f"{len(found)} distinct rule ID(s) cited, {len(vendored)} defined upstream"
    )
    check_freshness(vendored)

    print_report()
    return 1 if errors else 0


def print_report():
    for n in notes:
        print(f"ok:      {n}")
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR:   {e}")
    print(f"\ncitation check: {len(errors)} error(s), {len(warnings)} warning(s)")


if __name__ == "__main__":
    sys.exit(main())
