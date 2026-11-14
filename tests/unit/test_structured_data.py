"""Spec 023: artwork structured data, and the data-block exemption in the CSP check."""

import json

import pytest
from conftest import load, png_bytes  # noqa: F401  (png_bytes kept for parity with siblings)


@pytest.fixture
def co():
    return load("check-output")


@pytest.fixture
def built(tmp_path):
    root = tmp_path / "public"
    root.mkdir()

    def page(rel, html):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")

    def variant(rel):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"\xff\xd8\xff\xd9")

    page.variant, page.root = variant, root
    return page


CSP = "<meta http-equiv=Content-Security-Policy content=\"script-src 'self'\">"


class TestExecutableScriptTypes:
    """A JSON-LD data block is never executed, so script-src does not govern it. The exemption
    is HTML's exact line, not "anything with a type attribute"."""

    def test_no_type_is_executable(self, co):
        assert co.is_executable_script("<script>")

    @pytest.mark.parametrize("t", ["text/javascript", "module", "application/javascript", "TEXT/JAVASCRIPT"])
    def test_javascript_types_are_executable(self, co, t):
        assert co.is_executable_script(f'<script type="{t}">')

    def test_unquoted_minified_javascript_type_is_executable(self, co):
        assert co.is_executable_script("<script type=text/javascript>")

    @pytest.mark.parametrize("tag", ['<script type="application/ld+json">', "<script type=application/ld+json>"])
    def test_json_ld_is_a_data_block(self, co, tag):
        assert not co.is_executable_script(tag)

    def test_json_ld_under_strict_csp_passes(self, co, built):
        built("index.html", CSP + '<script type=application/ld+json>{"@type":"VisualArtwork"}</script>')
        co.check_csp_matches_the_markup(str(built.root))
        assert co.errors == []

    def test_typed_inline_javascript_under_strict_csp_still_fails(self, co, built):
        """The reason the types are listed exactly: this must not slip through as "has a type"."""
        built("index.html", CSP + "<script type=text/javascript>alert(1)</script>")
        co.check_csp_matches_the_markup(str(built.root))
        assert any("inline <script>" in e for e in co.errors)


class TestArtworkStructuredData:
    GOOD = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": "Olive",
        "creator": {"@type": "Person", "name": "Priti Ghatlia"},
        "image": "https://artbypriti.com/olive/Olive_hu_1.jpg",
    }

    def _page(self, built, *blocks):
        body = "".join(
            f"<script type=application/ld+json>{json.dumps(b) if isinstance(b, dict) else b}</script>"
            for b in blocks
        )
        built("olive/index.html", f"<html><head>{body}</head></html>")

    def _check(self, co, built):
        co.check_artwork_structured_data(str(built.root), {"olive": True})

    def test_valid_block_passes(self, co, built):
        built.variant("olive/Olive_hu_1.jpg")
        self._page(built, self.GOOD)
        self._check(co, built)
        assert co.errors == []
        assert any("valid VisualArtwork" in n for n in co.notes)

    def test_missing_block_fails(self, co, built):
        built("olive/index.html", "<html></html>")
        self._check(co, built)
        assert any("0 JSON-LD block(s)" in e for e in co.errors)

    def test_two_blocks_fail(self, co, built):
        built.variant("olive/Olive_hu_1.jpg")
        self._page(built, self.GOOD, self.GOOD)
        self._check(co, built)
        assert any("2 JSON-LD block(s)" in e for e in co.errors)

    def test_unparseable_json_fails(self, co, built):
        self._page(built, "{not json")
        self._check(co, built)
        assert any("does not parse" in e for e in co.errors)

    def test_a_creation_date_the_site_does_not_know_fails(self, co, built):
        """CON-DATA-006: front-matter dates are post dates; stating one as dateCreated invents a fact."""
        built.variant("olive/Olive_hu_1.jpg")
        self._page(built, dict(self.GOOD, dateCreated="2021-02-13"))
        self._check(co, built)
        assert any("dateCreated" in e for e in co.errors)

    def test_missing_creator_fails(self, co, built):
        built.variant("olive/Olive_hu_1.jpg")
        self._page(built, {k: v for k, v in self.GOOD.items() if k != "creator"})
        self._check(co, built)
        assert any("no creator" in e for e in co.errors)

    def test_master_image_fails(self, co, built):
        self._page(built, dict(self.GOOD, image="https://artbypriti.com/olive/Olive.jpg"))
        self._check(co, built)
        assert any("not a derived variant" in e for e in co.errors)

    def test_image_absent_from_the_build_fails(self, co, built):
        self._page(built, self.GOOD)
        self._check(co, built)
        assert any("not in the built site" in e for e in co.errors)

    def test_wrong_type_fails(self, co, built):
        built.variant("olive/Olive_hu_1.jpg")
        self._page(built, dict(self.GOOD, **{"@type": "Product"}))
        self._check(co, built)
        assert any("not VisualArtwork" in e for e in co.errors)

    def test_more_than_five_problems_are_summarised(self, co, built):
        artworks = {}
        for i in range(7):
            built(f"a{i}/index.html", "<html></html>")
            artworks[f"a{i}"] = True
        co.check_artwork_structured_data(str(built.root), artworks)
        assert any("and 2 more" in e for e in co.errors)
