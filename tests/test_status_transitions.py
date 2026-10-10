"""Tests for scripts/validation/check-status-transitions.py."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from conftest import REPO, SCHEMA_PATH, load_script, read_fixture, render

cst = load_script("scripts/validation/check-status-transitions.py", "check_status_transitions")


@pytest.fixture(scope="module")
def lifecycle():
    import yaml
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))["lifecycle"]


# ---------------------------------------------------------------------------
# Pure rules
# ---------------------------------------------------------------------------

HANDOVER_ALLOWED = [
    ("draft", "in-review"),
    ("in-review", "approved"),
    ("approved", "published"),
    ("published", "archived"),
    ("published", "in-review"),
]


@pytest.mark.parametrize("old,new", HANDOVER_ALLOWED)
def test_handover_transitions_are_allowed(lifecycle, old, new):
    assert cst.check_transition(old, new, lifecycle) is None


@pytest.mark.parametrize("old,new", [
    ("draft", "approved"),
    ("draft", "published"),
    ("in-review", "published"),
    ("approved", "draft"),
    ("published", "draft"),
    ("published", "approved"),
    ("archived", "draft"),
    ("archived", "in-review"),
    ("retracted", "published"),
])
def test_forbidden_transitions_are_rejected(lifecycle, old, new):
    message = cst.check_transition(old, new, lifecycle)
    assert message and "not allowed" in message


def test_unchanged_status_is_not_a_transition(lifecycle):
    assert cst.check_transition("published", "published", lifecycle) is None


def test_unknown_status_is_rejected(lifecycle):
    assert "unknown status" in cst.check_transition("draft", "live", lifecycle)


def test_revision_loops_are_allowed(lifecycle):
    assert cst.check_transition("in-review", "draft", lifecycle) is None
    assert cst.check_transition("advisor-review", "in-review", lifecycle) is None


@pytest.mark.parametrize("status,ok", [("draft", True), ("in-review", True),
                                       ("approved", False), ("published", False)])
def test_new_articles_must_start_early(lifecycle, status, ok):
    assert (cst.check_new_article(status, lifecycle) is None) is ok


# ---------------------------------------------------------------------------
# Real git repository
# ---------------------------------------------------------------------------

def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True).stdout


def write(repo: Path, name: str, **changes) -> Path:
    fm, body = read_fixture("testartikel-patient.md")
    fm["slug"] = name
    fm.update(changes)
    path = repo / "content" / "patient-info" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(fm, body), encoding="utf-8")
    return path


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.org")
    git(tmp_path, "config", "user.name", "Test")
    write(tmp_path, "publiziert", status="published")
    write(tmp_path, "entwurf", status="draft")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def run(repo: Path, capsys) -> tuple[int, str]:
    code = cst.main(["--base-ref", "main", "--repo", str(repo), "--schema", str(SCHEMA_PATH)])
    return code, capsys.readouterr().out


def test_no_changes_is_clean(repo, capsys):
    code, out = run(repo, capsys)
    assert code == 0 and "Violations:        0" in out


def test_new_draft_is_allowed(repo, capsys):
    write(repo, "neu", status="draft")
    assert run(repo, capsys)[0] == 0


def test_new_article_as_published_is_blocked(repo, capsys):
    write(repo, "neu", status="published")
    code, out = run(repo, capsys)
    assert code == 1 and "new articles must start" in out


def test_draft_to_published_is_blocked(repo, capsys):
    write(repo, "entwurf", status="published")
    code, out = run(repo, capsys)
    assert code == 1 and "'draft' -> 'published'" in out


def test_draft_to_in_review_is_allowed(repo, capsys):
    write(repo, "entwurf", status="in-review")
    assert run(repo, capsys)[0] == 0


def test_published_to_in_review_is_allowed(repo, capsys):
    write(repo, "publiziert", status="in-review", version="1.1.0")
    assert run(repo, capsys)[0] == 0


def test_published_content_is_frozen(repo, capsys):
    path = repo / "content" / "patient-info" / "publiziert.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nSchleichende Änderung.\n", encoding="utf-8")
    code, out = run(repo, capsys)
    assert code == 1 and "frozen" in out


def test_published_frontmatter_is_frozen(repo, capsys):
    write(repo, "publiziert", status="published", change_summary="Heimlich geändert.")
    code, out = run(repo, capsys)
    assert code == 1 and "frozen" in out


def test_safety_hold_can_be_set_on_published_article(repo, capsys):
    """Emergency brake of the peer-review policy: must never be blocked by the freeze."""
    write(repo, "publiziert", status="published", safety_hold=True)
    code, out = run(repo, capsys)
    assert code == 0, out


def test_safety_hold_plus_other_change_is_still_frozen(repo, capsys):
    write(repo, "publiziert", status="published", safety_hold=True, change_summary="Heimlich")
    code, out = run(repo, capsys)
    assert code == 1 and "frozen" in out


def test_moving_published_article_to_another_directory_keeps_slug(repo, capsys):
    (repo / "content" / "archiv").mkdir(parents=True)
    git(repo, "mv", "content/patient-info/publiziert.md", "content/archiv/publiziert.md")
    assert run(repo, capsys)[0] == 0


def test_published_to_retracted_is_allowed_with_notice(repo, capsys):
    write(repo, "publiziert", status="retracted", retraction_notice="Zurückgezogen wegen Fehler.")
    assert run(repo, capsys)[0] == 0


def test_deleting_published_article_is_blocked(repo, capsys):
    (repo / "content" / "patient-info" / "publiziert.md").unlink()
    code, out = run(repo, capsys)
    assert code == 1 and "archive" in out


def test_deleting_draft_is_allowed(repo, capsys):
    (repo / "content" / "patient-info" / "entwurf.md").unlink()
    assert run(repo, capsys)[0] == 0


def test_renaming_published_article_is_blocked(repo, capsys):
    git(repo, "mv", "content/patient-info/publiziert.md", "content/patient-info/umbenannt.md")
    code, out = run(repo, capsys)
    assert code == 1 and "immutable" in out


def test_templates_and_non_articles_are_ignored(repo, capsys):
    (repo / "content" / "templates").mkdir(parents=True)
    (repo / "content" / "templates" / "x.md").write_text("---\nstatus: published\n---\n", encoding="utf-8")
    (repo / "content" / "README.md").write_text("# Kein Artikel\n", encoding="utf-8")
    assert run(repo, capsys)[0] == 0


def test_bad_base_ref_is_a_script_error(repo, capsys):
    code = cst.main(["--base-ref", "gibt-es-nicht", "--repo", str(repo), "--schema", str(SCHEMA_PATH)])
    assert code == 2
