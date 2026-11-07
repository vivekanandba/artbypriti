"""scripts/report-failure.sh: a red scheduled run must reach a person.

health.yml failed four Mondays running (2026-10-12..11-02) and GitHub mailed only
whoever last edited the cron. Ported from trailward #79's reporter; these cases
drive it with a fake `gh` that records every call and serves canned issue lists.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "report-failure.sh"


def run(tmp_path, result, issues, title="Weekly health check is failing"):
    calls = tmp_path / "calls.log"
    fake = tmp_path / "bin" / "gh"
    fake.parent.mkdir()
    (tmp_path / "issues.json").write_text(json.dumps(issues))
    # The fake answers `gh api ... issues` by running the SCRIPT'S OWN --jq filter
    # through real jq over the canned list, so removing a clause from the script's
    # filter (the bot check, the exact title) is visible here. An earlier fake that
    # filtered for itself let that mutation survive. Every other call is logged.
    fake.write_text(f"""#!/usr/bin/env bash
echo "$*" >> {calls}
if [ "$1" = api ]; then
  expr=""
  while [ $# -gt 0 ]; do
    if [ "$1" = --jq ]; then expr="$2"; shift; fi
    shift
  done
  jq -r "$expr" "{tmp_path / 'issues.json'}"
fi
""")
    fake.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(PATH=f"{fake.parent}:{env['PATH']}", GH_REPO="o/r", RUN_URL="https://run/1")
    done = subprocess.run(["bash", str(SCRIPT), title, result], env=env,
                          capture_output=True, text=True)
    return done, (calls.read_text().splitlines() if calls.exists() else [])


BOT = {"type": "Bot"}
PERSON = {"type": "User"}


def test_a_failure_with_no_open_issue_opens_one(tmp_path):
    done, calls = run(tmp_path, "failure", [])
    assert done.returncode == 0, done.stderr
    assert any(c.startswith("issue create") and "Weekly health check is failing" in c for c in calls)


def test_a_failure_with_the_bot_issue_open_comments_instead_of_duplicating(tmp_path):
    done, calls = run(tmp_path, "failure",
                      [{"number": 7, "title": "Weekly health check is failing", "user": BOT}])
    assert done.returncode == 0, done.stderr
    assert any(c.startswith("issue comment 7") for c in calls)
    assert not any(c.startswith("issue create") for c in calls)


def test_a_cancelled_run_is_reported_like_a_failure(tmp_path):
    done, calls = run(tmp_path, "cancelled", [])
    assert any(c.startswith("issue create") and "cancelled" in c for c in calls)


def test_a_success_closes_the_open_bot_issue(tmp_path):
    done, calls = run(tmp_path, "success",
                      [{"number": 7, "title": "Weekly health check is failing", "user": BOT}])
    assert any(c.startswith("issue close 7") for c in calls)


def test_a_persons_issue_with_the_same_title_is_never_touched(tmp_path):
    done, calls = run(tmp_path, "success",
                      [{"number": 9, "title": "Weekly health check is failing", "user": PERSON}])
    assert not any(c.startswith("issue ") for c in calls)


@pytest.mark.parametrize("result", ["skipped", "neutral"])
def test_a_non_verdict_changes_nothing(tmp_path, result):
    done, calls = run(tmp_path, result, [])
    assert done.returncode == 0
    assert not any(c.startswith("issue ") for c in calls)


def test_no_result_is_an_error_not_a_silent_pass(tmp_path):
    done, _ = run(tmp_path, "", [])
    assert done.returncode == 2


def test_a_bot_issue_with_a_different_title_is_not_this_jobs_issue(tmp_path):
    """The title is matched exactly: another job's open alert is not this one's."""
    done, calls = run(tmp_path, "failure",
                      [{"number": 4, "title": "Weekly link check is failing", "user": BOT}])
    assert not any(c.startswith("issue comment 4") for c in calls)
    assert any(c.startswith("issue create") for c in calls)
