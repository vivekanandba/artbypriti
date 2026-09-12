#!/usr/bin/env bash
#
# Repo-specific pre-commit checks for artbypriti.
#
# The house gates (secrets, protected branch, determinism, artifacts, commit messages) are
# tools/check_hygiene.py, installed by the house-gates skill. This holds only what is
# specific to this repository, and is deliberately NOT a second .githooks/pre-commit:
# that path belongs to the house installer, which prepends its block and preserves local
# edits below it.
#
# Wire it in after house-gates is installed, by appending this line below the marker:
#
#   "$root/scripts/check-local-gates.sh"
#
# Bypass: git commit --no-verify   (or HOUSE_GATES_SKIP=1 for the house block)
set -e
root="$(git rev-parse --show-toplevel)"
python3 "$root/scripts/check-specs.py"
