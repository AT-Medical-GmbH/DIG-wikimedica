from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "editorial" / "wikimedica_editorial_agent.py"


def run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--state-dir", str(tmp_path / "state"), "--plan", str(REPO / "data/editorial/article-plan.json")],
        text=True, capture_output=True, check=False,
    )


def test_initialise_and_report(tmp_path: Path) -> None:
    result = run(tmp_path, "init")
    assert result.returncode == 0, result.stderr
    report = tmp_path / "report.md"
    result = run(tmp_path, "report", "--report", str(report))
    assert result.returncode == 0, result.stderr
    assert "WM-DIS-0012" in report.read_text(encoding="utf-8")


def test_no_executor_keeps_article_planned_without_claiming_research(tmp_path: Path) -> None:
    assert run(tmp_path, "init").returncode == 0
    result = run(tmp_path, "run")
    assert result.returncode == 0, result.stderr
    state = json.loads((tmp_path / "state" / "state.json").read_text(encoding="utf-8"))
    item = state["items"]["WM-DIS-0012"]
    assert item["status"] == "planned"
    assert item["error"] is None
    assert state["events"][-1]["kind"] == "waiting-for-executor"


def test_run_does_not_attempt_source_network_without_contact_address(tmp_path: Path) -> None:
    assert run(tmp_path, "init").returncode == 0
    result = run(tmp_path, "run")
    assert result.returncode == 0, result.stderr
    state = json.loads((tmp_path / "state" / "state.json").read_text(encoding="utf-8"))
    assert state["items"]["WM-DIS-0012"]["status"] == "planned"


def test_pause_retry_and_publication_evidence_gate(tmp_path: Path) -> None:
    assert run(tmp_path, "init").returncode == 0
    assert run(tmp_path, "pause").returncode == 0
    assert run(tmp_path, "run").returncode == 0
    assert run(tmp_path, "resume").returncode == 0
    assert run(tmp_path, "retry", "--article-id", "WM-DIS-0012").returncode == 0
    result = run(tmp_path, "verify-publication", "--article-id", "WM-DIS-0012")
    assert result.returncode == 2
    assert "keine verifizierte" in result.stderr.lower()
