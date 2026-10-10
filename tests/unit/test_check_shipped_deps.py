"""Unit tests for scripts/check-shipped-deps.py (CON-SEC-003)."""

import sys
import pytest
from conftest import load


@pytest.fixture
def cs():
    return load("check-shipped-deps")


class _Built:
    def __init__(self, root):
        self.root = root

    def page(self, rel, html):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")


@pytest.fixture
def built(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    b = _Built(root)
    b.page("index.html", "<html><head></head><body></body></html>")
    return b


def run(cs, root):
    argv = sys.argv
    sys.argv = ["check-shipped-deps.py", str(root)]
    try:
        return cs.main()
    finally:
        sys.argv = argv


def test_self_contained_site_passes(cs, built, capsys):
    assert run(cs, built.root) == 0
    assert "no external origins" in capsys.readouterr().out


def test_a_cdn_script_fails(cs, built):
    built.page("olive/index.html", '<script src="https://cdn.jsdelivr.net/npm/x"></script>')
    assert run(cs, built.root) == 1


def test_a_remote_webfont_fails(cs, built):
    built.page("a/index.html", '<link href="https://fonts.googleapis.com/css?family=X">')
    assert run(cs, built.root) == 1


def test_schema_org_and_namespaces_are_not_fetches(cs, built):
    """itemtype and XML namespaces are identifiers, not things the browser loads."""
    built.page("b/index.html",
               '<div itemtype="https://schema.org/ImageObject"></div>'
               '<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    assert run(cs, built.root) == 0


def test_own_domain_is_not_external(cs, built):
    built.page("c/index.html", '<link href="https://artbypriti.com/css/main.css">')
    assert run(cs, built.root) == 0


def test_missing_built_dir_errors(cs, tmp_path, capsys):
    assert run(cs, tmp_path / "ghost") == 1
    assert "no built site" in capsys.readouterr().err
