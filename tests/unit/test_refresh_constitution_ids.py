"""Unit tests for scripts/refresh-constitution-ids.py — the generator behind `make constitution-ids`.

This script writes the file every citation is checked against, so its failure modes matter
more than its success: a silently empty list would make all 26 citations dangle at once,
which reads as 26 broken citations rather than one broken parser (CON-VER-005).
"""

import os

import pytest
from conftest import load


@pytest.fixture
def rc():
    return load("refresh-constitution-ids")


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A writable repo root plus a mirror directory outside it."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    monkeypatch.chdir(repo)
    return repo, mirror


def point_at(rc, monkeypatch, mirror):
    monkeypatch.setattr(rc, "MIRROR_DIR", str(mirror))
    monkeypatch.setattr(rc, "MIRROR", str(mirror / "CONSTITUTION.md"))


class TestRefresh:
    def test_writes_the_ids_it_finds(self, rc, workspace, monkeypatch, capsys):
        repo, mirror = workspace
        (mirror / "CONSTITUTION.md").write_text(
            "# Constitution\n\n### CON-VER-001 · Gate on exit codes\n"
            "### CON-PROC-003 · Extend the layer\n",
            encoding="utf-8",
        )
        point_at(rc, monkeypatch, mirror)
        assert rc.main() == 0
        written = (repo / "docs" / "constitution-ids.txt").read_text(encoding="utf-8")
        assert "CON-VER-001" in written and "CON-PROC-003" in written

    def test_output_is_sorted_and_deduplicated(self, rc, workspace, monkeypatch):
        repo, mirror = workspace
        (mirror / "CONSTITUTION.md").write_text(
            "### CON-VER-002\n### CON-VER-001\n### CON-VER-002\n", encoding="utf-8"
        )
        point_at(rc, monkeypatch, mirror)
        rc.main()
        body = [
            l
            for l in (repo / "docs" / "constitution-ids.txt").read_text().splitlines()
            if l and not l.startswith("#")
        ]
        assert body == ["CON-VER-001", "CON-VER-002"]

    def test_the_header_records_where_it_came_from(self, rc, workspace, monkeypatch):
        """A snapshot with no provenance cannot be judged stale by a reader."""
        repo, mirror = workspace
        (mirror / "CONSTITUTION.md").write_text("### CON-VER-001\n", encoding="utf-8")
        point_at(rc, monkeypatch, mirror)
        rc.main()
        header = (repo / "docs" / "constitution-ids.txt").read_text()
        assert "Generated:" in header and "Refresh:" in header and "Mirror:" in header

    def test_a_missing_mirror_fails_without_writing(self, rc, workspace, monkeypatch):
        repo, mirror = workspace
        point_at(rc, monkeypatch, mirror)
        assert rc.main() == 1
        assert not (repo / "docs" / "constitution-ids.txt").exists()

    def test_an_unparseable_mirror_refuses_to_write_an_empty_list(
        self, rc, workspace, monkeypatch
    ):
        """The important one: if the heading format changes upstream, say so loudly rather
        than emptying the file and making every citation in the repo dangle."""
        repo, mirror = workspace
        (mirror / "CONSTITUTION.md").write_text(
            "A constitution whose headings no longer carry IDs.\n", encoding="utf-8"
        )
        point_at(rc, monkeypatch, mirror)
        assert rc.main() == 1
        assert not (repo / "docs" / "constitution-ids.txt").exists()

    def test_an_existing_list_survives_a_failed_refresh(self, rc, workspace, monkeypatch):
        repo, mirror = workspace
        out = repo / "docs" / "constitution-ids.txt"
        out.write_text("# existing\nCON-VER-001\n", encoding="utf-8")
        (mirror / "CONSTITUTION.md").write_text("no ids here\n", encoding="utf-8")
        point_at(rc, monkeypatch, mirror)
        assert rc.main() == 1
        assert "CON-VER-001" in out.read_text(encoding="utf-8")

    def test_git_metadata_degrades_to_unknown_rather_than_crashing(self, rc, workspace, monkeypatch):
        """The mirror is a git checkout in practice, but the generator must not require it."""
        repo, mirror = workspace
        (mirror / "CONSTITUTION.md").write_text("### CON-VER-001\n", encoding="utf-8")
        point_at(rc, monkeypatch, mirror)
        assert rc.main() == 0
        assert "unknown" in (repo / "docs" / "constitution-ids.txt").read_text()

    def test_creates_the_docs_directory_if_absent(self, rc, workspace, monkeypatch):
        repo, mirror = workspace
        os.rmdir(repo / "docs")
        (mirror / "CONSTITUTION.md").write_text("### CON-VER-001\n", encoding="utf-8")
        point_at(rc, monkeypatch, mirror)
        assert rc.main() == 0
        assert (repo / "docs" / "constitution-ids.txt").is_file()
