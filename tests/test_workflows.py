"""Guards for the CI/CD definitions: production deploys must stay tag-only and never run from PRs."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
WORKFLOWS = sorted((REPO / ".github" / "workflows").glob("*.yml"))


def load(name: str) -> dict:
    data = yaml.safe_load((REPO / ".github" / "workflows" / name).read_text())
    data["on"] = data.pop(True, data.get("on"))   # YAML 1.1 parses the key `on` as True
    return data


def test_deploy_workflow_is_tag_only_and_never_runs_from_pull_requests():
    wf = load("deploy.yml")
    triggers = wf["on"]
    assert set(triggers) == {"push", "workflow_dispatch"}
    assert "branches" not in triggers["push"]
    assert all(re.fullmatch(r"v\[0-9\]\+\.\[0-9\]\+\.\[0-9\]\+", t) for t in triggers["push"]["tags"])
    job = wf["jobs"]["deploy"]
    assert job["environment"] == "production"
    assert wf["concurrency"]["cancel-in-progress"] is False


def test_deploy_workflow_checks_tag_on_main_and_uses_no_hardcoded_hosts():
    text = (REPO / ".github/workflows/deploy.yml").read_text()
    assert "merge-base --is-ancestor" in text
    assert "StrictHostKeyChecking=yes" in text
    assert "DEPLOY_ENV=production" in text
    for old in ("VPS_HOST", "VPS_USER", "/opt/wikimedica"):
        assert old not in text


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_no_workflow_interpolates_untrusted_input_into_shell(path):
    text = path.read_text()
    for risky in ("github.event.pull_request.title", "github.event.pull_request.body", "github.event.head_commit.message",
                  "github.head_ref", "github.event.issue.title", "github.event.comment.body"):
        for line in text.splitlines():
            if risky in line and "run:" in line:
                pytest.fail(f"{path.name}: {risky} used directly in a run step")


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_workflow_declares_minimal_permissions(path):
    wf = yaml.safe_load(path.read_text())
    top = "permissions" in wf
    jobs = all("permissions" in j for j in wf["jobs"].values())
    assert top or jobs, f"{path.name} must declare permissions (workflow or every job)"


def test_compose_images_are_pinned():
    for f in (REPO / "infra" / "docker").glob("docker-compose*.yml"):
        for line in f.read_text().splitlines():
            m = re.match(r"\s*image:\s*(\S+)", line)
            if m and "${" not in m.group(1):
                assert ":" in m.group(1) and not m.group(1).endswith(":latest"), f"{f.name}: unpinned image {m.group(1)}"
