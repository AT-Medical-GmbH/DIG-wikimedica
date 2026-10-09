"""LocalSettings.example.php: syntax, permission model and removal of obsolete settings."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from conftest import REPO

LOCALSETTINGS = REPO / "infra" / "mediawiki" / "LocalSettings.example.php"
HARNESS = REPO / "tests" / "php" / "localsettings-harness.php"

pytestmark = pytest.mark.skipif(shutil.which("php") is None, reason="php not installed")


def test_php_syntax():
    result = subprocess.run(["php", "-l", str(LOCALSETTINGS)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_permission_model_and_settings():
    result = subprocess.run(["php", str(HARNESS), str(LOCALSETTINGS)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 failed" in result.stdout


@pytest.mark.parametrize("obsolete", [
    "$wgUseSquid", "$wgSquidServers", "$wgRevisionStoreType", "localhost:8142",
])
def test_obsolete_settings_are_not_active(obsolete):
    """Mentions in comments are fine; an active assignment is not."""
    for line in LOCALSETTINGS.read_text(encoding="utf-8").splitlines():
        code = line.split("#", 1)[0].split("//", 1)[0]
        assert obsolete not in code, f"active use of obsolete setting: {line.strip()}"
