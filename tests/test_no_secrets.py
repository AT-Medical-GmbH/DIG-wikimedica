"""The repository must not contain credentials: scan tracked-style files for typical secret shapes."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "AWS key id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "bot password": re.compile(r"WIKI_\w*BOT_PASSWORD\s*=\s*[0-9a-w]{32,}\b"),
}


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-co", "--exclude-standard"], capture_output=True, text=True)
    files = [REPO / p for p in out.stdout.splitlines()] if out.returncode == 0 else [
        p for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts]
    return [p for p in files if p.is_file() and p.stat().st_size < 2_000_000 and p.name != "package-lock.json"]


def test_no_secret_shaped_strings():
    hits = []
    for path in tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, rx in PATTERNS.items():
            if rx.search(text):
                hits.append(f"{path.relative_to(REPO)}: {label}")
    assert not hits, "\n".join(hits)


def test_env_example_has_only_placeholders():
    text = (REPO / "infra" / "env" / ".env.example").read_text()
    for line in text.splitlines():
        m = re.match(r"([A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|KEY)[A-Z0-9_]*)=(.*)", line)
        if m and m.group(2).strip():
            assert "REPLACE_WITH" in m.group(2) or m.group(2).startswith(("${", "<")), f"{m.group(1)} has a real-looking value"


def test_real_env_files_are_gitignored():
    ignore = (REPO / ".gitignore").read_text()
    assert re.search(r"^\.env$|^infra/env/\.env$|^\*\*/\.env$", ignore, re.M)
