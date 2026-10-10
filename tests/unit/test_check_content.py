"""Unit tests for scripts/check-content.py — front-matter validation."""

import pytest
from conftest import load


@pytest.fixture
def cc():
    return load("check-content")


def run(cc, root, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return cc.main.__wrapped__() if hasattr(cc.main, "__wrapped__") else _main(cc, root)


def _main(cc, root):
    import sys
    argv = sys.argv
    sys.argv = ["check-content.py", str(root)]
    try:
        return cc.main()
    finally:
        sys.argv = argv


class TestFrontMatterParsing:
    def test_missing_front_matter_is_an_error(self, cc, tmp_path):
        (tmp_path / "x.md").write_text("no front matter here", encoding="utf-8")
        assert cc.split_front_matter("no front matter", "x.md") is None
        assert any("no YAML front matter" in e for e in cc.errors)

    def test_unterminated_front_matter_is_an_error(self, cc):
        assert cc.split_front_matter("---\ntitle: x\n", "x.md") is None
        assert any("not terminated" in e for e in cc.errors)

    def test_scalar_reads_and_strips_quotes(self, cc):
        block = '\ntitle: "Quoted"\nweight: 3\nempty:\n'
        assert cc.scalar(block, "title") == "Quoted"
        assert cc.scalar(block, "weight") == "3"
        assert cc.scalar(block, "empty") is None
        assert cc.scalar(block, "absent") is None

    def test_declared_resources_collects_every_src(self, cc):
        block = "\ntitle: x\nresources:\n  - src: a.jpg\n  - src: b.jpg\nother: y\n"
        assert cc.declared_resources(block) == ["a.jpg", "b.jpg"]

    def test_no_resources_block_returns_empty(self, cc):
        assert cc.declared_resources("\ntitle: x\n") == []


class TestBundleValidation:
    def test_clean_bundle_passes(self, cc, content):
        content("olive")
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert cc.errors == []

    def test_declared_file_that_is_absent_is_an_error(self, cc, content):
        content("olive", resource="wrong-name.jpg", image="painting.jpg")
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert any("wrong-name.jpg" in e and "not in the bundle" in e for e in cc.errors)

    def test_bundle_with_no_image_is_an_error(self, cc, content):
        content("olive", resource=None, image=None)
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert any("no image" in e for e in cc.errors)

    @pytest.mark.parametrize("field", ["title", "date", "categories"])
    def test_structural_fields_are_errors_when_missing(self, cc, content, field):
        kwargs = {field: ""} if field != "title" else {"title": ""}
        content("olive", **kwargs)
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert any(field in e for e in cc.errors), f"{field} should error"

    def test_missing_description_only_warns(self, cc, content):
        """Constitution III: only the artist can write this, so it must never block a deploy."""
        content("olive", description="")
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert cc.errors == []
        assert any("description" in w for w in cc.warnings)

    def test_missing_dimensions_only_warns(self, cc, content):
        content("olive", dimensions="")
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert cc.errors == []
        assert any("dimensions" in w for w in cc.warnings)

    def test_about_is_exempt_from_artwork_rules(self, cc, content):
        content("about", description="", dimensions="", categories="")
        cc.check_bundle(str(content.root / "about"), "about")
        assert cc.errors == []


class TestDimensionFormat:
    def test_unparenthesised_dimensions_error(self, cc, content):
        content("olive", dimensions="46 cm Diameter")
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert any("parentheses" in e for e in cc.errors)

    def test_lowercase_x_separator_errors(self, cc, content):
        content("olive", dimensions="(51 cm x 41 cm)")
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert any("lowercase" in e for e in cc.errors)

    def test_inches_warn_but_do_not_block(self, cc, content):
        """The artist may have chosen inches; automation must not convert them."""
        content("olive", dimensions='(12" Diameter)')
        cc.check_bundle(str(content.root / "olive"), "olive")
        assert cc.errors == []
        assert any("inches" in w for w in cc.warnings)


class TestBranchBundle:
    def test_home_resource_in_a_child_bundle_is_an_error(self, cc, content):
        """The home-cover bug: the file exists, but inside a child bundle, so it matches nothing."""
        content("staircase", image="staircase.jpg")
        (content.root / "_index.md").write_text(
            "---\ntitle: Home\nresources:\n  - src: staircase.jpg\n---\n", encoding="utf-8")
        cc.check_branch_bundle(str(content.root))
        assert any("staircase.jpg" in e and "branch bundle" in e for e in cc.errors)

    def test_home_resource_present_at_root_passes(self, cc, content):
        (content.root / "cover.jpg").write_bytes(b"\xff\xd8\xff\xd9")
        (content.root / "_index.md").write_text(
            "---\ntitle: Home\nresources:\n  - src: cover.jpg\n---\n", encoding="utf-8")
        cc.check_branch_bundle(str(content.root))
        assert cc.errors == []

    def test_absent_index_warns(self, cc, content):
        cc.check_branch_bundle(str(content.root))
        assert any("home page front matter" in w for w in cc.warnings)


class TestMain:
    def test_main_returns_zero_on_a_clean_tree(self, cc, content, capsys):
        content("olive")
        (content.root / "_index.md").write_text("---\ntitle: Home\n---\n", encoding="utf-8")
        assert _main(cc, content.root) == 0

    def test_main_returns_one_when_a_declaration_is_broken(self, cc, content):
        content("olive", resource="ghost.jpg")
        (content.root / "_index.md").write_text("---\ntitle: Home\n---\n", encoding="utf-8")
        assert _main(cc, content.root) == 1

    def test_main_errors_on_a_missing_directory(self, cc, tmp_path, capsys):
        assert _main(cc, tmp_path / "nope") == 1
        assert "no such directory" in capsys.readouterr().err


class TestReportingAndEdges:
    def test_warnings_are_printed(self, cc, content, capsys):
        content("olive", dimensions="")
        (content.root / "_index.md").write_text("---\ntitle: Home\n---\n", encoding="utf-8")
        _main(cc, content.root)
        assert "warning:" in capsys.readouterr().out

    def test_bundle_with_unterminated_front_matter_stops_cleanly(self, cc, content):
        d = content("olive")
        (d / "index.md").write_text("---\ntitle: x\n", encoding="utf-8")
        cc.check_bundle(str(d), "olive")
        assert any("not terminated" in e for e in cc.errors)

    def test_branch_bundle_with_unterminated_front_matter_stops_cleanly(self, cc, content):
        (content.root / "_index.md").write_text("---\ntitle: x\n", encoding="utf-8")
        cc.check_branch_bundle(str(content.root))
        assert any("not terminated" in e for e in cc.errors)
