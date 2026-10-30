#!/usr/bin/env python3
"""Enforce spec-first: a substantive change must carry recorded intent.

Two independent checks:

  hygiene   — every specs/NNN-*/ has a real spec.md: no leftover template tokens, and
              success criteria present. An unfilled template is not a spec. This repo
              carried a 16-placeholder constitution for 15 months while advertising a
              process it did not follow.

  required  — a pull request touching substantive paths must either change something under
              specs/ or record `No-Spec: <reason>`. The escape hatch is deliberate: a gate
              with no way out gets routed around, and a routed-around gate protects nothing
              (Constitution, Development Workflow).

Usage:
  python3 scripts/check-specs.py                      # hygiene only
  python3 scripts/check-specs.py --diff-base <ref>    # hygiene + required
Exit: 0 = clean (warnings allowed), 1 = errors found

What this deliberately does NOT check: whether a spec is any *good*, or whether a change
left behind a gate that genuinely covers it. Neither is machine-checkable, and a check that
pretends otherwise measures compliance instead of coverage. See the "Honest limits" section
of specs/002-spec-process/spec.md.
"""

import os
import re
import subprocess
import sys

SPECS_DIR = "specs"

# Editing any of these can change what visitors see or how the site is built, so the intent
# behind the change is worth recording. Content edits, docs, and the specs themselves are not
# listed: a typo fix must never require a specification.
SUBSTANTIVE = (
    "layouts/",
    "assets/",
    "themes/",
    "scripts/",
    "tests/",
    ".github/workflows/",
    "archetypes/",
    "hugo.toml",
    "Makefile",
    "package.json",
    "package-lock.json",
    "playwright.config.js",
)

TEMPLATE_TOKENS = (
    "[PLACEHOLDER]",
    "[FEATURE NAME]",
    "[FEATURE]",
    "[###-feature-name]",
    "[PROJECT_NAME]",
    "[PRINCIPLE_1_NAME]",
    "NEEDS CLARIFICATION",
    "[DATE]",
)

EXEMPTION_RE = re.compile(r"^\s*No-Spec:\s*(\S.*)$", re.MULTILINE | re.IGNORECASE)

errors = []
warnings = []
notes = []


def run(*cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return out.stdout
    except OSError:
        return ""


def check_hygiene():
    if not os.path.isdir(SPECS_DIR):
        errors.append(f"no {SPECS_DIR}/ directory — run /speckit-specify to create a feature spec")
        return

    features = sorted(
        d for d in os.listdir(SPECS_DIR) if os.path.isdir(os.path.join(SPECS_DIR, d))
    )
    if not features:
        errors.append(f"{SPECS_DIR}/ contains no feature directories")
        return

    for feat in features:
        base = os.path.join(SPECS_DIR, feat)
        spec = os.path.join(base, "spec.md")

        if not os.path.isfile(spec):
            errors.append(f"{base}/: no spec.md")
            continue

        text = open(spec, encoding="utf-8").read()

        # Strip fenced blocks and inline code before scanning. A spec may legitimately
        # *discuss* these tokens — "the constitution carried 16 `[PLACEHOLDER]` tokens" is a
        # statement about history, not an unfilled field. Unfilled templates carry them bare,
        # as in "# Feature Specification: [FEATURE NAME]".
        prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        prose = re.sub(r"`[^`\n]*`", "", prose)

        for token in TEMPLATE_TOKENS:
            if token in prose:
                errors.append(
                    f"{spec}: still contains the template token {token!r} — "
                    f"an unfilled template is not a spec"
                )
                break

        if not re.search(r"^##+\s*.*Success Criteria", text, re.MULTILINE | re.IGNORECASE):
            errors.append(
                f"{spec}: no 'Success Criteria' section — state how you would know it worked "
                f"before implementing, not after"
            )

        for companion in ("plan.md", "tasks.md"):
            if not os.path.isfile(os.path.join(base, companion)):
                warnings.append(f"{base}/: no {companion} (expected for implemented work)")

    notes.append(f"{len(features)} feature spec(s) checked: {', '.join(features)}")


def check_registry():
    """specs/README.md must list every spec, and only specs that exist.

    The registry is a document whose entire purpose is completeness, and nothing asserted it
    was complete: it listed 4 of 11 specs when this check was written, having drifted silently
    for seven features. An index that quietly omits most of its contents is worse than no
    index, because it is read as authoritative (CON-PROC-011: a rule with no enforcing
    mechanism is a wish).
    """
    readme = os.path.join(SPECS_DIR, "README.md")
    if not os.path.isfile(readme):
        errors.append(f"{readme}: missing — the spec registry is where features are indexed")
        return

    text = open(readme, encoding="utf-8").read()
    on_disk = {
        d
        for d in os.listdir(SPECS_DIR)
        if os.path.isdir(os.path.join(SPECS_DIR, d)) and re.match(r"^\d{3}-", d)
    }
    # Rows link to the directory: [000](./000-backend-optimization/)
    listed = set(re.findall(r"\]\(\./(\d{3}-[^/)]+)/?\)", text))

    for missing in sorted(on_disk - listed):
        errors.append(
            f"{readme}: {missing}/ exists but has no row — every spec is listed, or the index lies"
        )
    for phantom in sorted(listed - on_disk):
        errors.append(f"{readme}: lists {phantom}/, which does not exist")

    if on_disk and on_disk == listed:
        notes.append(f"spec registry lists all {len(on_disk)} spec(s)")


def changed_files(base_ref):
    """Files changed relative to the merge base with base_ref."""
    merge_base = run("git", "merge-base", base_ref, "HEAD").strip()
    ref = merge_base or base_ref
    out = run("git", "diff", "--name-only", f"{ref}...HEAD")
    return [f for f in out.splitlines() if f.strip()]


def exemption_reason(base_ref):
    """An exemption may be recorded in any commit on the branch, or in the PR body."""
    merge_base = run("git", "merge-base", base_ref, "HEAD").strip() or base_ref
    log = run("git", "log", "--format=%B", f"{merge_base}..HEAD")
    for source in (log, os.environ.get("PR_BODY", "")):
        m = EXEMPTION_RE.search(source or "")
        if m:
            return m.group(1).strip()
    return None


def check_required(base_ref):
    files = changed_files(base_ref)
    if not files:
        notes.append(f"no changes against {base_ref} — nothing to require a spec for")
        return

    touched = sorted({f for f in files if f.startswith(SUBSTANTIVE)})
    if not touched:
        notes.append(
            f"{len(files)} changed file(s), none substantive — no spec required "
            f"(content and docs edits are exempt by design)"
        )
        return

    if any(f.startswith(SPECS_DIR + "/") for f in files):
        specs_touched = sorted({f for f in files if f.startswith(SPECS_DIR + "/")})
        notes.append(f"substantive change accompanied by {len(specs_touched)} spec file(s)")
        return

    reason = exemption_reason(base_ref)
    if reason:
        notes.append(f"substantive change with recorded exemption — No-Spec: {reason}")
        return

    shown = "\n".join(f"           - {f}" for f in touched[:8])
    more = f"\n           ...and {len(touched) - 8} more" if len(touched) > 8 else ""
    errors.append(
        "this change touches substantive paths but records no intent:\n"
        f"{shown}{more}\n"
        "         Either:\n"
        "           1. add or update a spec under specs/  (/speckit-specify), or\n"
        "           2. record `No-Spec: <reason>` in a commit message or the PR body\n"
        "         Option 2 is legitimate for small changes — the reason just has to be written down."
    )


def main():
    base_ref = None
    if "--diff-base" in sys.argv:
        idx = sys.argv.index("--diff-base")
        if idx + 1 < len(sys.argv):
            base_ref = sys.argv[idx + 1]

    check_hygiene()
    check_registry()
    if base_ref:
        check_required(base_ref)

    for n in notes:
        print(f"ok:      {n}")
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR:   {e}")

    print(f"\nspec checks: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
