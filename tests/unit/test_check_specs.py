"""Unit tests for scripts/check-specs.py — spec hygiene and the spec-required gate."""

import subprocess
import sys
import pytest
from conftest import load


@pytest.fixture
def cs():
    return load("check-specs")


@pytest.fixture
def specs(tmp_path, monkeypatch):
    """A specs/ tree inside a real git repo, since the gate diffs against a base ref."""
    monkeypatch.chdir(tmp_path)
    run = lambda *a: subprocess.run(a, cwd=tmp_path, capture_output=True, text=True)
    # `git init -b main` needs git >= 2.28; this box has 2.25. Without this the repo was
    # never created, every git call failed silently, and the tests "passed" on empty diffs.
    run("git", "init", "-q")
    run("git", "symbolic-ref", "HEAD", "refs/heads/main")
    run("git", "config", "user.email", "t@example.com")
    run("git", "config", "user.name", "T")
    root = tmp_path / "specs"; root.mkdir()

    def write_registry(names):
        """specs/README.md as check_registry expects it: one linked row per feature."""
        rows = "\n".join(f"| [{n[:3]}](./{n}/) | {n} | Implemented | PR #1 |" for n in sorted(names))
        (root / "README.md").write_text(
            "# Specs\n\n| # | Feature | Status | Shipped as |\n| --- | --- | --- | --- |\n"
            + rows
            + "\n",
            encoding="utf-8",
        )

    created = set()

    def feature(name, *, spec=True, criteria=True, tokens=False, plan=False, tasks=False,
                registry=True):
        d = root / name; d.mkdir(parents=True, exist_ok=True)
        # A tree is only "clean" if the index matches it, so the fixture keeps them in step
        # unless a test is specifically exercising the drift.
        if registry:
            created.add(name)
        write_registry(created)
        if spec:
            body = [f"# Feature Specification: {name}", "", "## Requirements", "- FR-001: a thing"]
            if criteria: body += ["", "## Success Criteria", "- SC-001: it works"]
            if tokens: body += ["", "Title: [FEATURE NAME]"]
            (d / "spec.md").write_text("\n".join(body), encoding="utf-8")
        if plan: (d / "plan.md").write_text("# Plan", encoding="utf-8")
        if tasks: (d / "tasks.md").write_text("# Tasks", encoding="utf-8")
        return d

    feature.root, feature.run, feature.tmp = root, run, tmp_path
    feature.write_registry = write_registry
    return feature


def commit_all(specs, message="change"):
    specs.run("git", "add", "-A")
    specs.run("git", "commit", "-q", "-m", message)


class TestHygiene:
    def test_complete_spec_passes(self, cs, specs):
        specs("001-thing", plan=True, tasks=True)
        cs.check_hygiene()
        assert cs.errors == [] and cs.warnings == []

    def test_unfilled_template_token_is_an_error(self, cs, specs):
        specs("001-thing", tokens=True, plan=True, tasks=True)
        cs.check_hygiene()
        assert any("template token" in e for e in cs.errors)

    def test_token_quoted_in_prose_is_allowed(self, cs, specs):
        """A spec must be able to DISCUSS the tokens it checks for."""
        d = specs("001-thing", plan=True, tasks=True)
        (d / "spec.md").write_text(
            "# Feature Specification: x\n\nThe old file had 16 `[PLACEHOLDER]` tokens.\n"
            "```\n[FEATURE NAME]\n```\n\n## Success Criteria\n- SC-001: ok\n", encoding="utf-8")
        cs.check_hygiene()
        assert cs.errors == []

    def test_missing_success_criteria_is_an_error(self, cs, specs):
        specs("001-thing", criteria=False, plan=True, tasks=True)
        cs.check_hygiene()
        assert any("Success Criteria" in e for e in cs.errors)

    def test_missing_spec_file_is_an_error(self, cs, specs):
        specs("001-thing", spec=False)
        cs.check_hygiene()
        assert any("no spec.md" in e for e in cs.errors)

    def test_missing_plan_and_tasks_only_warn(self, cs, specs):
        specs("001-thing")
        cs.check_hygiene()
        assert cs.errors == []
        assert len([w for w in cs.warnings if "plan.md" in w or "tasks.md" in w]) == 2

    def test_absent_specs_directory_is_an_error(self, cs, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cs.check_hygiene()
        assert any("no specs" in e for e in cs.errors)

    def test_empty_specs_directory_is_an_error(self, cs, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "specs").mkdir()
        cs.check_hygiene()
        assert any("no feature directories" in e for e in cs.errors)


class TestSpecRequired:
    def _branch_with(self, specs, files, message="change"):
        specs("000-base", plan=True, tasks=True)
        commit_all(specs, "base")
        specs.run("git", "checkout", "-q", "-b", "feature")
        for rel, text in files.items():
            p = specs.tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        commit_all(specs, message)

    def test_substantive_change_without_intent_is_an_error(self, cs, specs):
        self._branch_with(specs, {"layouts/partials/x.html": "<div></div>"})
        cs.check_required("main")
        assert any("records no intent" in e for e in cs.errors)

    def test_substantive_change_with_a_spec_passes(self, cs, specs):
        self._branch_with(specs, {"layouts/partials/x.html": "<div></div>",
                                  "specs/001-new/spec.md": "# s\n## Success Criteria\n- ok"})
        cs.check_required("main")
        assert cs.errors == []

    def test_exemption_in_a_commit_message_passes(self, cs, specs):
        self._branch_with(specs, {"assets/css/x.css": "body{}"},
                          message="tweak\n\nNo-Spec: one-line CSS change")
        cs.check_required("main")
        assert cs.errors == []
        assert any("exemption" in n for n in cs.notes)

    def test_exemption_in_the_pr_body_passes(self, cs, specs, monkeypatch):
        self._branch_with(specs, {"assets/css/x.css": "body{}"})
        monkeypatch.setenv("PR_BODY", "Tidy up.\n\nNo-Spec: trivial\n")
        cs.check_required("main")
        assert cs.errors == []

    def test_content_only_change_needs_no_spec(self, cs, specs):
        self._branch_with(specs, {"content/olive/index.md": "---\ntitle: x\n---\n"})
        cs.check_required("main")
        assert cs.errors == []
        assert any("none substantive" in n for n in cs.notes)

    def test_docs_only_change_needs_no_spec(self, cs, specs):
        self._branch_with(specs, {"docs/notes.md": "hello", "README.md": "hi"})
        cs.check_required("main")
        assert cs.errors == []

    def test_no_changes_at_all_is_fine(self, cs, specs):
        specs("000-base", plan=True, tasks=True)
        commit_all(specs, "base")
        cs.check_required("main")
        assert cs.errors == []

    def test_many_touched_files_are_summarised(self, cs, specs):
        files = {f"scripts/s{i}.py": "x" for i in range(11)}
        self._branch_with(specs, files)
        cs.check_required("main")
        assert any("and 3 more" in e for e in cs.errors)


class TestRegistry:
    """specs/README.md drifted to 4 of 11 specs with nothing asserting otherwise. An index
    is only useful if something fails when it stops being complete (CON-PROC-011)."""

    def test_a_spec_missing_from_the_index_fails(self, cs, specs):
        specs("001-listed")
        specs("002-hidden", registry=False)   # on disk, never added to the table
        cs.check_registry()
        assert any("002-hidden/ exists but has no row" in e for e in cs.errors)

    def test_an_index_row_for_a_missing_spec_fails(self, cs, specs):
        specs("001-listed")
        specs.write_registry({"001-listed", "003-deleted"})
        cs.check_registry()
        assert any("lists 003-deleted/, which does not exist" in e for e in cs.errors)

    def test_a_complete_index_passes(self, cs, specs):
        specs("001-listed")
        specs("002-also-listed")
        cs.check_registry()
        assert cs.errors == []
        assert any("lists all 2 spec(s)" in n for n in cs.notes)

    def test_a_missing_readme_fails(self, cs, specs):
        specs("001-listed")
        (specs.root / "README.md").unlink()
        cs.check_registry()
        assert any("missing" in e for e in cs.errors)

    def test_non_numeric_directories_are_ignored(self, cs, specs):
        """`templates/` or a stray scratch directory is not a feature and needs no row."""
        specs("001-listed")
        (specs.root / "templates").mkdir()
        cs.check_registry()
        assert cs.errors == []


class TestHelpers:
    def test_exemption_regex_is_case_insensitive(self, cs):
        assert cs.EXEMPTION_RE.search("no-spec: because") is not None

    def test_run_survives_a_missing_binary(self, cs):
        assert cs.run("definitely-not-a-real-binary-xyz") == ""


class TestMain:
    def _run(self, cs, *args):
        argv = sys.argv
        sys.argv = ["check-specs.py", *args]
        try:
            return cs.main()
        finally:
            sys.argv = argv

    def test_clean_tree_returns_zero(self, cs, specs):
        specs("001-thing", plan=True, tasks=True)
        assert self._run(cs) == 0

    def test_unfilled_template_returns_one(self, cs, specs):
        specs("001-thing", tokens=True, plan=True, tasks=True)
        assert self._run(cs) == 1

    def test_diff_base_flag_engages_the_required_check(self, cs, specs):
        specs("000-base", plan=True, tasks=True)
        commit_all(specs, "base")
        specs.run("git", "checkout", "-q", "-b", "feature")
        (specs.tmp / "Makefile").write_text("all:\n\techo hi\n", encoding="utf-8")
        commit_all(specs, "touch the Makefile")
        assert self._run(cs, "--diff-base", "main") == 1


class TestReporting:
    def test_warnings_are_printed(self, cs, specs, capsys):
        specs("001-thing")            # no plan.md / tasks.md -> warnings
        argv = sys.argv
        sys.argv = ["check-specs.py"]
        try:
            cs.main()
        finally:
            sys.argv = argv
        assert "warning:" in capsys.readouterr().out
