"""Contract tests: the toolchain is pinned once, and the pins agree (spec 019).

CON-VER-010: a check whose result depends on its environment runs on a named, versioned image,
every job that checks the same artefact uses the same one, and a test asserts the image tag and
the lockfile agree. Screenshots are only comparable when the browser is identical, so a
Playwright image that drifts from the installed @playwright/test is a baseline defect waiting to
happen -- and, per the rule's own incidents, one that a tolerance absorbs silently.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def makefile_var(name):
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    m = re.search(rf"^{name}\s*:?=\s*(.+)$", text, re.MULTILINE)
    assert m, f"Makefile does not define {name}"
    return m.group(1).strip()


class TestPlaywrightPin:
    def test_image_tag_matches_the_lockfile(self):
        image = makefile_var("PLAYWRIGHT_IMAGE")
        m = re.search(r"playwright:v(\d+\.\d+\.\d+)-", image)
        assert m, f"PLAYWRIGHT_IMAGE is not a versioned tag: {image}"
        lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
        resolved = lock["packages"]["node_modules/@playwright/test"]["version"]
        assert m.group(1) == resolved, (
            f"container is Playwright {m.group(1)} but the lockfile resolved {resolved} -- "
            f"screenshots would be taken by a different browser than the one installed"
        )

    def test_package_json_pins_an_exact_version(self):
        """A range (^1.54) resolved to 1.62 in one repo and 1.61 in another (fleet CLAUDE.md)."""
        pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        spec = pkg["devDependencies"]["@playwright/test"]
        assert re.fullmatch(r"\d+\.\d+\.\d+", spec), f"@playwright/test is a range: {spec}"


class TestPinsLiveInOnePlace:
    """Two copies of a version are a drift waiting to happen. CI calls the Makefile instead."""

    PINNED = ("koalaman/shellcheck:", "bandit==", "mcr.microsoft.com/playwright:")

    def test_no_workflow_restates_a_pinned_tool(self):
        offenders = []
        for wf in sorted(WORKFLOWS.glob("*.yml")):
            for n, line in enumerate(wf.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                if any(pin in line for pin in self.PINNED):
                    offenders.append(f"{wf.name}:{n}: {line.strip()}")
        assert offenders == [], "pin these in the Makefile and call make:\n" + "\n".join(offenders)

    def test_ci_runs_the_same_lint_command_a_developer_runs(self):
        text = (WORKFLOWS / "pr-check.yml").read_text(encoding="utf-8")
        assert re.search(r"^\s*run:\s*make lint\s*$", text, re.MULTILINE), (
            "pr-check.yml should run `make lint`, not its own copy of the linters"
        )


class TestVendoredFilesAreNotStyleLinted:
    def test_hooks_are_excluded_from_shellcheck(self):
        """CON-COV-004: .githooks/* carry a vendored house-gates block, linted once upstream.
        Style-linting them here makes the next re-vendoring a red build nobody here can fix."""
        assert ".githooks" not in makefile_var("SHELL_FILES")

    def test_this_repos_own_shell_is_still_linted(self):
        assert "scripts/" in makefile_var("SHELL_FILES")


class TestOneBuildPath:
    """CON-COV-005: when two code paths build the same artifact, test the one that ships.

    The deploy ran its own `hugo --minify --baseURL ...` while every browser test ran on
    `make build`, so 30-odd tests -- screenshots, accessibility, the lightbox -- had never once
    looked at a byte that shipped. Now there is one command, and the deploy drives the browser
    suite over its own artifact before uploading it.
    """

    # Plain text, not YAML: PyYAML is not a dependency of this suite and should not become one
    # to answer "which line comes first". A step's `run:` content is what is matched.
    @staticmethod
    def _lines(name):
        return [l for l in (WORKFLOWS / name).read_text(encoding="utf-8").splitlines()
                if not l.lstrip().startswith("#")]

    def test_no_workflow_invokes_hugo_directly(self):
        offenders = []
        for wf in sorted(WORKFLOWS.glob("*.yml")):
            for n, line in enumerate(self._lines(wf.name), 1):
                if re.match(r"^\s*(run:\s*)?hugo(\s|\\|$)", line):
                    offenders.append(f"{wf.name}: {line.strip()}")
        assert offenders == [], (
            "build through `make build`, not a second hugo command line: " + ", ".join(offenders)
        )

    def test_deploy_builds_with_make(self):
        assert any(re.search(r"run:\s*make build\b", l) for l in self._lines("hugo.yml"))

    def test_deploy_runs_the_browser_suite_on_its_artifact_before_upload(self):
        lines = self._lines("hugo.yml")
        at = lambda pat: next((i for i, l in enumerate(lines) if re.search(pat, l)), None)
        build, browser, upload = at(r"make build\b"), at(r"make visual-built"), at(r"upload-pages-artifact")
        assert browser is not None, "the deploy never drives a browser over what it ships"
        assert build < browser < upload, "browser suite must run after the build and before upload"

    def test_visual_built_does_not_rebuild(self):
        """If it rebuilt, the deploy would test a fresh build instead of the artifact it uploads."""
        text = (ROOT / "Makefile").read_text(encoding="utf-8")
        m = re.search(r"^visual-built:(.*)$", text, re.MULTILINE)
        assert m, "Makefile has no visual-built target"
        assert "build" not in m.group(1).split("##")[0]
