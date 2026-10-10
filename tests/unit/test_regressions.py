"""One named test per defect that has actually escaped in this project.

The suite's own acceptance criterion (spec 008): a test suite that cannot catch the bugs
that really happened is theatre. Each test below fails if its incident is reintroduced.
Cross-referenced with docs/incidents.md.
"""

import json
import re
from pathlib import Path

import pytest
from conftest import load, jpeg_bytes

ROOT = Path(__file__).resolve().parents[2]


class TestGateBugs:
    """Bugs in the gates themselves — the checks everything else trusts."""

    def test_favicons_are_not_mistaken_for_published_masters(self, tmp_path):
        """Incident: check-output.py flagged static/images/favicon.png as a master.

        A false positive in a blocking gate is as damaging as a miss: it teaches people the
        gate is noise. Static assets are copied verbatim by design.
        """
        co = load("check-output")
        built = tmp_path / "public"
        (built / "images").mkdir(parents=True)
        (built / "images" / "favicon.png").write_bytes(jpeg_bytes(180, 180))
        (built / "images" / "apple-touch-icon.png").write_bytes(jpeg_bytes(180, 180))
        co.check_no_masters(str(built))
        assert co.errors == [], "static assets must not be reported as published masters"

    def test_home_page_front_matter_is_validated(self, tmp_path, monkeypatch):
        """Incident: check-content.py walked content/*/index.md and never read content/_index.md.

        The home cover declared a file living inside a child bundle, matched nothing, and Hugo
        silently fell back — for ~15 months. The validator built to catch exactly that class
        could not see the file it lived in.
        """
        cc = load("check-content")
        content = tmp_path / "content"
        (content / "staircase").mkdir(parents=True)
        (content / "staircase" / "staircase.jpg").write_bytes(jpeg_bytes(800, 600))
        (content / "_index.md").write_text(
            "---\ntitle: Home\nresources:\n  - src: staircase.jpg\n---\n", encoding="utf-8")
        cc.check_branch_bundle(str(content))
        assert any("staircase.jpg" in e for e in cc.errors), \
            "a branch-bundle resource pointing into a child bundle must fail"

    def test_a_spec_may_quote_the_tokens_it_checks_for(self, tmp_path, monkeypatch):
        """Incident: check-specs.py failed BOTH real specs for mentioning [PLACEHOLDER] in prose.

        A checker that cannot tolerate being described is a checker nobody can document.
        """
        cs = load("check-specs")
        monkeypatch.chdir(tmp_path)
        d = tmp_path / "specs" / "001-x"; d.mkdir(parents=True)
        (d / "spec.md").write_text(
            "# Feature Specification: x\n\n"
            "The constitution carried 16 `[PLACEHOLDER]` tokens and a `[FEATURE NAME]` header.\n\n"
            "## Success Criteria\n- SC-001: fine\n", encoding="utf-8")
        (d / "plan.md").write_text("# p", encoding="utf-8")
        (d / "tasks.md").write_text("# t", encoding="utf-8")
        cs.check_hygiene()
        assert cs.errors == [], "tokens inside code spans are discussion, not an unfilled template"

    def test_artwork_pages_are_exempt_from_the_fixed_slot_rule(self, tmp_path):
        """Incident: the no-upscaling check assumed a 1000px slot on artwork pages.

        Measuring the rendered geometry showed that figure shrink-wraps, so displayed ==
        natural and the image is never stretched. The check as first written would have
        failed pages that were correct.
        """
        co = load("check-output")
        content = tmp_path / "content" / "olive"; content.mkdir(parents=True)
        (content / "p.jpg").write_bytes(jpeg_bytes(2000, 3000))
        built = tmp_path / "public" / "olive"; built.mkdir(parents=True)
        (built / "p_hu_1.jpg").write_bytes(jpeg_bytes(577, 1000))
        (built / "index.html").write_text(
            '<img class="lazyload gallery-single-img" data-src=/olive/p_hu_1.jpg>', encoding="utf-8")
        co.check_no_upscaling(str(tmp_path / "public"), str(tmp_path / "content"))
        assert co.errors == [], "the artwork page has no fixed slot; it cannot upscale"

    def test_visual_threshold_stays_at_zero(self):
        """Incident: Playwright's default threshold 0.2 let an obvious regression pass 7/7.

        Shifting the whole site background #f4efe0 -> #e8dcc0 computes to a per-pixel delta of
        ~193 against a tolerance of ~7043. The gate was measurably blind. Sensitivity must come
        from threshold 0; tolerance from maxDiffPixelRatio.
        """
        cfg = (ROOT / "playwright.config.js").read_text(encoding="utf-8")
        m = re.search(r"threshold:\s*([0-9.]+)", cfg)
        assert m, "playwright.config.js must state an explicit threshold"
        assert float(m.group(1)) == 0, \
            "threshold must be 0; any higher silently tolerates real colour regressions"
        assert re.search(r"maxDiffPixelRatio:\s*0?\.\d+", cfg), \
            "tolerance must come from maxDiffPixelRatio, not from threshold"


class TestSiteInvariants:
    """Invariants that previously regressed in the site itself."""

    def test_masters_are_still_unpublished_in_config(self):
        """116MB of originals shipped for months; the cascade is what stops it."""
        idx = (ROOT / "content" / "_index.md").read_text(encoding="utf-8")
        assert re.search(r"^\s*publishResources:\s*false", idx, re.M), \
            "content/_index.md must keep the publishResources cascade"

    def test_image_cache_is_pointed_somewhere_ci_can_persist(self):
        """CI set HUGO_CACHEDIR but persisted nothing; ~200s of work repeated every deploy."""
        toml = (ROOT / "hugo.toml").read_text(encoding="utf-8")
        assert "[caches.images]" in toml and ":cacheDir" in toml

    def test_deploy_workflow_gates_before_publishing(self):
        """A direct push to main once reached production with nothing validating it."""
        wf = (ROOT / ".github" / "workflows" / "hugo.yml").read_text(encoding="utf-8")
        assert "check-content.py" in wf, "deploy must validate before building"
        assert "check-output.py" in wf, "deploy must assert on the built site before uploading"
