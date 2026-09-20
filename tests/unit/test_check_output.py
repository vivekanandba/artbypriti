"""Unit tests for scripts/check-output.py — assertions on the BUILT SITE."""

import sys
import pytest
from conftest import load, jpeg_bytes, png_bytes


@pytest.fixture
def co():
    return load("check-output")


class _Site:
    """A minimal built site: HTML pages plus derived image variants."""

    def __init__(self, root):
        self.root = root

    def add_page(self, rel, html):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        return p

    def add_variant(self, rel, width, height=600):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(jpeg_bytes(width, height))
        return p


@pytest.fixture
def site(tmp_path):
    root = tmp_path / "public"
    s = _Site(root)
    for rel in ("index.html", "about/index.html", "request/index.html"):
        s.add_page(rel, "<html></html>")
    for rel in ("sitemap.xml", "robots.txt"):
        (root / rel).write_text("x", encoding="utf-8")
    return s


class TestImageSize:
    def test_reads_jpeg_dimensions(self, co, tmp_path):
        f = tmp_path / "a.jpg"; f.write_bytes(jpeg_bytes(1600, 900))
        assert co.image_size(str(f)) == (1600, 900)

    def test_reads_png_dimensions(self, co, tmp_path):
        f = tmp_path / "a.png"; f.write_bytes(png_bytes(640, 480))
        assert co.image_size(str(f)) == (640, 480)

    def test_returns_none_for_a_non_image(self, co, tmp_path):
        f = tmp_path / "a.txt"; f.write_bytes(b"not an image at all, but long enough to read")
        assert co.image_size(str(f)) is None

    def test_returns_none_for_a_truncated_file(self, co, tmp_path):
        f = tmp_path / "a.jpg"; f.write_bytes(b"\xff\xd8")
        assert co.image_size(str(f)) is None

    def test_returns_none_when_absent(self, co, tmp_path):
        assert co.image_size(str(tmp_path / "ghost.jpg")) is None


class TestNoMasters:
    def test_published_master_is_an_error(self, co, site):
        site.add_variant("olive/Olive.jpg", 2500)          # no _hu_ marker => a master
        site.add_page("olive/index.html", "<html></html>")
        co.check_no_masters(str(site.root))
        assert any("master" in e for e in co.errors)

    def test_derived_variants_are_fine(self, co, site):
        site.add_variant("olive/Olive_hu_abc123.jpg", 600)
        site.add_page("olive/index.html", "<html></html>")
        co.check_no_masters(str(site.root))
        assert co.errors == []

    def test_static_favicons_are_not_flagged(self, co, site):
        """The first version of this check flagged static/images/favicon.png."""
        site.add_variant("images/favicon.png", 180)
        co.check_no_masters(str(site.root))
        assert co.errors == []


class TestPayloadBudget:
    def test_within_budget_passes(self, co, site):
        co.check_payload(str(site.root))
        assert co.errors == []
        assert any("payload" in n for n in co.notes)

    def test_over_budget_errors(self, co, site, monkeypatch):
        monkeypatch.setattr(co, "MAX_PAYLOAD_MB", 0)
        co.check_payload(str(site.root))
        assert any("exceeds" in e for e in co.errors)


class TestArtworkPages:
    def test_missing_page_is_an_error(self, co, site):
        co.check_artwork_pages(str(site.root), {"ghost": True})
        assert any("no built page" in e for e in co.errors)

    def test_page_without_an_image_is_an_error(self, co, site):
        site.add_page("olive/index.html", "<html><p>no pictures</p></html>")
        co.check_artwork_pages(str(site.root), {"olive": False})
        assert any("renders no image" in e for e in co.errors)

    def test_promised_caption_that_is_absent_is_an_error(self, co, site):
        site.add_page("olive/index.html", '<img data-src=/a.jpg>')
        co.check_artwork_pages(str(site.root), {"olive": True})
        assert any("renders no caption" in e for e in co.errors)

    def test_caption_present_passes(self, co, site):
        site.add_page("olive/index.html", '<img data-src=/a.jpg><div class=dimensions>(5 cm X 5 cm)</div>')
        co.check_artwork_pages(str(site.root), {"olive": True})
        assert co.errors == []

    def test_no_dimensions_in_front_matter_only_warns(self, co, site):
        site.add_page("olive/index.html", '<img data-src=/a.jpg>')
        co.check_artwork_pages(str(site.root), {"olive": False})
        assert co.errors == []
        assert any("no size caption" in w for w in co.warnings)


class TestExpectedFiles:
    def test_all_present_passes(self, co, site):
        co.check_expected_files(str(site.root))
        assert co.errors == []

    def test_missing_robots_is_an_error(self, co, site):
        (site.root / "robots.txt").unlink()
        co.check_expected_files(str(site.root))
        assert any("robots.txt" in e for e in co.errors)


class TestInternalLinks:
    def test_dead_internal_link_is_an_error(self, co, site):
        site.add_page("index.html", '<a href="/nowhere/">x</a>')
        co.check_internal_links(str(site.root))
        assert any("broken internal link" in e for e in co.errors)

    def test_external_and_anchor_links_are_skipped(self, co, site):
        site.add_page("index.html",
                      '<a href="https://example.com">x</a><a href="#top">y</a>'
                      '<a href="mailto:a@b.c">z</a><a href="data:,x">w</a>')
        co.check_internal_links(str(site.root))
        assert co.errors == []

    def test_directory_link_resolves_via_index_html(self, co, site):
        site.add_page("index.html", '<a href="/about/">x</a>')
        co.check_internal_links(str(site.root))
        assert co.errors == []

    def test_many_broken_links_are_summarised(self, co, site):
        links = "".join(f'<a href="/gone-{i}/">x</a>' for i in range(14))
        site.add_page("index.html", links)
        co.check_internal_links(str(site.root))
        assert any("more broken link" in e for e in co.errors)


class TestNoUpscaling:
    def test_grid_image_narrower_than_its_slot_is_an_error(self, co, site, content):
        content("olive", image="painting.jpg")           # master 800px wide
        site.add_variant("olive/p_hu_1.jpg", 434)
        site.add_page("index.html", '<img class=lazyload data-src=/olive/p_hu_1.jpg>')
        co.check_no_upscaling(str(site.root), str(content.root))
        assert any("upscaled by the browser" in e for e in co.errors)

    def test_grid_image_at_slot_width_passes(self, co, site, content):
        content("olive", image="painting.jpg")
        site.add_variant("olive/p_hu_1.jpg", 600)
        site.add_page("index.html", '<img class=lazyload data-src=/olive/p_hu_1.jpg>')
        co.check_no_upscaling(str(site.root), str(content.root))
        assert co.errors == []

    def test_small_master_warns_instead_of_failing(self, co, site, content):
        """Constitution III — no automation can conjure resolution never photographed."""
        d = content("tiny", image=None)
        (d / "tiny.jpg").write_bytes(jpeg_bytes(300, 400))
        site.add_variant("tiny/t_hu_1.jpg", 300)
        site.add_page("index.html", '<img class=lazyload data-src=/tiny/t_hu_1.jpg>')
        co.check_no_upscaling(str(site.root), str(content.root))
        assert co.errors == []
        assert any("master is smaller" in w for w in co.warnings)

    def test_artwork_page_image_is_exempt(self, co, site, content):
        """That figure shrink-wraps, so it has no fixed slot and can never be upscaled."""
        content("olive", image="painting.jpg")
        site.add_variant("olive/p_hu_1.jpg", 577)
        site.add_page("olive/index.html",
                      '<img class="lazyload gallery-single-img" data-src=/olive/p_hu_1.jpg>')
        co.check_no_upscaling(str(site.root), str(content.root))
        assert co.errors == []

    def test_images_without_data_src_are_skipped(self, co, site, content):
        content("olive")
        site.add_page("index.html", '<img class=lazyload src=/x.jpg>')
        co.check_no_upscaling(str(site.root), str(content.root))
        assert co.errors == []


class TestArtworksFromContent:
    def test_reports_whether_dimensions_are_promised(self, co, content):
        content("with-dims", dimensions="(5 cm X 5 cm)")
        content("without", dimensions="")
        content("about")
        out = co.artworks_from_content(str(content.root))
        assert out == {"with-dims": True, "without": False}   # about is excluded

    def test_missing_directory_yields_nothing(self, co, tmp_path):
        assert co.artworks_from_content(str(tmp_path / "ghost")) == {}


class TestMain:
    def _run(self, co, built, content_dir):
        argv = sys.argv
        sys.argv = ["check-output.py", str(built), "--content", str(content_dir)]
        try:
            return co.main()
        finally:
            sys.argv = argv

    def test_clean_site_returns_zero(self, co, site, content):
        content("olive", image="painting.jpg")
        site.add_variant("olive/p_hu_1.jpg", 600)
        site.add_page("olive/index.html",
                      '<img data-src=/olive/p_hu_1.jpg><div class=dimensions>(5 cm X 5 cm)</div>')
        assert self._run(co, site.root, content.root) == 0

    def test_missing_built_dir_returns_one(self, co, tmp_path, content, capsys):
        content("olive")
        assert self._run(co, tmp_path / "ghost", content.root) == 1
        assert "no built site" in capsys.readouterr().err

    def test_no_artworks_returns_one(self, co, site, tmp_path, capsys):
        empty = tmp_path / "empty"; empty.mkdir()
        assert self._run(co, site.root, empty) == 1
        assert "no artwork bundles" in capsys.readouterr().err


class TestImageHeaderEdgeCases:
    """The stdlib JPEG reader replaces Pillow, so its odd paths need exercising too."""

    def test_padded_ff_fill_bytes_are_skipped(self, co, tmp_path):
        """JPEG allows runs of 0xFF as padding before a marker."""
        f = tmp_path / "a.jpg"
        f.write_bytes(b"\xff\xd8" + b"\xff" * 6 + b"\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
                      + b"\xff\xc0\x00\x11\x08\x01\x2c\x01\x90\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01")
        assert co.image_size(str(f)) == (400, 300)

    def test_standalone_markers_are_skipped(self, co, tmp_path):
        f = tmp_path / "a.jpg"
        f.write_bytes(b"\xff\xd8" + b"\xff\xd0" + b"\xff\xd1"
                      + b"\xff\xc0\x00\x11\x08\x00\x64\x00\xc8\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01")
        assert co.image_size(str(f)) == (200, 100)

    def test_truncated_before_the_segment_length(self, co, tmp_path):
        f = tmp_path / "a.jpg"
        f.write_bytes(b"\xff\xd8" + b"\x00" * 22 + b"\xff\xe0")
        assert co.image_size(str(f)) is None

    def test_truncated_inside_the_frame_header(self, co, tmp_path):
        f = tmp_path / "a.jpg"
        f.write_bytes(b"\xff\xd8" + b"\x00" * 22 + b"\xff\xc0\x00\x11\x08\x01")
        assert co.image_size(str(f)) is None

    def test_stream_ending_without_a_frame_marker(self, co, tmp_path):
        f = tmp_path / "a.jpg"
        f.write_bytes(b"\xff\xd8" + b"\x00" * 30)
        assert co.image_size(str(f)) is None

    def test_unreadable_path_returns_none(self, co, tmp_path):
        d = tmp_path / "a-directory.jpg"; d.mkdir()
        assert co.image_size(str(d)) is None


class TestReporting:
    def test_warnings_and_errors_are_printed(self, co, site, content, capsys):
        """The operator only ever sees stdout; silence on a failure would be the worst bug."""
        import sys
        content("olive", image="painting.jpg", dimensions="")
        site.add_variant("olive/p_hu_1.jpg", 434)
        site.add_page("index.html", '<img class=lazyload data-src=/olive/p_hu_1.jpg>')
        site.add_page("olive/index.html", '<img data-src=/olive/p_hu_1.jpg>')
        argv = sys.argv
        sys.argv = ["check-output.py", str(site.root), "--content", str(content.root)]
        try:
            rc = co.main()
        finally:
            sys.argv = argv
        out = capsys.readouterr().out
        assert rc == 1
        assert "ERROR:" in out and "warning:" in out
