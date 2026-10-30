"""Unit tests for scripts/check-citations.py — do the cited rule IDs actually exist?

The gate's whole value is telling three things apart that look identical in prose: a rule
that exists, a rule this repo has only proposed, and a typo. Each has its own test here.
"""

import sys

import pytest
from conftest import load


@pytest.fixture
def cc():
    return load("check-citations")


@pytest.fixture
def mirror_dir(tmp_path_factory):
    """Somewhere OUTSIDE the scanned repo. A constitution file inside it would have its own
    rule DEFINITIONS read as citations -- which is exactly what happened the first time."""
    return tmp_path_factory.mktemp("mirror")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A miniature repo: docs/ with the two list files, plus files that cite IDs."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()

    def build(*, defined=("CON-VER-001", "CON-PROC-003"), proposed=(), cites=""):
        (tmp_path / "docs" / "constitution-ids.txt").write_text(
            "# header\n" + "\n".join(defined) + ("\n" if defined else ""), encoding="utf-8"
        )
        (tmp_path / "docs" / "constitution-ids-proposed.txt").write_text(
            "# header\n" + "\n".join(proposed) + ("\n" if proposed else ""), encoding="utf-8"
        )
        (tmp_path / "NOTES.md").write_text(cites, encoding="utf-8")
        return tmp_path

    build.root = tmp_path
    return build


def run(cc, monkeypatch, *, mirror=None):
    """Run main() with the mirror pointed somewhere predictable, not at the real machine.

    sys.argv is set explicitly: main() reads argv[1] as the root to scan, and under pytest
    that slot holds the test file's path. The same shape of bug once made check-live.py hang
    for 300s in this suite.
    """
    monkeypatch.setattr(cc, "MIRROR", mirror or "/nonexistent/CONSTITUTION.md")
    monkeypatch.setattr(sys, "argv", ["check-citations.py"])
    return cc.main()


class TestDanglingCitations:
    def test_a_citation_to_a_nonexistent_rule_fails(self, cc, repo, monkeypatch):
        repo(cites="We follow CON-VER-404 here.\n")  # not-a-citation (test fixture, not a claim about a real rule)
        assert run(cc, monkeypatch) == 1
        assert any("CON-VER-404 is cited but does not exist" in e for e in cc.errors)  # not-a-citation (test fixture, not a claim about a real rule)

    def test_the_failure_names_file_and_line(self, cc, repo, monkeypatch):
        repo(cites="line one\nline two cites CON-VER-404\n")  # not-a-citation (test fixture, not a claim about a real rule)
        run(cc, monkeypatch)
        assert any("NOTES.md:2" in e for e in cc.errors)

    def test_resolving_citations_pass(self, cc, repo, monkeypatch):
        repo(cites="See CON-VER-001 and CON-PROC-003.\n")
        assert run(cc, monkeypatch) == 0
        assert cc.errors == []

    def test_a_letter_o_typo_is_caught_not_ignored(self, cc, repo, monkeypatch):
        """The regex is loose on the numeric part on purpose: a plausible-looking typo must
        fail rather than slip past as something the pattern does not recognise."""
        repo(cites="As required by CON-VER-O01.\n")  # not-a-citation (test fixture, not a claim about a real rule)
        assert run(cc, monkeypatch) == 1
        assert any("CON-VER-O01" in e for e in cc.errors)  # not-a-citation (test fixture, not a claim about a real rule)

    def test_a_suppressed_line_is_skipped(self, cc, repo, monkeypatch):
        repo(cites="An example of a bad id, CON-VER-404, not-a-citation\n")
        assert run(cc, monkeypatch) == 0

    def test_the_list_files_do_not_cite_themselves(self, cc, repo, monkeypatch):
        """Both files name every ID by construction; scanning them would be circular."""
        repo(defined=("CON-VER-001",), cites="nothing here\n")
        assert run(cc, monkeypatch) == 0


class TestProposedIds:
    def test_a_proposed_id_passes_and_is_reported_as_proposed(self, cc, repo, monkeypatch):
        repo(proposed=("CON-DATA-006  because we proposed it upstream",),
             cites="We proposed CON-DATA-006.\n")
        assert run(cc, monkeypatch) == 0
        assert any("cited as proposed, not as adopted" in n for n in cc.notes)

    def test_a_proposed_id_that_was_adopted_fails(self, cc, repo, monkeypatch):
        """A stale exemption silently downgrades a real rule to a maybe."""
        repo(defined=("CON-VER-001", "CON-PROC-003"),
             proposed=("CON-PROC-003  stale: this was adopted months ago",),
             cites="See CON-PROC-003.\n")
        assert run(cc, monkeypatch) == 1
        assert any("has been ADOPTED" in e for e in cc.errors)

    def test_an_exemption_without_a_reason_fails(self, cc, repo, monkeypatch):
        repo(proposed=("CON-DATA-006",), cites="We proposed CON-DATA-006.\n")
        assert run(cc, monkeypatch) == 1
        assert any("no reason recorded" in e for e in cc.errors)

    def test_an_exemption_nothing_cites_warns(self, cc, repo, monkeypatch):
        """A dead exemption is how an allowlist quietly becomes a blanket."""
        repo(proposed=("CON-DATA-006  proposed, but no longer referenced",), cites="nothing\n")
        assert run(cc, monkeypatch) == 0
        assert any("nothing cites it" in w for w in cc.warnings)


class TestFreshness:
    def test_absent_mirror_reports_skipped_not_ok(self, cc, repo, monkeypatch):
        """CON-VER-005 / CON-DATA-002: 'could not determine' is not 'no difference'."""
        repo(cites="See CON-VER-001.\n")
        run(cc, monkeypatch)
        assert any("SKIPPED" in n for n in cc.notes)
        assert not any("matches the mirror" in n for n in cc.notes)

    def test_a_stale_vendored_list_warns_but_does_not_fail(self, cc, repo, monkeypatch, mirror_dir):
        mirror = mirror_dir / "CONSTITUTION.md"
        mirror.write_text("### CON-VER-001\n### CON-PROC-003\n### CON-NEW-001\n", encoding="utf-8")  # not-a-citation (test fixture, not a claim about a real rule)
        repo(cites="See CON-VER-001.\n")
        assert run(cc, monkeypatch, mirror=str(mirror)) == 0
        assert any("stale" in w and "CON-NEW-001" in w for w in cc.warnings)  # not-a-citation (test fixture, not a claim about a real rule)

    def test_a_matching_mirror_reports_a_match(self, cc, repo, monkeypatch, mirror_dir):
        mirror = mirror_dir / "CONSTITUTION.md"
        mirror.write_text("### CON-VER-001\n### CON-PROC-003\n", encoding="utf-8")
        repo(cites="See CON-VER-001.\n")
        assert run(cc, monkeypatch, mirror=str(mirror)) == 0
        assert any("matches the mirror" in n for n in cc.notes)

    def test_a_mirror_defining_nothing_warns_rather_than_claiming_drift(
        self, cc, repo, monkeypatch, mirror_dir
    ):
        """An unparseable mirror means the check failed, not that 35 rules vanished."""
        mirror = mirror_dir / "CONSTITUTION.md"
        mirror.write_text("# A constitution with a changed heading format\n", encoding="utf-8")
        repo(cites="See CON-VER-001.\n")
        assert run(cc, monkeypatch, mirror=str(mirror)) == 0
        assert any("cannot judge freshness" in w for w in cc.warnings)


class TestMissingVendoredList:
    def test_a_missing_list_fails_rather_than_passing_vacuously(self, cc, repo, monkeypatch):
        """With no list, every citation is unverifiable — that must not read as success."""
        repo(cites="See CON-VER-001.\n")
        (repo.root / "docs" / "constitution-ids.txt").unlink()
        assert run(cc, monkeypatch) == 1
        assert any("nothing to check citations against" in e for e in cc.errors)
