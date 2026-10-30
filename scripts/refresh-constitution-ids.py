#!/usr/bin/env python3
"""Regenerate docs/constitution-ids.txt from the local constitution mirror.

Run via `make constitution-ids`. This is the ONLY thing that should write that file: it is a
vendored snapshot, and a hand-edit is indistinguishable from a rule that does not exist
(CON-PROC-007 -- automation proposes, humans dispose: this proposes a diff, it does not commit).

It deliberately does not run on a schedule. A rule landing upstream should be noticed by a
person deciding whether this repo's citations still mean what they said.
"""

import os
import re
import subprocess
import sys

MIRROR_DIR = os.path.expanduser("~/data-dash/.constitution-mirror")
MIRROR = os.path.join(MIRROR_DIR, "CONSTITUTION.md")
OUT = os.path.join("docs", "constitution-ids.txt")
DEFINITION_RE = re.compile(r"^#+\s*(CON-[A-Z]{3,5}-[0-9]{3})\b")

HEADER = """\
# Constitution rule IDs — VENDORED SNAPSHOT, generated. Do not hand-edit.
#
# Why this file exists: CI only gets this repository. It cannot read ~/.claude or
# ~/data-dash, so a checker that consults the real constitution cannot be a CI gate
# (CON-VER-004). The IDs are therefore vendored here and refreshed deliberately.
#
# Source:    vivekanandba/fleet (formerly constitution) — CONSTITUTION.md
# Mirror:    ~/data-dash/.constitution-mirror @ {commit} ({commit_date})
# Generated: {today}
# Refresh:   make constitution-ids
#
# This is a snapshot of what EXISTS, not of what this repo may cite: an ID this repo
# proposes but the constitution has not adopted belongs in constitution-ids-proposed.txt.
"""


def git(*args, default="unknown"):
    try:
        out = subprocess.run(
            ("git", "-C", MIRROR_DIR) + args, capture_output=True, text=True, check=False
        )
        return out.stdout.strip() or default
    except OSError:
        return default


def main():
    if not os.path.isfile(MIRROR):
        print(f"No constitution mirror at {MIRROR}", file=sys.stderr)
        return 1

    ids = set()
    with open(MIRROR, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = DEFINITION_RE.match(line.strip())
            if m:
                ids.add(m.group(1))

    if not ids:
        # Writing an empty list would make every citation in the repo dangle at once, which
        # reads as 26 broken citations rather than one broken parser (CON-VER-005).
        print(
            f"{MIRROR} yielded no rule IDs — refusing to write an empty list. "
            f"The heading format has probably changed.",
            file=sys.stderr,
        )
        return 1

    from datetime import date

    header = HEADER.format(
        commit=git("rev-parse", "--short", "HEAD"),
        commit_date=git("log", "-1", "--format=%cs"),
        today=date.today().isoformat(),
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(header)
        for ident in sorted(ids):
            fh.write(ident + "\n")

    print(f"wrote {OUT}: {len(ids)} rule ID(s) from mirror @ {git('rev-parse', '--short', 'HEAD')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
