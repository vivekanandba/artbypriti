"""Unit tests for scripts/check-live.py — the deployed HTTP contract.

Every test mocks the network. A health check that hits the real site from a unit suite
would be slow, flaky, and would fail for reasons that have nothing to do with the code.
"""

import sys
import urllib.error
import pytest
from conftest import load


@pytest.fixture
def cl():
    return load("check-live")


class FakeResponse:
    def __init__(self, status, body=b""):
        self.status, self._body = status, body
    def read(self):
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def routes(mapping, default=200, body=b"<img src=/x_hu_1.jpg>"):
    """Build a urlopen stand-in that answers from a {url-substring: status} map."""
    def fake(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        for key, status in mapping.items():
            if key in url:
                if status >= 400:
                    raise urllib.error.HTTPError(url, status, "err", {}, None)
                return FakeResponse(status, body)
        if default >= 400:
            raise urllib.error.HTTPError(url, default, "err", {}, None)
        return FakeResponse(default, body)
    return fake


class TestFetch:
    def test_returns_status_and_body(self, cl, monkeypatch):
        monkeypatch.setattr(cl.urllib.request, "urlopen", routes({}, 200, b"hello"))
        assert cl.fetch("https://x/") == (200, b"hello")

    def test_http_error_is_returned_as_its_code_not_raised(self, cl, monkeypatch):
        monkeypatch.setattr(cl.urllib.request, "urlopen", routes({}, 404))
        assert cl.fetch("https://x/")[0] == 404

    def test_network_failure_retries_then_reports_none(self, cl, monkeypatch):
        calls = []
        def boom(req, timeout=None):
            calls.append(1); raise OSError("no route to host")
        monkeypatch.setattr(cl.urllib.request, "urlopen", boom)
        monkeypatch.setattr(cl.time, "sleep", lambda s: None)   # don't actually wait
        status, _ = cl.fetch("https://x/", tries=3)
        assert status is None
        assert len(calls) == 3, "must retry before crying wolf (NFR-002)"


class TestMain:
    def _run(self, cl, base="https://example.test"):
        argv = sys.argv
        sys.argv = ["check-live.py", base]
        try:
            return cl.main()
        finally:
            sys.argv = argv

    def test_healthy_site_returns_zero(self, cl, monkeypatch, capsys):
        monkeypatch.setattr(cl.urllib.request, "urlopen",
                            routes({cl.MUST_404: 404}, 200))
        assert self._run(cl) == 0
        out = capsys.readouterr().out
        assert "key pages return 200" in out
        assert "masters are not published" in out

    def test_a_dead_page_fails(self, cl, monkeypatch):
        monkeypatch.setattr(cl.urllib.request, "urlopen",
                            routes({"/about/": 500, cl.MUST_404: 404}, 200))
        assert self._run(cl) == 1
        assert any("/about/" in e for e in cl.errors)

    def test_a_reachable_master_fails(self, cl, monkeypatch):
        """If publishResources regresses, an 8MB original becomes downloadable again."""
        monkeypatch.setattr(cl.urllib.request, "urlopen", routes({}, 200))
        assert self._run(cl) == 1
        assert any("master is being published" in e for e in cl.errors)

    def test_a_broken_archive_reference_fails(self, cl, monkeypatch):
        monkeypatch.setattr(cl.urllib.request, "urlopen",
                            routes({"github.com": 404, cl.MUST_404: 404}, 200))
        assert self._run(cl) == 1
        assert any("archive" in e for e in cl.errors)

    def test_home_without_processed_variants_warns(self, cl, monkeypatch):
        monkeypatch.setattr(cl.urllib.request, "urlopen",
                            routes({cl.MUST_404: 404}, 200, body=b"<html>no images</html>"))
        assert self._run(cl) == 0
        assert any("no processed image variants" in w for w in cl.warnings)
